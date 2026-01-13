"""
Dict Access Mode Tests
Test Rules:
    @system_rules.txt
    @global-test-rules.md

Tests for:
- Issue 1: Dict/dynamic_dict key access modes
  - Direct mode: key only in command, not in alias (single-item dict)
  - List mode: key in alias, other keys resolve from same index
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
from dynamic_alias.cache import CacheManager
from dynamic_alias.resolver import DataResolver
from dynamic_alias.executor import CommandExecutor


class TestDictAccessModes(unittest.TestCase):
    """Test both dict access modes: direct and list."""
    
    @classmethod
    def setUpClass(cls):
        cls.config_file = os.path.join(os.path.dirname(__file__), "dya.yaml")
        assert os.path.exists(cls.config_file), f"Config file not found: {cls.config_file}"
        
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "dya.json")
        
        self.loader = ConfigLoader(self.config_file)
        self.loader.load()
        
        self.cache = CacheManager(self.cache_path, enabled=True)
        self.cache.load()
        
        self.resolver = DataResolver(self.loader, self.cache)
        self.executor = CommandExecutor(self.resolver)

    def tearDown(self):
        self.temp_dir.cleanup()

    # =========================================================================
    # Direct Access Mode Tests
    # =========================================================================
    
    def test_direct_access_single_item_dict_resolves(self):
        """Direct mode: Single-item dict should resolve keys when not in alias."""
        # Find the direct-access command
        result = self.executor.find_command(["direct-access"])
        self.assertIsNotNone(result, "Command 'direct-access' not found")
        
        chain, variables, is_help, remaining = result
        self.assertFalse(is_help)
        self.assertEqual(len(chain), 1)
        
        # The command template should be resolved
        # Variables should NOT contain single_config since it's not in alias
        self.assertNotIn('single_config', variables)
        
    def test_direct_access_resolves_all_keys(self):
        """Direct mode: All keys from single-item dict should resolve."""
        result = self.executor.find_command(["direct-access"])
        self.assertIsNotNone(result)
        
        chain, variables, is_help, remaining = result
        
        # Simulate command resolution (what execute() does)
        import re
        full_template = " ".join([obj.command for obj in chain])
        
        def app_var_replace(match):
            source = match.group(1)
            key = match.group(2)
            if source in variables and isinstance(variables[source], dict):
                return str(variables[source].get(key, match.group(0)))
            # Direct mode: always use first item (position 0)
            data_list = self.resolver.resolve_one(source)
            if data_list:
                return str(data_list[0].get(key, match.group(0)))
            return match.group(0)
        
        resolved = re.sub(r'\$\$\{(\w+)\.(\w+)\}', app_var_replace, full_template)
        
        # All placeholders should be resolved
        self.assertIn("key=api_key", resolved)
        self.assertIn("value=secret123", resolved)
        self.assertIn("endpoint=https://api.example.com", resolved)
        self.assertNotIn("$${", resolved)

    def test_direct_access_multi_item_dict_uses_first_item(self):
        """Direct mode: Multi-item dict should resolve using first item (position 0)."""
        # Create a command template with multi-item dict (static_envs has 2 items)
        import re
        template = "echo $${static_envs.url}"
        variables = {}  # Not selected via alias
        
        def app_var_replace(match):
            source = match.group(1)
            key = match.group(2)
            if source in variables and isinstance(variables[source], dict):
                return str(variables[source].get(key, match.group(0)))
            # Direct mode: always use first item (position 0)
            data_list = self.resolver.resolve_one(source)
            if data_list:
                return str(data_list[0].get(key, match.group(0)))
            return match.group(0)
        
        resolved = re.sub(r'\$\$\{(\w+)\.(\w+)\}', app_var_replace, template)
        
        # Should resolve to first item (dev.internal, which is position 0)
        self.assertEqual(resolved, "echo dev.internal")

    # =========================================================================
    # List Access Mode Tests
    # =========================================================================
    
    def test_list_access_resolves_matching_keys(self):
        """List mode: Keys in command should resolve from same index as alias."""
        # "list-access dev" should resolve url from dev's entry
        result = self.executor.find_command(["list-access", "dev"])
        self.assertIsNotNone(result, "Command 'list-access dev' not found")
        
        chain, variables, is_help, remaining = result
        self.assertFalse(is_help)
        
        # Variables should contain the matched dict item
        self.assertIn('static_envs', variables)
        self.assertEqual(variables['static_envs']['name'], 'dev')
        self.assertEqual(variables['static_envs']['url'], 'dev.internal')

    def test_list_access_resolves_correct_index(self):
        """List mode: Second item selection should resolve second item's keys."""
        result = self.executor.find_command(["list-access", "prod"])
        self.assertIsNotNone(result)
        
        chain, variables, is_help, remaining = result
        
        self.assertIn('static_envs', variables)
        self.assertEqual(variables['static_envs']['name'], 'prod')
        self.assertEqual(variables['static_envs']['url'], 'prod.internal')

    def test_list_access_invalid_value_no_match(self):
        """List mode: Non-existent value should not match."""
        result = self.executor.find_command(["list-access", "nonexistent"])
        # Should not match because "nonexistent" is not in static_envs.name
        self.assertIsNone(result)

    # =========================================================================
    # Dict Consumer Tests (existing pattern)
    # =========================================================================
    
    def test_dict_consumer_resolves_both_keys(self):
        """Existing 'consume' command should work with list mode."""
        result = self.executor.find_command(["consume", "dev"])
        self.assertIsNotNone(result)
        
        chain, variables, is_help, remaining = result
        
        self.assertIn('static_envs', variables)
        self.assertEqual(variables['static_envs']['name'], 'dev')
        self.assertEqual(variables['static_envs']['url'], 'dev.internal')

    def test_dynamic_dict_consumer_resolves(self):
        """Dynamic dict 'dyn' command should work with list mode."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = '[{"id": "node-1", "ip": "10.0.0.1"}, {"id": "node-2", "ip": "10.0.0.2"}]'
            mock_run.return_value.returncode = 0
            
            result = self.executor.find_command(["dyn", "node-1"])
            self.assertIsNotNone(result)
            
            chain, variables, is_help, remaining = result
            
            self.assertIn('dynamic_nodes', variables)
            self.assertEqual(variables['dynamic_nodes']['name'], 'node-1')
            self.assertEqual(variables['dynamic_nodes']['ip'], '10.0.0.1')


class TestTerminalReset(unittest.TestCase):
    """Test terminal reset functionality."""
    
    def test_shell_module_has_stty_sane_logic(self):
        """Shell run method should have stty sane for terminal reset."""
        import inspect
        from dynamic_alias import shell
        
        # Get source code of the shell module
        source = inspect.getsource(shell)
        
        # Check for stty sane in the source
        self.assertIn('stty sane', source)
        
    def test_shell_module_has_finally_block(self):
        """Shell run method should have finally block for cleanup."""
        import inspect
        from dynamic_alias import shell
        
        # Get source code of run method
        source = inspect.getsource(shell.InteractiveShell.run)
        
        # Check for finally block
        self.assertIn('finally:', source)
        
    def test_shell_module_imports_os_and_sys(self):
        """Shell module should have os and sys imports."""
        import inspect
        from dynamic_alias import shell
        
        # Get source of the module to check imports
        source_file = inspect.getsourcefile(shell)
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn('import sys', content)
        self.assertIn('import os', content)


if __name__ == '__main__':
    unittest.main()
