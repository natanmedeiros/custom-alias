import unittest
from unittest.mock import MagicMock, patch
from dynamic_alias.executor import CommandExecutor
from dynamic_alias.resolver import DataResolver
from dynamic_alias.models import CommandConfig, DynamicDictConfig

class TestTimeout(unittest.TestCase):
    def setUp(self):
        # Setup Resolver and Executor
        self.mock_config_loader = MagicMock()
        self.mock_cache = MagicMock()
        self.resolver = DataResolver(self.mock_config_loader, self.mock_cache)
        self.resolver.resolved_data = {}
        self.executor = CommandExecutor(self.resolver)

    @patch('dynamic_alias.executor.print_formatted_text')
    @patch('subprocess.run')
    def test_command_timeout(self, mock_run, mock_print):
        # 1. Default Timeout (0 -> None)
        cmd_default = CommandConfig(name="DefaultTimeout", alias="def", command="echo", timeout=0)
        
        self.executor.execute([cmd_default], {}, [])
        args, kwargs = mock_run.call_args
        self.assertIsNone(kwargs.get('timeout'))

        # 2. Custom Timeout
        cmd_custom = CommandConfig(name="CustomTimeout", alias="cust", command="echo", timeout=5)
        
        self.executor.execute([cmd_custom], {}, [])
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get('timeout'), 5)

    @patch('subprocess.run')
    def test_dynamic_dict_timeout(self, mock_run):
        # Setup mock return valid json so it doesn't fail before subprocess call
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '[{"key": "val"}]'

        # 1. Default Timeout (10)
        dd_default = DynamicDictConfig(name="DefaultDD", command="list", mapping={}, timeout=10)
        self.resolver._execute_dynamic_source(dd_default)
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get('timeout'), 10)

        # 2. Custom Timeout
        dd_custom = DynamicDictConfig(name="CustomDD", command="list", mapping={}, timeout=30)
        self.resolver._execute_dynamic_source(dd_custom)
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get('timeout'), 30)

if __name__ == '__main__':
    unittest.main()
