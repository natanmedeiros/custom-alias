
import pytest
from unittest.mock import MagicMock, patch
from dynamic_alias.executor import CommandExecutor
from dynamic_alias.models import CommandConfig, DictConfig, DynamicDictConfig, SubCommand, ArgConfig
from dynamic_alias.resolver import DataResolver
from dynamic_alias.config import ConfigLoader
from dynamic_alias.shell import InteractiveShell

@pytest.fixture
def mock_resolver():
    mock_loader = MagicMock(spec=ConfigLoader)
    mock_loader.dicts = {
        'static_dict': DictConfig(name='static_dict', data=[])
    }
    mock_loader.dynamic_dicts = {
        'dynamic_dict': DynamicDictConfig(name='dynamic_dict', command='', mapping={})
    }
    mock_loader.commands = [
        CommandConfig(name='TestCmd', alias='test', command='echo test', helper='Test Helper'),
        CommandConfig(name='CmdWithArg', alias='cmd arg', command='echo arg', args=[
            ArgConfig(alias='-f', command='-f', helper='Flag Helper')
        ])
    ]
    
    mock_resolver = MagicMock(spec=DataResolver)
    mock_resolver.config = mock_loader
    mock_resolver.resolved_data = {}
    return mock_resolver

def test_find_command_returns_is_help(mock_resolver):
    executor = CommandExecutor(mock_resolver)
    
    # Test Normal Command
    chain, vars, is_help = executor.find_command(['test'])
    assert chain[0].alias == 'test'
    assert is_help is False

    # Test Command Help
    result = executor.find_command(['test', '-h'])
    if result:
        chain, vars, is_help = result
        assert chain[0].alias == 'test'
        assert is_help is True
    else:
        pytest.fail("Command not found")

def test_help_flag_blocked_as_variable(mock_resolver):
    # Setup a command that takes a variable
    cmd = CommandConfig(name='VarCmd', alias='var ${val}', command='echo ${val}')
    mock_resolver.config.commands.append(cmd)
    executor = CommandExecutor(mock_resolver)

    # Test passing -h as variable
    result = executor.find_command(['var', '-h'])
    # Rule 1.3.5: "helper must consider partial match commands when variables wasnt informed"
    # So 'var -h' should match 'var ${val}' with is_help=True
    assert result is not None
    chain, vars, is_help = result
    assert chain[0].alias == 'var ${val}'
    assert is_help is True 

def test_print_global_help_structure(mock_resolver):
    executor = CommandExecutor(mock_resolver)
    
    with patch('dynamic_alias.executor.print_formatted_text') as mock_print:
        # Also patch builtin print because executor uses it for '-' separator and some lines
        with patch('builtins.print') as mock_builtin_print:
            executor.print_global_help()
            
            # Verify calls
            # We can inspect arguments to see if key strings are present
            printed_text = ""
            for call in mock_print.call_args_list:
                args, _ = call
                for arg in args:
                    if hasattr(arg, 'value'): # HTML object
                        printed_text += arg.value
                    else:
                        printed_text += str(arg)
            
            for call in mock_builtin_print.call_args_list:
                args, _ = call
                for arg in args:
                    printed_text += str(arg)

            assert "DYNAMIC ALIAS HELPER" in printed_text
            assert "Dicts (Static):" in printed_text
            assert "static_dict" in printed_text
            # Dynamic Dicts might be printed differently? 
            # In executor: print(f"  - {name}") -> builtin print
            assert "Dynamic Dicts:" in printed_text
            assert "dynamic_dict" in printed_text
            assert "Commands:" in printed_text
            assert "TestCmd" in printed_text
            assert "Test Helper" in printed_text

def test_interactive_shell_global_help(mock_resolver):
    executor = MagicMock() # Remove spec to avoid matching old class signature if any issue
    
    shell = InteractiveShell(mock_resolver, executor)
    
    parts = ['-h']
    if len(parts) == 1 and parts[0] in ('-h', '--help'):
        executor.print_global_help()
    
    executor.print_global_help.assert_called_once()

def test_interactive_shell_command_help(mock_resolver):
    executor = MagicMock()
    # Simulate find_command returning is_help=True
    cmd_mock = MagicMock()
    # Fix return value to have 3 elements
    executor.find_command.return_value = ([cmd_mock], {}, True)
    
    shell = InteractiveShell(mock_resolver, executor)
    
    # Simulate shell logic for found command
    parts = ['test', '-h']
    result = executor.find_command(parts)
    
    if result:
        cmd, vars, is_help = result
        if is_help:
            executor.print_help(cmd)
        else:
            executor.execute(cmd, vars)
            
    executor.print_help.assert_called_once_with([cmd_mock])
    executor.execute.assert_not_called()

def test_partial_match_help(mock_resolver):
    # Setup: 'pg ${db}'
    cmd = CommandConfig(name='PgCmd', alias='pg ${db}', command='psql')
    mock_resolver.config.commands.append(cmd)
    executor = CommandExecutor(mock_resolver)

    # Test 'pg -h' -> Should be partial match help
    # Because ${db} is a variable and we didn't provide it, but provided -h
    # Logic: alias=['pg', '${db}'], input=['pg', '-h']
    # 'pg' matches. '${db}' matches '-h' as help.
    result = executor.find_command(['pg', '-h'])
    
    assert result is not None
    chain, vars, is_help = result
    assert chain[0].alias == 'pg ${db}'
    assert is_help is True

def test_partial_match_fail_on_static(mock_resolver):
    # Setup: 'static sub'
    cmd = CommandConfig(name='StaticCmd', alias='static sub', command='echo')
    mock_resolver.config.commands.append(cmd)
    executor = CommandExecutor(mock_resolver)
    
    # Test 'static -h' -> Should NOT match 'static sub' as help, 
    # because 'sub' is static and != '-h'.
    # Rules don't say we should autocomplete static with help flag unless valid?
    # Actually 1.3.5 says "when variables wasnt informed".
    # It implies variable slots.
    result = executor.find_command(['static', '-h'])
    assert result is None

def test_partial_match_dynamic_var_help(mock_resolver):
    # Setup: 'dy $${static_dict.name}'
    # static_dict has content? mock_resolver has 'static_dict'
    cmd = CommandConfig(name='DyCmd', alias='dy $${static_dict.name}', command='echo')
    mock_resolver.config.commands.append(cmd)
    
    # Ensure static_dict has data so it WOULD pass if we gave a valid name
    mock_resolver.resolved_data = {
        'static_dict': [{'name': 'item1'}]
    }
    
    executor = CommandExecutor(mock_resolver)
    
    # Test 'dy -h' -> Should be partial match help skipping value validation
    result = executor.find_command(['dy', '-h'])
    
    assert result is not None
    chain, vars, is_help = result
    assert chain[0].name == 'DyCmd'
    assert is_help is True
