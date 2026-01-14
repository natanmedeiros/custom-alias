"""
Cache Management Flags Tests
Test Rules:
    @system_rules.txt
    @global-test-rules.md

Tests for:
- Rule 1.2.21: --${shortcut}-clear-cache (purge non-underscore entries)
- Rule 1.2.22: Purge expired cache entries on load
- Rule 1.2.23: --${shortcut}-clear-history (purge _history)
- Rule 1.2.24: --${shortcut}-clear-all (delete cache file)
"""
import os
import sys
import unittest
import tempfile
import json
import time
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

from dynamic_alias.cache import CacheManager


class TestClearCache(unittest.TestCase):
    """Test Rule 1.2.21: --${shortcut}-clear-cache"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_clear_cache_removes_non_underscore_entries(self):
        """clear_cache should remove entries not starting with underscore."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {
            'dynamic_dict1': {'timestamp': int(time.time()), 'data': [{'key': 'val1'}]},
            'dynamic_dict2': {'timestamp': int(time.time()), 'data': [{'key': 'val2'}]},
            '_history': ['cmd1', 'cmd2']
        }
        cache.save()
        
        count = cache.clear_cache()
        
        self.assertEqual(count, 2)
        self.assertNotIn('dynamic_dict1', cache.cache)
        self.assertNotIn('dynamic_dict2', cache.cache)
        self.assertIn('_history', cache.cache)
    
    def test_clear_cache_preserves_history(self):
        """clear_cache should preserve _history entry."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {
            'data': {'timestamp': 123, 'data': []},
            '_history': ['cmd1', 'cmd2', 'cmd3']
        }
        
        cache.clear_cache()
        
        self.assertIn('_history', cache.cache)
        self.assertEqual(len(cache.cache['_history']), 3)
    
    def test_clear_cache_saves_to_file(self):
        """clear_cache should persist changes to file."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'data': {'timestamp': 123, 'data': []}}
        cache.save()
        
        cache.clear_cache()
        
        # Load fresh and verify
        cache2 = CacheManager(self.cache_path, enabled=True)
        cache2.load()
        self.assertNotIn('data', cache2.cache)
    
    def test_clear_cache_returns_zero_when_empty(self):
        """clear_cache should return 0 when no entries to clear."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'_history': ['cmd1']}
        
        count = cache.clear_cache()
        
        self.assertEqual(count, 0)


class TestClearHistory(unittest.TestCase):
    """Test Rule 1.2.23: --${shortcut}-clear-history"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_clear_history_removes_history(self):
        """clear_history should remove _history entry."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {
            '_history': ['cmd1', 'cmd2'],
            'data': {'timestamp': 123, 'data': []}
        }
        
        result = cache.clear_history()
        
        self.assertTrue(result)
        self.assertNotIn('_history', cache.cache)
    
    def test_clear_history_preserves_cache_data(self):
        """clear_history should preserve other cache entries."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {
            '_history': ['cmd1'],
            'dynamic_dict': {'timestamp': 123, 'data': [{'key': 'val'}]}
        }
        
        cache.clear_history()
        
        self.assertIn('dynamic_dict', cache.cache)
    
    def test_clear_history_returns_false_when_no_history(self):
        """clear_history should return False if no history exists."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {}
        
        result = cache.clear_history()
        
        self.assertFalse(result)
    
    def test_clear_history_saves_to_file(self):
        """clear_history should persist changes to file."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'_history': ['cmd1']}
        cache.save()
        
        cache.clear_history()
        
        # Load fresh and verify
        cache2 = CacheManager(self.cache_path, enabled=True)
        cache2.load()
        self.assertNotIn('_history', cache2.cache)


class TestClearAll(unittest.TestCase):
    """Test Rule 1.2.24: --${shortcut}-clear-all"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_delete_all_removes_file(self):
        """delete_all should delete the cache file."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'data': {}}
        cache.save()
        
        self.assertTrue(os.path.exists(self.cache_path))
        
        result = cache.delete_all()
        
        self.assertTrue(result)
        self.assertFalse(os.path.exists(self.cache_path))
    
    def test_delete_all_clears_in_memory_cache(self):
        """delete_all should clear in-memory cache."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {'key1': {}, 'key2': {}, '_history': []}
        cache.save()
        
        cache.delete_all()
        
        self.assertEqual(cache.cache, {})
    
    def test_delete_all_returns_false_when_no_file(self):
        """delete_all should return False if file doesn't exist."""
        cache = CacheManager(self.cache_path, enabled=True)
        
        result = cache.delete_all()
        
        self.assertFalse(result)


class TestPurgeExpired(unittest.TestCase):
    """Test Rule 1.2.22: Purge expired cache entries"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_purge_expired_removes_old_entries(self):
        """purge_expired should remove entries past TTL."""
        cache = CacheManager(self.cache_path, enabled=True)
        old_time = int(time.time()) - 1000  # 1000 seconds ago
        cache.cache = {
            'expired_dict': {'timestamp': old_time, 'data': []},
            'fresh_dict': {'timestamp': int(time.time()), 'data': []},
            '_history': ['cmd1']
        }
        
        ttl_map = {'expired_dict': 300, 'fresh_dict': 300}  # 5 min TTL
        count = cache.purge_expired(ttl_map)
        
        self.assertEqual(count, 1)
        self.assertNotIn('expired_dict', cache.cache)
        self.assertIn('fresh_dict', cache.cache)
    
    def test_purge_expired_preserves_history(self):
        """purge_expired should never remove _history."""
        cache = CacheManager(self.cache_path, enabled=True)
        cache.cache = {
            '_history': ['cmd1', 'cmd2']
        }
        
        count = cache.purge_expired({})
        
        self.assertEqual(count, 0)
        self.assertIn('_history', cache.cache)
    
    def test_purge_expired_uses_ttl_map(self):
        """purge_expired should use TTL from ttl_map."""
        cache = CacheManager(self.cache_path, enabled=True)
        old_time = int(time.time()) - 500  # 500 seconds ago
        cache.cache = {
            'short_ttl': {'timestamp': old_time, 'data': []},
            'long_ttl': {'timestamp': old_time, 'data': []}
        }
        
        ttl_map = {
            'short_ttl': 300,  # Expired (500 > 300)
            'long_ttl': 600    # Not expired (500 < 600)
        }
        count = cache.purge_expired(ttl_map)
        
        self.assertEqual(count, 1)
        self.assertNotIn('short_ttl', cache.cache)
        self.assertIn('long_ttl', cache.cache)


if __name__ == '__main__':
    unittest.main()
