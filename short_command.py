#!/usr/bin/env python3
"""
Short command application
Description:
    Short command is an application that allows users to create aliases with superpowers for commands.
Rules:
    @system_rules.txt
"""
import sys
import os
import json
import yaml
import subprocess
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import HTML

# Constants
CACHE_ENABLED = True
def _resolve_path(options: List[str], default: str) -> str:
    return next((p for p in map(os.path.expanduser, options) if os.path.exists(p)), os.path.expanduser(default))

CACHE_FILE = _resolve_path([".shoco.json", "shoco.json", "~/.shoco.json", "~/shoco.json"], "~/.shoco.json")
CONFIG_FILE = _resolve_path([".shoco.yaml", "shoco.yaml", "~/.shoco.yaml", "~/shoco.yaml"], "~/.shoco.yaml")
DEFAULT_TIMEOUT = 10

@dataclass
class DictConfig:
    name: str
    data: List[Dict[str, Any]]

@dataclass
class DynamicDictConfig:
    name: str
    command: str
    mapping: Dict[str, str]
    priority: int = 1
    timeout: int = DEFAULT_TIMEOUT

@dataclass
class ArgConfig:
    alias: str
    command: str
    helper: Optional[str] = None

@dataclass
class SubCommand:
    alias: str
    command: str
    helper: Optional[str] = None
    sub: List['SubCommand'] = field(default_factory=list)
    args: List[ArgConfig] = field(default_factory=list)

@dataclass
class CommandConfig:
    name: str
    alias: str
    command: str
    helper: Optional[str] = None
    sub: List[SubCommand] = field(default_factory=list)
    args: List[ArgConfig] = field(default_factory=list)
    timeout: int = DEFAULT_TIMEOUT

class CacheManager:
    def __init__(self, cache_file: str, enabled: bool):
        self.cache_file = cache_file
        self.enabled = enabled
        self.cache: Dict[str, List[Dict[str, Any]]] = {}

    def load(self):
        if not self.enabled:
            return
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}")

    def save(self):
        if not self.enabled:
            return
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")

    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        if not self.enabled:
            return None
        return self.cache.get(key)

    def set(self, key: str, value: List[Dict[str, Any]]):
        if self.enabled:
            self.cache[key] = value

