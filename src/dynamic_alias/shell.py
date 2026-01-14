import sys
import os
import signal
from prompt_toolkit import PromptSession
from prompt_toolkit.history import History
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from .resolver import DataResolver
from .executor import CommandExecutor
from .completer import DynamicAliasCompleter
from .constants import CUSTOM_SHORTCUT

class CacheHistory(History):
    def __init__(self, cache_manager, limit: int = 20):
        super().__init__()
        self.cache_manager = cache_manager
        self.limit = limit
        
    def load_history_strings(self):
        # Return history in chronological order (oldest to newest)
        return reversed(self.cache_manager.get_history())
        
    def store_string(self, string: str):
         # Rule 1.2.25/1.2.26: 
         # We typically verify/save here, but PromptSession runs this in a background thread.
         # This causes a race condition with subprocesses (like set-local) that modify the cache concurrently.
         # To fix this, we disable saving here and manually handle it in the main loop (synchronously).
         pass

class InteractiveShell:
    def __init__(self, resolver: DataResolver, executor: CommandExecutor):
        self.resolver = resolver
        self.executor = executor

    def run(self):
        # Register SIGTERM handler for graceful cleanup when killed
        def cleanup_and_exit(signum, frame):
            if sys.platform != 'win32':
                os.system('stty sane 2>/dev/null')
            sys.exit(0)
        
        if sys.platform != 'win32':
            signal.signal(signal.SIGTERM, cleanup_and_exit)
            signal.signal(signal.SIGHUP, cleanup_and_exit)  # Also handle terminal close
        
        completer = DynamicAliasCompleter(self.resolver, self.executor)
        
        # Rule 1.1.10: Use styles from config (with defaults in models.py)
        global_config = self.resolver.config.global_config
        style = Style.from_dict(global_config.styles)
        
        # Placeholder styling
        placeholder_color = global_config.placeholder_color
        placeholder_text_content = global_config.placeholder_text
        placeholder_html = HTML(f'<style color="{placeholder_color}">{placeholder_text_content}</style>')

        bindings = KeyBindings()

        @bindings.add('enter')
        def _(event):
            b = event.current_buffer
            if b.complete_state:
                # If menu is open, Enter selects the item (autocompletes)
                if b.complete_state.current_completion:
                    b.apply_completion(b.complete_state.current_completion)
                elif b.complete_state.completions:
                    b.apply_completion(b.complete_state.completions[0])
            else:
                # If no menu, Enter executes
                b.validate_and_handle()

        @bindings.add('tab')
        def _(event):
            b = event.current_buffer
            if b.complete_state:
                # If menu is open, Tab selects the item (autocompletes) - SAME as Enter behavior for list
                if b.complete_state.current_completion:
                     b.apply_completion(b.complete_state.current_completion)
                elif b.complete_state.completions:
                     b.apply_completion(b.complete_state.completions[0])
            else:
                pass 
                
            # If we don't handle it here (i.e. not in complete_state), we should let default handling happen?
            # But KeyBinding catches it. We must manually trigger completion if not open.
            if not b.complete_state:
                b.start_completion(select_first=True)

        @bindings.add('backspace')
        def _(event):
            b = event.current_buffer
            
            # 1. Perform standard backspace
            doc = b.document
            if doc.cursor_position > 0:
                 b.delete_before_cursor(1)
            else:
                 # Nothing to delete
                 return

            # 2. Rule 1.2.13 & 1.2.15: Evaluate autocompletion again
            # We explicitly trigger completion after deletion to ensure menu updates immediately
            # even if we deleted the entire word or are now at an empty string.
            b.start_completion(select_first=False) # select_first=False to just show menu without pre-selecting to avoid aggressive intrusion
        
        history_size = global_config.history_size
        history = CacheHistory(self.resolver.cache, history_size)
        
        session = PromptSession(
            completer=completer,
            style=style,
            history=history,
            complete_while_typing=True,
            key_bindings=bindings
        )

        try:
            while True:
                try:
                    text = session.prompt(f'{CUSTOM_SHORTCUT} > ', placeholder=placeholder_html)
                    text = text.strip()
                    if not text:
                        continue
                    
                    # Manual History Management (Sync Logic)
                    # 1. Reload cache to pick up any changes from previous commands/subprocesses
                    self.resolver.cache.load()
                    # 2. Add current command to history
                    self.resolver.cache.add_history(text, global_config.history_size)
                    # 3. Save updated state (merging external changes + new history)
                    self.resolver.cache.save()

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
                        cmd, vars, is_help, remaining = result
                        if is_help:
                            self.executor.print_help(cmd)
                        else:
                            self.executor.execute(cmd, vars, remaining)
                    
                    elif len(parts) == 1 and parts[0] in ('-h', '--help'):
                        self.executor.print_global_help()
                        
                    else:
                        # Shell mode: execute unrecognized commands directly in shell
                        if global_config.shell:
                            import subprocess
                            try:
                                if global_config.verbose:
                                    print(f"[VERBOSE] Shell mode: executing '{text}'")
                                subprocess.run(text, shell=True)
                            except Exception as shell_err:
                                print(f"Shell error: {shell_err}")
                        else:
                            print("Invalid command.")

                except KeyboardInterrupt:
                    continue
                except EOFError:
                    break
                except Exception as e:
                    print(f"Error: {e}")
        finally:
            # Reset terminal state on exit (fixes bash invisible input issue)
            # Issue: prompt_toolkit can leave terminal in raw/alternate state
            if sys.platform != 'win32':
                os.system('stty sane 2>/dev/null')
