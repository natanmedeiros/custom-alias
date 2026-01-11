import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from .resolver import DataResolver
from .executor import CommandExecutor
from .completer import DynamicAliasCompleter
from .constants import CUSTOM_SHORTCUT

class InteractiveShell:
    def __init__(self, resolver: DataResolver, executor: CommandExecutor):
        self.resolver = resolver
        self.executor = executor

    def run(self):
        completer = DynamicAliasCompleter(self.resolver, self.executor)
        
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
                # If no menu, Tab triggers completion (standard behavior)
                # But rule says "tab and enter must have same behavior, complete word".
                # If no list is showing, Enter executes. But Tab should assume we want to complete?
                # "but if not showing any list, enter must execute command".
                # It doesn't say Tab executes. Tab usually just opens completion.
                # So we keep Tab as standard completion trigger if list not open?
                # Actually, standard 'tab' key binding in prompt_toolkit triggers completion if not active.
                # So forcing it to apply_completion might break opening the menu?
                # No, standard 'tab' usually cycles or completes common prefix.
                # If I hijack it, I must ensure it still opens menu if closed?
                # Wait. "When showing autocompletion list...".
                # The rule applies ONLY "When showing autocompletion list".
                # So inside `if b.complete_state`, Tab and Enter do same thing.
                # Outside? Enter executes. Tab? Probably opens list.
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
        
        session = PromptSession(
            completer=completer,
            style=style,
            complete_while_typing=True,
            key_bindings=bindings
        )

        while True:
            try:
                text = session.prompt(f'{CUSTOM_SHORTCUT} > ', placeholder=HTML('<style color="gray">(tab for menu)</style>'))
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
                    cmd, vars, is_help, remaining = result
                    if is_help:
                        self.executor.print_help(cmd)
                    else:
                        self.executor.execute(cmd, vars, remaining)
                
                elif len(parts) == 1 and parts[0] in ('-h', '--help'):
                    self.executor.print_global_help()
                    
                else:
                    print("Invalid command.")

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")
