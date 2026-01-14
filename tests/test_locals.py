"""
Locals Storage Tests
Test Rules:
    @system_rules.txt
    @global-test-rules.md

Tests for:
- Rule 1.2.25: Local variables in cache as _locals
- Rule 1.2.26: --${shortcut}-set-locals flag
- Rule 1.2.27: --${shortcut}-clear-locals flag
"""
import os
import sys
import unittest
import tempfile
from unittest.mock import MagicMock

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

from dynamic_alias.cache import CacheManager


class TestLocalsStorage(unittest.TestCase):
    """Test Rule 1.2.25: Local variables storage in cache."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_set_local_creates_locals_entry(self):
        """set_local should create _locals entry if not exists."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {}
        
        cache.set_local('test_key', 'test_value')
        
        self.assertIn('_locals', cache.cache)
        self.assertEqual(cache.cache['_locals']['test_key'], 'test_value')
    
    def test_set_local_overwrites_existing(self):
        """set_local should overwrite existing value."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'_locals': {'key': 'old_value'}}
        
        cache.set_local('key', 'new_value')
        
        self.assertEqual(cache.cache['_locals']['key'], 'new_value')
    
    def test_get_local_returns_value(self):
        """get_local should return stored value."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'_locals': {'my_key': 'my_value'}}
        
        result = cache.get_local('my_key')
        
        self.assertEqual(result, 'my_value')
    
    def test_get_local_returns_none_if_not_found(self):
        """get_local should return None if key not found."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'_locals': {}}
        
        result = cache.get_local('nonexistent')
        
        self.assertIsNone(result)
    
    def test_get_local_returns_none_if_no_locals(self):
        """get_local should return None if _locals doesn't exist."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {}
        
        result = cache.get_local('any_key')
        
        self.assertIsNone(result)
    
    def test_get_locals_returns_all(self):
        """get_locals should return all local variables."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'_locals': {'key1': 'val1', 'key2': 'val2'}}
        
        result = cache.get_locals()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result['key1'], 'val1')
        self.assertEqual(result['key2'], 'val2')
    
    def test_get_locals_returns_empty_dict_if_none(self):
        """get_locals should return empty dict if no locals."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {}
        
        result = cache.get_locals()
        
        self.assertEqual(result, {})


class TestClearLocals(unittest.TestCase):
    """Test Rule 1.2.27: --${shortcut}-clear-locals"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_clear_locals_removes_all_locals(self):
        """clear_locals should remove _locals entry."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {
            '_locals': {'key1': 'val1', 'key2': 'val2'},
            'other_data': {}
        }
        
        result = cache.clear_locals()
        
        self.assertTrue(result)
        self.assertNotIn('_locals', cache.cache)
    
    def test_clear_locals_preserves_other_data(self):
        """clear_locals should preserve other cache entries."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {
            '_locals': {'key': 'val'},
            '_history': ['cmd1'],
            'dynamic_dict': {'timestamp': 123, 'data': []}
        }
        
        cache.clear_locals()
        
        self.assertIn('_history', cache.cache)
        self.assertIn('dynamic_dict', cache.cache)
    
    def test_clear_locals_returns_false_when_no_locals(self):
        """clear_locals should return False if no locals exist."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {}
        
        result = cache.clear_locals()
        
        self.assertFalse(result)
    
    def test_clear_locals_saves_to_file(self):
        """clear_locals should persist changes to file."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'_locals': {'key': 'val'}}
        cache.save()
        
        cache.clear_locals()
        
        # Load fresh and verify
        cache2 = CacheManager(self.cache_path, enabled=True)
        cache2.load()
        self.assertNotIn('_locals', cache2.cache)


class TestLocalsPersistence(unittest.TestCase):
    """Test locals persistence across cache loads."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_locals_persist_after_save_load(self):
        """Locals should persist after save and load."""
        # Set locals
        cache = CacheManager(self.cache_path, enabled=True)
        cache.set_local('persist_key', 'persist_value')
        
        # Load fresh instance
        cache2 = CacheManager(self.cache_path, enabled=True)
        cache2.load()
        
        result = cache2.get_local('persist_key')
        self.assertEqual(result, 'persist_value')


if __name__ == '__main__':
    unittest.main()
