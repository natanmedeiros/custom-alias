
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from importlib import import_module

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import the actual module using importlib (not the function shadowed by __init__.py)
main_module = import_module('dynamic_alias.main')
main = main_module.main
from dynamic_alias.constants import CUSTOM_SHORTCUT

def test_dya_help_flag(capsys):
    # Test --dya-help
    argv = ['script_name', f'--{CUSTOM_SHORTCUT}-help']
    
    with patch.object(main_module, 'InteractiveShell') as MockShell:
        MockShell.return_value.run.return_value = None
        with patch('sys.argv', argv):
            try:
                main()
            except SystemExit:
                pass
            
    captured = capsys.readouterr()
    output = captured.out
    
    assert "Application Help" in output
    assert "Usage Rules:" in output
    assert "Reserved Arguments:" in output
    assert f"--{CUSTOM_SHORTCUT}-help" in output
    assert "https://github.com/natanmedeiros/dynamic-alias" in output

def test_global_help_footer(capsys):
    # Test -h (with valid config)
    config_path = os.path.join(os.path.dirname(__file__), "dya.yaml")
    argv = ['script_name', '-h', f'--{CUSTOM_SHORTCUT}-config', config_path]
    
    with patch.object(main_module, 'InteractiveShell') as MockShell:
        MockShell.return_value.run.return_value = None
        with patch('sys.argv', argv):
            try:
                main()
            except SystemExit:
                pass
            
    captured = capsys.readouterr()
    output = captured.out
    
    assert "Command Line Interface powered by Dynamic Alias" in output
    assert f"To display {CUSTOM_SHORTCUT} helper use --{CUSTOM_SHORTCUT}-help" in output

def test_missing_config_with_help(capsys):
    # Test missing config AND -h
    # When --dya-config points to non-existent file, app should report error
    non_existent_config = "/path/to/non_existent_config.yaml"
    argv = ['script_name', '-h', f'--{CUSTOM_SHORTCUT}-config', non_existent_config]
    
    with patch.object(main_module, 'InteractiveShell') as MockShell:
        MockShell.return_value.run.return_value = None
        with patch('sys.argv', argv):
            try:
                main()
            except SystemExit:
                pass
            
    captured = capsys.readouterr()
    output = captured.out
    
    # Should show help since -h is present
    assert "Application Help" in output or "Dynamic Alias" in output

def test_missing_config_without_help(capsys):
    # Test missing config without -h
    # When --dya-config points to non-existent file, app should error or use fallback
    non_existent_config = "/path/to/non_existent_config.yaml"
    argv = ['script_name', f'--{CUSTOM_SHORTCUT}-config', non_existent_config]
    
    with patch.object(main_module, 'InteractiveShell') as MockShell:
        MockShell.return_value.run.return_value = None
        with patch('sys.argv', argv):
            try:
                main()
            except SystemExit as e:
                # If exits, should be with error code
                assert e.code == 1
            
    captured = capsys.readouterr()
    output = captured.out + captured.err
    
    # Should either report error or be empty (fallback worked silently)
    # App help should NOT be printed without -h flag
    assert "Application Help" not in output

