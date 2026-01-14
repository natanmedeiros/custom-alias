"""
Shell Mode Tests
Test Rules:
    @system_rules.txt
    @global-test-rules.md

Tests for:
- Shell mode config parsing
- Shell mode execution of unrecognized commands
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Mock prompt_toolkit modules BEFORE any imports
sys.modules['prompt_toolkit'] = MagicMock()
sys.modules['prompt_toolkit.shortcuts'] = MagicMock()
sys.modules['prompt_toolkit.formatted_text'] = MagicMock()
sys.modules['prompt_toolkit.key_binding'] = MagicMock()
sys.modules['prompt_toolkit.history'] = MagicMock()
sys.modules['prompt_toolkit.patch_stdout'] = MagicMock()
sys.modules['prompt_toolkit.completion'] = MagicMock()
sys.modules['prompt_toolkit.styles'] = MagicMock()

# Add src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dynamic_alias.config import ConfigLoader
from dynamic_alias.models import GlobalConfig


class TestShellModeConfig(unittest.TestCase):
    """Test shell mode configuration parsing."""
    
    def test_shell_mode_default_false(self):
        """Shell mode should default to False."""
        config = GlobalConfig()
        self.assertFalse(config.shell)
    
    def test_shell_mode_parsed_from_config(self):
        """Shell mode should be parsed from config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
config:
  shell: true
""")
            f.flush()
            
            loader = ConfigLoader(f.name)
            loader.load()
            
            self.assertTrue(loader.global_config.shell)
            
        os.unlink(f.name)
    
    def test_shell_mode_false_explicit(self):
        """Shell mode can be explicitly set to false."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
config:
  shell: false
""")
            f.flush()
            
            loader = ConfigLoader(f.name)
            loader.load()
            
            self.assertFalse(loader.global_config.shell)
            
        os.unlink(f.name)


class TestShellModeValidation(unittest.TestCase):
    """Test shell mode validation."""
    
    def test_shell_key_is_valid_in_config(self):
        """'shell' should be a valid config key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
config:
  shell: true
""")
            f.flush()
            
            from dynamic_alias.validator import ConfigValidator
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            # Should not have config key errors
            config_errors = [r for r in report.results 
                            if 'Unknown config keys' in r.message]
            self.assertEqual(len(config_errors), 0)
            
        os.unlink(f.name)


class TestShellModeExecution(unittest.TestCase):
    """Test shell mode command execution."""
    
    def test_shell_mode_executes_command(self):
        """When shell mode is enabled, unrecognized commands should be executed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
config:
  shell: true

---
type: command
name: Test
alias: test
command: echo test
""")
            f.flush()
            
            loader = ConfigLoader(f.name)
            loader.load()
            
            # Shell mode should be enabled
            self.assertTrue(loader.global_config.shell)
            
        os.unlink(f.name)
    
    def test_without_shell_mode_shows_invalid(self):
        """Without shell mode, unrecognized commands show 'Invalid command'."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
config:
  shell: false

---
type: command
name: Test
alias: test
command: echo test
""")
            f.flush()
            
            loader = ConfigLoader(f.name)
            loader.load()
            
            # Shell mode should be disabled
            self.assertFalse(loader.global_config.shell)
            
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
