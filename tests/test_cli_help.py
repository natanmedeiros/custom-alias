
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dynamic_alias.main import main
from dynamic_alias.constants import CUSTOM_SHORTCUT

def test_dya_help_flag(capsys):
    # Test --dya-help
    argv = ['script_name', f'--{CUSTOM_SHORTCUT}-help']
    
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
    non_existent_config = "non_existent_config.yaml"
    argv = ['script_name', '-h', f'--{CUSTOM_SHORTCUT}-config', non_existent_config]
    
    with patch('sys.argv', argv):
        try:
            main()
        except SystemExit:
            pass
            
    captured = capsys.readouterr()
    output = captured.out
    
    assert f"Config file not found at {non_existent_config}" in output
    assert "="*30 in output
    assert "Application Help" in output
    assert "Reserved Arguments:" in output

def test_missing_config_without_help(capsys):
    # Test missing config without -h
    non_existent_config = "non_existent_config.yaml"
    argv = ['script_name', f'--{CUSTOM_SHORTCUT}-config', non_existent_config]
    
    with patch('sys.argv', argv):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
            
    captured = capsys.readouterr()
    output = captured.out
    
    assert f"Config file not found at {non_existent_config}" in output
    assert "Application Help" not in output