class ConfigLoader:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.dicts: Dict[str, DictConfig] = {}
        self.dynamic_dicts: Dict[str, DynamicDictConfig] = {}
        self.commands: List[CommandConfig] = []

    def _substitute_env_vars(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        pattern = r'\$\$\{env\.(\w+)\}'
        def replace(match):
            var_name = match.group(1)
            return os.environ.get(var_name, '')
        return re.sub(pattern, replace, text)

    def _process_data_structure(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        processed = []
        for item in data:
            new_item = {}
            for k, v in item.items():
                if isinstance(v, str):
                    new_item[k] = self._substitute_env_vars(v)
                else:
                    new_item[k] = v
            processed.append(new_item)
        return processed

    def load(self):
        if not os.path.exists(self.config_file):
            print(f"Error: Config file not found at {self.config_file}")
            sys.exit(1)

        with open(self.config_file, 'r') as f:
            content = f.read()
            docs = [doc for doc in content.split('---') if doc.strip()]

        for doc_str in docs:
            try:
                doc = yaml.safe_load(doc_str)
                if not doc or 'type' not in doc:
                    continue

                if doc['type'] == 'dict':
                    name = doc['name']
                    data = self._process_data_structure(doc.get('data', []))
                    self.dicts[name] = DictConfig(name=name, data=data)

                elif doc['type'] == 'dynamic_dict':
                    self.dynamic_dicts[doc['name']] = DynamicDictConfig(
                        name=doc['name'],
                        command=doc['command'],
                        mapping=doc['mapping'],
                        priority=doc.get('priority', 1),
                        timeout=doc.get('timeout', DEFAULT_TIMEOUT)
                    )

                elif doc['type'] == 'command':
                    self.commands.append(self._parse_command(doc))

            except yaml.YAMLError as e:
                print(f"Error parsing YAML: {e}")

        self.dynamic_dicts = dict(sorted(self.dynamic_dicts.items(), key=lambda x: x[1].priority))

    def _parse_command(self, doc: Dict) -> CommandConfig:
        subs = []
        if 'sub' in doc:
            subs = [self._parse_subcommand(s) for s in doc['sub']]
        
        return CommandConfig(
            name=doc['name'],
            alias=doc['alias'],
            command=doc['command'],
            helper=doc.get('helper'),
            sub=subs,
            args=[self._parse_arg(a) for a in doc.get('args', [])],
            timeout=doc.get('timeout', DEFAULT_TIMEOUT)
        )

    def _parse_subcommand(self, doc: Dict) -> SubCommand:
        subs = []
        if 'sub' in doc:
            subs = [self._parse_subcommand(s) for s in doc['sub']]
        
        return SubCommand(
            alias=doc['alias'],
            command=doc['command'],
            helper=doc.get('helper'),
            sub=subs,
            args=[self._parse_arg(a) for a in doc.get('args', [])]
        )
    
    def _parse_arg(self, doc: Dict) -> ArgConfig:
        return ArgConfig(
            alias=doc['alias'],
            command=doc['command'],
            helper=doc.get('helper')
        )

class DataResolver:
    def __init__(self, config: ConfigLoader, cache: CacheManager):
        self.config = config
        self.cache = cache
        self.resolved_data: Dict[str, List[Dict[str, Any]]] = {}

    def resolve_all(self):
        for name, d in self.config.dicts.items():
            self.resolved_data[name] = d.data
        
        for name, dd in self.config.dynamic_dicts.items():
            data = self.cache.get(name)
            if data is None:
                data = self._execute_dynamic_source(dd)
                self.cache.set(name, data)
            self.resolved_data[name] = data

    def _execute_dynamic_source(self, dd: DynamicDictConfig) -> List[Dict[str, Any]]:
        try:
            cmd = dd.command
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=dd.timeout)
            if result.returncode != 0:
                print(f"Error executing dynamic dict '{dd.name}': {result.stderr}")
                return []

            raw_json = json.loads(result.stdout)
            mapped_data = []
            target_list = raw_json
            if isinstance(raw_json, dict):
                 pass # Heuristic handling
            
            if not isinstance(target_list, list):
                target_list = [target_list]

            for item in target_list:
                new_item = {}
                for internal_key, json_key in dd.mapping.items():
                    if json_key in item:
                        new_item[internal_key] = item[json_key]
                if new_item:
                    mapped_data.append(new_item)
            return mapped_data

        except Exception as e:
            print(f"Error in dynamic dict '{dd.name}': {e}")
            return []

class CommandExecutor:
    def __init__(self, data_resolver: DataResolver):
        self.resolver = data_resolver

    def _match_alias_parts(self, alias_parts: List[str], input_parts: List[str]) -> tuple[bool, Dict[str, Any]]:
        if len(input_parts) < len(alias_parts):
            return False, {}

        variables = {}
        for alias_token, user_token in zip(alias_parts, input_parts):
            # 1. Check for app variable: $${source.key}
            app_var_match = re.match(r'\$\$\{(\w+)\.(\w+)\}', alias_token)
            if app_var_match:
                source_name = app_var_match.group(1) 
                key_name = app_var_match.group(2)    
                
                data_list = self.resolver.resolved_data.get(source_name)
                if not data_list:
                    return False, {}
                
                found_item = None
                for item in data_list:
                    if str(item.get(key_name)) == user_token:
                        found_item = item
                        break
                
                if found_item:
                    variables[source_name] = found_item
                else:
                    return False, {} 
                continue

            # 2. Check for user variable: ${var}
            user_var_match = re.match(r'\$\{(\w+)\}', alias_token)
            if user_var_match:
                var_name = user_var_match.group(1)
                variables[var_name] = user_token
                continue

            # 3. Static match
            if alias_token != user_token:
                return False, {}
        
        return True, variables

    def find_command(self, args: List[str]) -> Optional[tuple[List[Union[CommandConfig, SubCommand, ArgConfig]], Dict[str, Any]]]:
        for cmd in self.resolver.config.commands:
            chain, variables = self._try_match(cmd, args)
            if chain:
                return chain, variables
        return None

    def _try_match(self, command_obj: Union[CommandConfig, SubCommand], args: List[str]) -> tuple[List[Union[CommandConfig, SubCommand, ArgConfig]], Dict]:
        alias_parts = command_obj.alias.split()
        
        # 1. Match Command Alias
        matched, variables = self._match_alias_parts(alias_parts, args[:len(alias_parts)])
        if not matched:
            return [], {}
        
        remaining_args = args[len(alias_parts):]
        current_chain = [command_obj]

        # 2. Match Command Args (Greedy)
        while remaining_args and hasattr(command_obj, 'args') and command_obj.args:
            found_arg = False
            for arg_obj in command_obj.args:
                arg_alias_parts = arg_obj.alias.split()
                matched_arg, arg_vars = self._match_alias_parts(arg_alias_parts, remaining_args[:len(arg_alias_parts)])
                
                if matched_arg:
                    variables.update(arg_vars)
                    current_chain.append(arg_obj)
                    remaining_args = remaining_args[len(arg_alias_parts):]
                    found_arg = True
                    break 
            
            if not found_arg:
                break

        # 3. Match Sub-commands
        if hasattr(command_obj, 'sub') and command_obj.sub and remaining_args:
            for sub in command_obj.sub:
                sub_chain, sub_vars = self._try_match(sub, remaining_args)
                if sub_chain:
                    variables.update(sub_vars)
                    return current_chain + sub_chain, variables
        
        if not remaining_args:
             return current_chain, variables
             
        return [], {}

    def execute(self, command_chain: List[Union[CommandConfig, SubCommand, ArgConfig]], variables: Dict[str, Any]):
        full_template = " ".join([obj.command for obj in command_chain])
        
        def app_var_replace(match):
            source = match.group(1)
            key = match.group(2)
            if source in variables and isinstance(variables[source], dict):
                return str(variables[source].get(key, match.group(0)))
            return match.group(0)

        cmd_resolved = re.sub(r'\$\$\{(\w+)\.(\w+)\}', app_var_replace, full_template)
        
        def user_var_replace(match):
            key = match.group(1)
            if key in variables and isinstance(variables[key], str):
                return variables[key]
            return match.group(0)

        cmd_resolved = re.sub(r'\$\{(\w+)\}', user_var_replace, cmd_resolved)
        
        print_formatted_text(HTML(f"<b><green>Running:</green></b> {cmd_resolved}"))
        print("-" * 30)
        
        try:
            timeout = DEFAULT_TIMEOUT
            if command_chain and hasattr(command_chain[0], 'timeout'):
                timeout = command_chain[0].timeout
                
            subprocess.run(cmd_resolved, shell=True, timeout=timeout)

        except KeyboardInterrupt:
            print("\nOperation cancelled.")
        except subprocess.TimeoutExpired:
            print(f"\nError: Command timed out after {timeout}s")
        except Exception as e:
            print(f"Execution error: {e}")

class ShocoCompleter(Completer):
    def __init__(self, resolver: DataResolver, executor: CommandExecutor):
        self.resolver = resolver
        self.executor = executor

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        try:
            import shlex
            parts = shlex.split(text)
        except:
            return

        if not parts:
            parts = ['']
        
        elif text.endswith(' '):
            parts.append('')
        
        # Parse context
        # We need to traverse the command tree consistent with the input
        
        scope = self.resolver.config.commands
        used_args_in_scope = set() # Aliases of used args
        
        # Cursor tracking
        part_idx = 0
        
        matched_cmd_node = None # The last command/subcommand matched
        pending_arg = None # If we are in the middle of an arg (alias match start but not full)
        
        # We process all parts EXCEPT the last one (which is the one being completed)
        # However, to track context, we try to match as much as possible.
        
        while part_idx < len(parts) - 1:
            token = parts[part_idx]
            match_found = False
            
            # 1. Try Commands/Subs in scope
            start_parts_slice = parts[part_idx:] 
            
            for cmd in scope:
                cmd_parts = cmd.alias.split()
                if part_idx + len(cmd_parts) <= len(parts) - 1:
                     is_match, _ = self.executor._match_alias_parts(cmd_parts, parts[part_idx:part_idx+len(cmd_parts)])
                     if is_match:
                         matched_cmd_node = cmd
                         part_idx += len(cmd_parts)
                         scope = cmd.sub if hasattr(cmd, 'sub') else []
                         used_args_in_scope = set() 
                         match_found = True
                         break
            
            if match_found:
                continue
                
            # 2. Try match ARGS in (matched_cmd_node) context
            if matched_cmd_node and hasattr(matched_cmd_node, 'args'):
                for arg in matched_cmd_node.args:
                    if arg.alias in used_args_in_scope:
                        continue
                    
                    arg_parts = arg.alias.split()
                    if part_idx + len(arg_parts) <= len(parts) - 1:
                        is_match, _ = self.executor._match_alias_parts(arg_parts, parts[part_idx:part_idx+len(arg_parts)])
                        if is_match:
                             used_args_in_scope.add(arg.alias)
                             part_idx += len(arg_parts)
                             match_found = True
                             break
            
            if match_found:
                continue

            break
            
        # End of consumption loop.
        # matched_cmd_node is the active command.
        # part_idx points to where we are completions.
        
        # Check if we are incomplete on a multi-token structure (Command or Arg)
        
        prefix = parts[-1]
        
        # If part_idx is NOT at len(parts)-1, it means we stopped consuming before the end.
        # This implies we are "inside" a multi-token structure or invalid input.
        
        if part_idx < len(parts) - 1:
            # We have some tokens that didn't fully match a structure.
            # e.g. `pg db1 -o` (and we are at `''`?)
            # No, if `pg db1 -o `, parts=`['-o', '']`. part_idx matches `-o`.
            # Wait, my loop condition `part_idx < len(parts) - 1`.
            # If `parts` = `['...','-o', '']`.
            # part_idx is at `-o`.
            # If `-o` is start of arg `-o ${file}`.
            
            # Check for Partial Matches starting at part_idx
            
            # 1. Partial Arg?
            if matched_cmd_node and hasattr(matched_cmd_node, 'args'):
                for arg in matched_cmd_node.args:
                    if arg.alias in used_args_in_scope:
                        continue
                    arg_parts = arg.alias.split()
                    # Check prefix match
                    # We have `parts[part_idx : -1]` (Completed tokens after match)
                    # And `parts[-1]` (Typing)
                    
                    # Consumed so far: `parts[part_idx:len(parts)-1]`
                    consumed_chunk = parts[part_idx:len(parts)-1]
                    
                    # Does this chunk match the start of arg_parts?
                    if len(consumed_chunk) < len(arg_parts):
                        # Potential match
                        is_match, _ = self.executor._match_alias_parts(arg_parts[:len(consumed_chunk)], consumed_chunk)
                        if is_match:
                            # We are inside this arg.
                            # What is the expected next token?
                            next_token_idx = len(consumed_chunk)
                            expected_token_alias = arg_parts[next_token_idx]
                            
                            # Suggestions
                            # If expected token is variable `${...}`, Do NOT yield (Rule 4.18)
                            # If expected token is static, yield it if matches prefix
                            if expected_token_alias.startswith('$${'):
                                yield Completion(expected_token_alias, start_position=-len(prefix), display=expected_token_alias)
                            elif expected_token_alias.startswith('${'):
                                # User rule: Args can autocomplete only flags, not user variables
                                pass 
                            else:
                                if expected_token_alias.startswith(prefix):
                                    yield Completion(expected_token_alias, start_position=-len(prefix))
                            
                            # If we matched a partial arg, we return (exclusive?)
                            return

            # 2. Partial Command?
            for cmd in scope:
                cmd_parts = cmd.alias.split()
                # Check prefix match
                # Consumed so far: parts[part_idx:len(parts)-1]
                consumed_chunk = parts[part_idx:len(parts)-1]
                
                if not consumed_chunk:
                    continue
                    
                if len(consumed_chunk) < len(cmd_parts):
                    # Check if consumed chunk matches start of alias
                    is_match, _ = self.executor._match_alias_parts(cmd_parts[:len(consumed_chunk)], consumed_chunk)
                    if is_match:
                        # We are inside this command alias
                        next_token_idx = len(consumed_chunk)
                        expected_token_alias = cmd_parts[next_token_idx]
                        
                        # Suggestion logic
                        # Dynamic Var $${...}
                        app_var_match = re.match(r'\$\$\{(\w+)\.(\w+)\}', expected_token_alias)
                        if app_var_match:
                            source, key = app_var_match.group(1), app_var_match.group(2)
                            if source in self.resolver.resolved_data:
                                for item in self.resolver.resolved_data[source]:
                                    val = str(item.get(key, ''))
                                    if val.startswith(prefix):
                                        yield Completion(val, start_position=-len(prefix))
                        
                        # User Var ${...}
                        elif expected_token_alias.startswith('${'):
                             # Rule 4.20: Avoid user defined variables completion like ${sql_text}
                             pass
                             # yield Completion(expected_token_alias, start_position=-len(prefix), display=expected_token_alias)
                             
                        # Static Text
                        else:
                            if expected_token_alias.startswith(prefix):
                                yield Completion(expected_token_alias, start_position=-len(prefix))
                        
                        # If we found a partial command match, we should probably stop?
                        # Or continue to find distinct aliases? 
                        # Return to yield exclusive results for this alias path?
                        # Yes, finding specific command path.
                        # But wait, multiple commands might share prefix?
                        # e.g. `s3 sync` and `s3 ls`.
                        # If we typed `s3 `, we match both!
                        # We should yield from ALL matches, not return immediately.
                        # So don't return.
                        pass
        else:
            # part_idx == len(parts) - 1.
            
            # Suggestions:
            # 1. Subcommands of matched_cmd_node
            # 2. Unused Args of matched_cmd_node
            
            candidates = []
            
            if matched_cmd_node:
                # Subs
                if hasattr(matched_cmd_node, 'sub'):
                    candidates.extend(matched_cmd_node.sub)
                
                # Args (unused)
                if hasattr(matched_cmd_node, 'args'):
                    for arg in matched_cmd_node.args:
                        if arg.alias not in used_args_in_scope:
                            candidates.append(arg)
            else:
                # Root commands
                candidates.extend(self.resolver.config.commands)
            
            for cand in candidates:
                # First token of alias
                cand_parts = cand.alias.split()
                head = cand_parts[0]
                
                # Handling dynamic vars $${...}
                app_var_match = re.match(r'\$\$\{(\w+)\.(\w+)\}', head)
                if app_var_match:
                    source, key = app_var_match.group(1), app_var_match.group(2)
                    if source in self.resolver.resolved_data:
                        for item in self.resolver.resolved_data[source]:
                            val = str(item.get(key, ''))
                            if val.startswith(prefix):
                                yield Completion(val, start_position=-len(prefix))
                elif head.startswith('${'):
                     # User var placeholder as start of command? Rare but possible.
                     yield Completion(head, start_position=-len(prefix))
                else:
                    if head.startswith(prefix):
                        yield Completion(head, start_position=-len(prefix))


class InteractiveShell:
    def __init__(self, resolver: DataResolver, executor: CommandExecutor):
        self.resolver = resolver
        self.executor = executor

    def run(self):
        completer = ShocoCompleter(self.resolver, self.executor)
        
        style = Style.from_dict({
            'completion-menu.completion': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',
            'scrollbar.background': 'bg:#88aaaa',
            'scrollbar.button': 'bg:#222222',
        })

        bindings = KeyBindings()

        @bindings.add('enter')
        def _(event):
            b = event.current_buffer
            if b.complete_state:
                if b.complete_state.current_completion:
                    b.apply_completion(b.complete_state.current_completion)
                elif b.complete_state.completions:
                    b.apply_completion(b.complete_state.completions[0])
            else:
                b.validate_and_handle()
        
        session = PromptSession(
            completer=completer,
            style=style,
            complete_while_typing=True,
            key_bindings=bindings
        )

        while True:
            try:
                text = session.prompt('shoco > ', placeholder=HTML('<style color="gray">(tab for menu)</style>'))
                text = text.strip()
                if not text:
                    continue
                if text in ['exit', 'quit']:
                    break
                    
                import shlex
                try:
                    parts = shlex.split(text)
                except ValueError:
                    print("Error: Invalid quotes")
                    continue
                    
                result = self.executor.find_command(parts)
                
                if result:
                    cmd, vars = result
                    self.executor.execute(cmd, vars)
                    self.resolver.cache.save()
                else:
                    print("Invalid command.")

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    loader = ConfigLoader(CONFIG_FILE)
    loader.load()
    
    cache = CacheManager(CACHE_FILE, CACHE_ENABLED)
    cache.load()
    
    resolver = DataResolver(loader, cache)
    resolver.resolve_all()
    
    executor = CommandExecutor(resolver)

    if len(sys.argv) > 1:
        args = sys.argv[1:]
        result = executor.find_command(args)
        if result:
            cmd, vars = result
            executor.execute(cmd, vars)
            cache.save()
        else:
            print("Error: Command not found.")
    else:
        shell = InteractiveShell(resolver, executor)
        shell.run()

if __name__ == "__main__":
    main()
