import os
import unittest
from unittest.mock import patch, MagicMock
from dynamic_alias.config import ConfigLoader
from dynamic_alias.cache import CacheManager
from dynamic_alias.resolver import DataResolver
from dynamic_alias.executor import CommandExecutor
import subprocess

# Paths for test resources
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(TEST_DIR, "dya.yaml")
CACHE_PATH = os.path.join(TEST_DIR, "dya.json")

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create empty cache if not exists
        if not os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, 'w') as f:
                f.write('{}')

    def setUp(self):
        self.loader = ConfigLoader(CONFIG_PATH)
        self.loader.load()
        
        self.cache = CacheManager(CACHE_PATH, True)
        self.cache.load()
        
        self.resolver = DataResolver(self.loader, self.cache)
        self.resolver.resolve_all()
        # Ensure cache is saved after resolution (to verify dynamic dict fetch)
        self.cache.save()
        
        self.executor = CommandExecutor(self.resolver)

    def test_strict_true(self):
        # Alias: strict (strict=true)
        # 1. Exact match
        chain, vars, is_help, remaining = self.executor.find_command(["strict"])
        self.assertIsNotNone(chain)
        self.assertEqual(remaining, [])
        
        # 2. Extra args -> remaining populated
        chain, vars, is_help, remaining = self.executor.find_command(["strict", "extra"])
        self.assertEqual(remaining, ["extra"])
        
        # 3. Execution rejection
        with patch('dynamic_alias.executor.print_formatted_text') as mock_print:
            with patch('subprocess.run') as mock_run:
                self.executor.execute(chain, vars, remaining)
                mock_run.assert_not_called()
                # Should verify error print containing "Strict mode"
                args, _ = mock_print.call_args
                self.assertIn("Strict mode", str(args[0]))

    def test_strict_false(self):
        # Alias: loose (strict=false)
        chain, vars, is_help, remaining = self.executor.find_command(["loose", "extra"])
        self.assertEqual(remaining, ["extra"])
        
        # Execution append
        with patch('dynamic_alias.executor.print_formatted_text'):
            with patch('subprocess.run') as mock_run:
                self.executor.execute(chain, vars, remaining)
                mock_run.assert_called()
                # Verify "extra" is in the command string
                cmd_arg = mock_run.call_args[0][0]
                self.assertIn("extra", cmd_arg)

    def test_timeout_fail(self):
        # Alias: sleep_fail (timeout=1, sleeps 3)
        chain, vars, is_help, remaining = self.executor.find_command(["sleep_fail"])
        
        # We assume subprocess.run actually runs the command 'python -c ...'
        # Since we use real subprocess.run in the code (unless mocked), we should let it run
        # but we need to capture output to avoid spamming test runner?
        # The executor prints to stdout/stderr.
        # But wait, unit tests usually shouldn't wait 3 seconds if we can help it.
        # However, user asked for timeout validation using compatible sleep.
        # So we SHOULD let it run.
        
        # We need to capture stdout/stderr from executre methods print statements
        with patch('dynamic_alias.executor.print') as mock_print: 
             # Also executor uses print_formatted_text
            with patch('dynamic_alias.executor.print_formatted_text') as mock_pft:
                 self.executor.execute(chain, vars, remaining)
                 
                 # It should catch TimeoutExpired internally and print Error
                 # The executor uses subprocess.run(..., timeout=timeout)
                 # So it raises TimeoutExpired.
                 # Executor catches it and prints "Error: Command timed out..."
                 
                 # Verify one of prints contained "timed out"
                 # We need to inspect all calls to print
                 found_timeout_msg = False
                 for call in mock_print.call_args_list:
                     if "timed out" in str(call):
                         found_timeout_msg = True
                         break
                 self.assertTrue(found_timeout_msg, "Should define timeout error message")

    def test_timeout_success(self):
        # Alias: sleep_success (timeout=5, runs fast)
        chain, vars, is_help, remaining = self.executor.find_command(["sleep_success"])
        
        with patch('dynamic_alias.executor.print') as mock_print: 
             with patch('dynamic_alias.executor.print_formatted_text'):
                 self.executor.execute(chain, vars, remaining)
                 # Should NOT show timeout error
                 for call in mock_print.call_args_list:
                     self.assertNotIn("timed out", str(call))

    def test_dynamic_dict_resolution(self):
        # Check if 'nodes' were resolved/cached
        nodes = self.resolver.resolved_data.get('nodes')
        self.assertIsNotNone(nodes)
        self.assertTrue(len(nodes) >= 2)
        self.assertEqual(nodes[0]['name'], 'node1')

if __name__ == '__main__':
    unittest.main()
