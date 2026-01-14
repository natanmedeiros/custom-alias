"""
Dynamic Dict JSON Validation Tests
Test Rules:
    @system_rules.txt
    @global-test-rules.md

Tests for:
- Valid JSON output parsing
- Invalid JSON output error handling
- Empty output error handling
- Timeout error handling
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from io import StringIO

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
import subprocess


class TestDynamicDictJsonValidation(unittest.TestCase):
    """Test JSON validation for dynamic dict command output."""
    
    @classmethod
    def setUpClass(cls):
        cls.config_file = os.path.join(os.path.dirname(__file__), "dya.yaml")
        
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "dya.json")
        
        self.loader = ConfigLoader(self.config_file)
        self.loader.load()
        
        self.cache = CacheManager(self.cache_path, enabled=True)
        self.cache.load()
        
        self.resolver = DataResolver(self.loader, self.cache)

    def tearDown(self):
        self.temp_dir.cleanup()

    # =========================================================================
    # Valid JSON Tests
    # =========================================================================
    
    def test_valid_json_array_parses_correctly(self):
        """Valid JSON array output should parse correctly."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = '[{"id": "node-1", "ip": "10.0.0.1"}]'
            mock_run.return_value.returncode = 0
            
            data = self.resolver.resolve_one('dynamic_nodes')
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['name'], 'node-1')
            self.assertEqual(data[0]['ip'], '10.0.0.1')
    
    def test_valid_json_object_parses_correctly(self):
        """Valid JSON object (single item) should be wrapped in list."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{"id": "single", "ip": "10.0.0.5"}'
            mock_run.return_value.returncode = 0
            
            data = self.resolver.resolve_one('dynamic_nodes')
            
            self.assertIsNotNone(data)
            self.assertEqual(len(data), 1)
    
    # =========================================================================
    # Invalid JSON Tests
    # =========================================================================
    
    def test_invalid_json_outputs_error(self):
        """Invalid JSON output should print detailed error."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = 'not valid json at all'
            mock_run.return_value.returncode = 0
            
            # Capture stderr/stdout
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                data = self.resolver.resolve_one('dynamic_nodes')
            
            output = captured_output.getvalue()
            
            # Should return empty list
            self.assertEqual(data, [])
            
            # Should contain error details
            self.assertIn("Invalid JSON output", output)
            self.assertIn("JSON Error:", output)
            self.assertIn("Output:", output)
    
    def test_invalid_json_shows_command(self):
        """Invalid JSON error should show the command that was executed."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{broken: json}'
            mock_run.return_value.returncode = 0
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                self.resolver.resolve_one('dynamic_nodes')
            
            output = captured_output.getvalue()
            self.assertIn("Command:", output)
    
    def test_invalid_json_shows_position(self):
        """Invalid JSON error should show the error position."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = '{"valid": "start", broken}'
            mock_run.return_value.returncode = 0
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                self.resolver.resolve_one('dynamic_nodes')
            
            output = captured_output.getvalue()
            self.assertIn("position", output.lower())
    
    def test_invalid_json_shows_output_preview(self):
        """Invalid JSON error should show preview of the output."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = 'Error: AWS CLI not configured'
            mock_run.return_value.returncode = 0
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                self.resolver.resolve_one('dynamic_nodes')
            
            output = captured_output.getvalue()
            self.assertIn("AWS CLI not configured", output)
    
    # =========================================================================
    # Empty Output Tests
    # =========================================================================
    
    def test_empty_output_shows_error(self):
        """Empty command output should show specific error."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            mock_run.return_value.returncode = 0
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                data = self.resolver.resolve_one('dynamic_nodes')
            
            output = captured_output.getvalue()
            
            self.assertEqual(data, [])
            self.assertIn("no output", output.lower())
    
    def test_whitespace_only_output_shows_error(self):
        """Whitespace-only output should be treated as empty."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = '   \n\t  \n  '
            mock_run.return_value.returncode = 0
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                data = self.resolver.resolve_one('dynamic_nodes')
            
            self.assertEqual(data, [])
    
    # =========================================================================
    # Timeout Tests
    # =========================================================================
    
    def test_timeout_shows_specific_error(self):
        """Command timeout should show specific timeout error."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd='test', timeout=10)
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                data = self.resolver.resolve_one('dynamic_nodes')
            
            output = captured_output.getvalue()
            
            self.assertEqual(data, [])
            self.assertIn("timed out", output.lower())
    
    # =========================================================================
    # Edge Cases
    # =========================================================================
    
    def test_long_output_preview_is_truncated(self):
        """Long invalid output should be truncated in error message."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            # Create output longer than 200 chars
            long_output = "x" * 300
            mock_run.return_value.stdout = long_output
            mock_run.return_value.returncode = 0
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                self.resolver.resolve_one('dynamic_nodes')
            
            output = captured_output.getvalue()
            
            # Should be truncated with ...
            self.assertIn("...", output)
    
    def test_command_error_returncode_handled(self):
        """Non-zero return code should show stderr error."""
        with patch('dynamic_alias.resolver.subprocess.run') as mock_run:
            mock_run.return_value.stdout = ''
            mock_run.return_value.stderr = 'Command failed: permission denied'
            mock_run.return_value.returncode = 1
            
            captured_output = StringIO()
            with patch('sys.stdout', captured_output):
                data = self.resolver.resolve_one('dynamic_nodes')
            
            output = captured_output.getvalue()
            
            self.assertEqual(data, [])
            self.assertIn("permission denied", output.lower())


if __name__ == '__main__':
    unittest.main()
