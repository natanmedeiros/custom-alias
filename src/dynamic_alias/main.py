import sys
import os
from typing import List

# Add parent directory to path to allow running as script if needed, 
# though checking __package__ is better for installed packages.
# For local dev without install:
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .config import ConfigLoader
from .cache import CacheManager
from .resolver import DataResolver
from .executor import CommandExecutor
from .shell import InteractiveShell
from .validator import ConfigValidator, print_validation_report, validate_config_silent
from .constants import CUSTOM_SHORTCUT, CUSTOM_NAME

# Constants
CACHE_ENABLED = True

def _resolve_path(options: List[str], default: str) -> str:
    return next((p for p in map(os.path.expanduser, options) if os.path.exists(p)), os.path.expanduser(default))

def main():
    # 1. Parse app-level flags
    args = sys.argv[1:]
    
    config_flag = f"--{CUSTOM_SHORTCUT}-config"
    cache_flag = f"--{CUSTOM_SHORTCUT}-cache"
    validate_flag = f"--{CUSTOM_SHORTCUT}-validate"
    clear_cache_flag = f"--{CUSTOM_SHORTCUT}-clear-cache"
    clear_history_flag = f"--{CUSTOM_SHORTCUT}-clear-history"
    clear_all_flag = f"--{CUSTOM_SHORTCUT}-clear-all"
    
    config_file_override = None
    cache_file_override = None
    run_validation = False
    run_clear_cache = False
    run_clear_history = False
    run_clear_all = False
    
    filtered_args = []
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == config_flag:
            if i + 1 < len(args):
                config_file_override = args[i+1]
                i += 2
                continue
            else:
                print(f"Error: {config_flag} requires an argument")
                sys.exit(1)
        elif arg == cache_flag:
            if i + 1 < len(args):
                cache_file_override = args[i+1]
                i += 2
                continue
            else:
                print(f"Error: {cache_flag} requires an argument")
                sys.exit(1)
        elif arg == validate_flag:
            run_validation = True
            i += 1
            continue
        elif arg == clear_cache_flag:
            run_clear_cache = True
            i += 1
            continue
        elif arg == clear_history_flag:
            run_clear_history = True
            i += 1
            continue
        elif arg == clear_all_flag:
            run_clear_all = True
            i += 1
            continue
        else:
            filtered_args.append(arg)
            i += 1
            
    # 2. Resolve Paths
    if config_file_override:
        final_config_path = os.path.expanduser(config_file_override)
    else:
        path_options_yaml = [f".{CUSTOM_SHORTCUT}.yaml", f"{CUSTOM_SHORTCUT}.yaml", f"~/.{CUSTOM_SHORTCUT}.yaml", f"~/{CUSTOM_SHORTCUT}.yaml"]
        default_yaml = f"~/.{CUSTOM_SHORTCUT}.yaml"
        final_config_path = _resolve_path(path_options_yaml, default_yaml)

    if cache_file_override:
        final_cache_path = os.path.expanduser(cache_file_override)
    else:
        path_options_json = [f".{CUSTOM_SHORTCUT}.json", f"{CUSTOM_SHORTCUT}.json", f"~/.{CUSTOM_SHORTCUT}.json", f"~/{CUSTOM_SHORTCUT}.json"]
        default_json = f"~/.{CUSTOM_SHORTCUT}.json"
        final_cache_path = _resolve_path(path_options_json, default_json)


    # Check for App Help
    dya_help_flag = f"--{CUSTOM_SHORTCUT}-help"
    
    def print_dya_help():
        print(f"\n{CUSTOM_NAME} Application Help")
        print("-" * 30)
        print("Usage Rules:")
        print("  - Configuration is defined in YAML format.")
        print("  - Supports static dicts, dynamic dicts (via shell commands), and commands.")
        print("  - Commands can use variables from user input values ${var} or dicts/dynamic_dicts $${source.key} syntax.")
        print("\nConfiguration Example:")
        print("  ---")
        print("  type: command")
        print("  name: Hello World")
        print("  alias: hello")
        print("  command: echo 'Hello World'")
        print("\nReserved Arguments:")
        print(f"  -h, --help               : Display help for commands or global help")
        print(f"  {config_flag} <path>      : Specify custom configuration file")
        print(f"  {cache_flag} <path>       : Specify custom cache file")
        print(f"  {validate_flag}          : Validate configuration file")
        print(f"  {clear_cache_flag}     : Clear dynamic dict cache (keeps history)")
        print(f"  {clear_history_flag}   : Clear command history")
        print(f"  {clear_all_flag}       : Delete entire cache file")
        print(f"  {dya_help_flag}               : Display this command line builder help")
        print("\nDocumentation:")
        print("  https://github.com/natanmedeiros/dynamic-alias?tab=readme-ov-file#documentation")
        print()

    if dya_help_flag in filtered_args:
        print_dya_help()
        return
    
    # Handle --{shortcut}-validate (rules 1.1.14-1.1.17)
    if run_validation:
        validator = ConfigValidator(final_config_path)
        report = validator.validate()
        exit_code = print_validation_report(report, CUSTOM_SHORTCUT)
        sys.exit(exit_code)
    
    # Handle cache management flags (rules 1.2.21, 1.2.23, 1.2.24)
    if run_clear_cache or run_clear_history or run_clear_all:
        cache = CacheManager(final_cache_path, True)
        cache.load()
        
        if run_clear_all:
            # Rule 1.2.24: Delete entire cache file
            if cache.delete_all():
                print(f"Cache file deleted: {final_cache_path}")
            else:
                print(f"Cache file not found: {final_cache_path}")
            return
        
        if run_clear_cache:
            # Rule 1.2.21: Clear non-underscore entries
            count = cache.clear_cache()
            print(f"Cleared {count} cache entries (history preserved)")
        
        if run_clear_history:
            # Rule 1.2.23: Clear _history
            if cache.clear_history():
                print("Command history cleared")
            else:
                print("No history to clear")
        
        return



    # 3. Bundled Config Enforcement (SHA Check)
    # Rules 1.1.12, 1.1.13 + SHA Enforcement
    bundled_config_path = os.path.join(os.path.dirname(__file__), f"{CUSTOM_SHORTCUT}.yaml")
    user_home_config = os.path.expanduser(f"~/.{CUSTOM_SHORTCUT}.yaml")
    
    if os.path.exists(bundled_config_path):
        should_copy = False
        reason = ""
        
        if not os.path.exists(user_home_config):
            should_copy = True
            reason = "Missing user configuration"
        else:
            # Compare Checksums
            import hashlib
            
            def get_file_hash(filepath):
                hasher = hashlib.sha256()
                with open(filepath, 'rb') as f:
                    # Safety break logic for tests mocking open with infinite read
                    max_chunks = 100000 # ~800MB limit should be enough for config
                    chunks_read = 0
                    while chunk := f.read(8192):
                        hasher.update(chunk)
                        chunks_read += 1
                        if chunks_read > max_chunks:
                            raise RuntimeError(f"Config file too large or infinite read (chunks={chunks_read})")
                return hasher.hexdigest()
            
            try:
                bundled_hash = get_file_hash(bundled_config_path)
                user_hash = get_file_hash(user_home_config)
                
                if bundled_hash != user_hash:
                    should_copy = True
                    reason = "Configuration mismatch (SHA variation)"
            except Exception as hash_err:
                 print(f"Warning: Failed to verify configuration integrity: {hash_err}")

        if should_copy:
            try:
                import shutil
                shutil.copy(bundled_config_path, user_home_config)
                print(f"[{CUSTOM_NAME}] Updating default configuration from bundle: {reason}")
            except Exception as copy_err:
                print(f"Warning: Failed to update default configuration: {copy_err}")

    # 4. Load App
    loader = ConfigLoader(final_config_path)
    try:
        loader.load()
    except FileNotFoundError as e:
         # Rule 1.3.8: Handle missing config (Original Logic)
        # Check if help was requested
        is_help_request = (len(filtered_args) == 1 and filtered_args[0] in ('-h', '--help'))
        
        if is_help_request:
            print(f"Error: {e}")
            print("\n" + "="*30 + "\n")
            print_dya_help()
            return
        else:
            print(f"Error: {e}")
            sys.exit(1)
    
    verbose = loader.global_config.verbose
    
    if verbose:
        print(f"[VERBOSE] Loaded configuration from: {final_config_path}")
    
    # Silent validation at startup (only outputs if errors found)
    if not validate_config_silent(final_config_path, CUSTOM_SHORTCUT):
        sys.exit(1)
    
    cache = CacheManager(final_cache_path, CACHE_ENABLED)
    cache_existed = os.path.exists(final_cache_path)
    cache.load()
    
    if verbose:
        if cache_existed:
            print(f"[VERBOSE] Loaded cache from: {final_cache_path}")
        else:
            print(f"[VERBOSE] Created new cache file: {final_cache_path}")
        
        history = cache.get_history()
        if history:
            print(f"[VERBOSE] Loaded {len(history)} history entries")
    
    resolver = DataResolver(loader, cache)
    # Don't resolve_all() at startup - use lazy loading
    # resolve_all() is only called for non-interactive command execution
    
    executor = CommandExecutor(resolver)

    if filtered_args:
        # Global help check
        if len(filtered_args) == 1 and filtered_args[0] in ('-h', '--help'):
            executor.print_global_help()
            return

        # Non-interactive mode also uses lazy loading
        # resolve_one() is called during find_command and execute as needed
        
        result = executor.find_command(filtered_args)
        if result:
            cmd, vars, is_help, remaining = result
            if is_help:
                executor.print_help(cmd)
            else:
                executor.execute(cmd, vars, remaining)
            # Save cache after execution (captures any resolved dicts)
            cache.save()
        else:
            print("Error: Command not found.")
    else:
        # Interactive mode - lazy loading via resolve_one() in completer
        shell = InteractiveShell(resolver, executor)
        shell.run()

if __name__ == "__main__":
    main()
