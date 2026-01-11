
import pytest
import sys
import os
import shutil
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dynamic_alias.main import main
from dynamic_alias.constants import CUSTOM_SHORTCUT

@pytest.fixture
def mock_home(tmp_path):
    """Mocks user home to a tmp path"""
    with patch('os.path.expanduser') as mock_expand:
        def side_effect(path):
            if path.startswith('~'):
                return str(tmp_path / path[2:])
            return path
        mock_expand.side_effect = side_effect
        yield tmp_path

def test_bundled_config_copy_first_run(mock_home, capsys):
    # Scenario:
    # 1. User config missing in HOME
    # 2. Bundled config exists in package
    # 3. Expectation: Load bundled, Copy to HOME, Print message.
    
    bundled_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        'src', 'dynamic_alias', f'{CUSTOM_SHORTCUT}.yaml'
    )
    
    # We need to mock existence of bundled config if it doesn't exist in dev env yet
    # But main.py looks for it relative to __file__.
    # For test purpose, we can use patch on os.path.exists
    
    real_exists = os.path.exists
    
    def exists_side_effect(path):
        # If checking for bundled config, verify we are mocking it as True
        if "dynamic_alias" in path and path.endswith(f"{CUSTOM_SHORTCUT}.yaml"):
            return True
        # If checking for home config, let it rely on our empty mock_home
        if str(mock_home) in path:
            return real_exists(path)
        return real_exists(path)

    # We also need ConfigLoader to not fail when loading our fake bundled path
    with patch('os.path.exists', side_effect=exists_side_effect):
        with patch('dynamic_alias.config.ConfigLoader.load') as mock_load: 
            # We mock load() to prevent actual file read error since we faked existence
            
            # Use --{shortcut} arg to avoid any args issue? No, run without args to trigger loading default.
            argv = ['script_name']
            
            # We need to mock shutil.copy to verify copy action without needing real file
            with patch('shutil.copy') as mock_copy:
                with patch('sys.argv', argv):
                    try:
                        main()
                    except SystemExit:
                        # main might exit or run interactive shell mock
                        pass
                    except Exception:
                        pass
                
                # Verify copy was called
                expected_dest = str(mock_home / f".{CUSTOM_SHORTCUT}.yaml")
                mock_copy.assert_called_once()
                args, _ = mock_copy.call_args
                assert args[1] == expected_dest
                
                captured = capsys.readouterr()
                assert "First run detected" in captured.out

def test_bundled_config_fallback_load(mock_home, capsys):
    # Scenario: Only verify it attempts to load bundled when user config missing
    
    bundled_path = "mock/path/bundled.yaml"
    
    with patch('os.path.dirname') as mock_dirname:
        mock_dirname.return_value = "mock/path"
        
        with patch('os.path.exists') as mock_exists:
            # os.path.exists logic:
            # 1. ConfigLoader checks user config -> False
            # 2. main.py checks bundled config -> True
            # 3. main.py checks user home config (for copy) -> True (Simulate it already exists so no copy)
            
            def exists_side_effect(path):
                if path == f"mock/path\\{CUSTOM_SHORTCUT}.yaml" or path == f"mock/path/{CUSTOM_SHORTCUT}.yaml":
                    return True
                if str(mock_home) in path:
                    return True # Simulate exists to skip copy
                if "config.yaml" in path: # default user config check in main
                    return False
                return False
                
            mock_exists.side_effect = exists_side_effect
            
            with patch('dynamic_alias.config.ConfigLoader') as MockLoader:
                argv = ['script_name']
                with patch('sys.argv', argv):
                    try:
                        main()
                    except:
                        pass
                
                # Verify ConfigLoader initialized with bundled path
                # Note: os.path.dirname was mocked, so we expect mocked path
                # The code uses os.path.dirname(__file__) which we mocked.
                
                # Check call args of ConfigLoader
                # It might be called multiple times?
                # 1. Load User Config (fail) -> NO, main.py checks existence first?
                # Wait, main.py instantiates ConfigLoader(final_config_path) directly.
                # ConfigLoader.load() raises FileNotFoundError.
                # So verify second instantiation.
                
                calls = MockLoader.call_args_list
                # Last call should be bundled path
                assert len(calls) >= 2 
                # Call 0: User config path
                # Call 1: Bundled config path
                
                check_path = f"mock/path/{CUSTOM_SHORTCUT}.yaml"
                found = any(check_path in str(call) for call in calls) or \
                        any(f"mock/path\\{CUSTOM_SHORTCUT}.yaml" in str(call) for call in calls)
                assert found
