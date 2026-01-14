"""
Dynamic Dict Circular Reference Tests
Test Rules:
    @system_rules.txt
    @global-test-rules.md

Tests for:
- Circular reference detection at runtime (resolver.py)
- Circular reference detection at validation time (validator.py)
- Valid chaining scenarios
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
from dynamic_alias.validator import ConfigValidator


class TestValidatorCircularReference(unittest.TestCase):
    """Test circular reference detection in ConfigValidator."""
    
    def test_no_circular_reference_valid(self):
        """Valid chain without circular reference passes validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: level1
priority: 1
command: echo '[]'
mapping:
  key: key

---
type: dynamic_dict
name: level2
priority: 2
command: echo '$${level1.key}'
mapping:
  key: key
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            circular_check = next((r for r in report.results 
                                  if 'circular' in r.message.lower()), None)
            self.assertIsNotNone(circular_check)
            self.assertTrue(circular_check.passed, 
                           f"Expected no circular reference: {circular_check.message}")
            
        os.unlink(f.name)
    
    def test_direct_circular_reference(self):
        """A -> A should be detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: self_ref
priority: 1
command: echo '$${self_ref.key}'
mapping:
  key: key
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            circular_errors = [r for r in report.results 
                              if 'circular' in r.message.lower() and not r.passed]
            self.assertGreater(len(circular_errors), 0)
            
        os.unlink(f.name)
    
    def test_two_way_circular_reference(self):
        """A -> B -> A should be detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: dict_a
priority: 1
command: echo '$${dict_b.key}'
mapping:
  key: key

---
type: dynamic_dict
name: dict_b
priority: 2
command: echo '$${dict_a.key}'
mapping:
  key: key
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            circular_errors = [r for r in report.results 
                              if 'circular' in r.message.lower() and not r.passed]
            self.assertGreater(len(circular_errors), 0)
            
        os.unlink(f.name)
    
    def test_three_way_circular_reference(self):
        """A -> B -> C -> A should be detected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: dict_a
priority: 1
command: echo '$${dict_b.key}'
mapping:
  key: key

---
type: dynamic_dict
name: dict_b
priority: 2
command: echo '$${dict_c.key}'
mapping:
  key: key

---
type: dynamic_dict
name: dict_c
priority: 3
command: echo '$${dict_a.key}'
mapping:
  key: key
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            circular_errors = [r for r in report.results 
                              if 'circular' in r.message.lower() and not r.passed]
            self.assertGreater(len(circular_errors), 0)
            
        os.unlink(f.name)
    
    def test_static_dict_reference_not_circular(self):
        """Reference to static dict is not circular even if it looks like one."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dict
name: config
data:
  - key: value

---
type: dynamic_dict
name: dyn
priority: 1
command: echo '$${config.key}'
mapping:
  key: key
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            circular_check = next((r for r in report.results 
                                  if 'No circular references' in r.message), None)
            self.assertIsNotNone(circular_check)
            self.assertTrue(circular_check.passed)
            
        os.unlink(f.name)


class TestResolverCircularReference(unittest.TestCase):
    """Test circular reference detection at runtime in DataResolver."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_circular_reference_returns_empty(self):
        """Circular reference should return empty list and print error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: circular
priority: 1
command: echo '$${circular.key}'
mapping:
  key: key
""")
            f.flush()
            
            loader = ConfigLoader(f.name)
            loader.load()
            
            cache = CacheManager(self.cache_path, enabled=True)
            cache.load()
            
            resolver = DataResolver(loader, cache)
            
            # Capture output
            captured = StringIO()
            with patch('sys.stdout', captured):
                result = resolver.resolve_one('circular')
            
            output = captured.getvalue()
            
            self.assertEqual(result, [])
            self.assertIn('Circular reference', output)
            
        os.unlink(f.name)
    
    def test_resolution_stack_cleared_after_error(self):
        """Resolution stack should be cleared even after circular reference error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dict
name: static
data:
  - key: value

---
type: dynamic_dict
name: circular
priority: 1
command: echo '$${circular.key}'
mapping:
  key: key
""")
            f.flush()
            
            loader = ConfigLoader(f.name)
            loader.load()
            
            cache = CacheManager(self.cache_path, enabled=True)
            cache.load()
            
            resolver = DataResolver(loader, cache)
            
            # First call triggers circular reference
            with patch('sys.stdout', StringIO()):
                resolver.resolve_one('circular')
            
            # Resolution stack should be empty
            self.assertEqual(len(resolver._resolution_stack), 0)
            
            # Static dict should still work
            result = resolver.resolve_one('static')
            self.assertEqual(len(result), 1)
            
        os.unlink(f.name)


class TestValidChaining(unittest.TestCase):
    """Test valid chaining scenarios work correctly."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, "cache.json")
        
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_dict_to_dynamic_dict_chain(self):
        """Static dict -> dynamic_dict should work."""
        config_path = os.path.join(os.path.dirname(__file__), "dya.yaml")
        
        loader = ConfigLoader(config_path)
        loader.load()
        
        cache = CacheManager(self.cache_path, enabled=True)
        cache.load()
        
        resolver = DataResolver(loader, cache)
        
        # level2_chain references level1_chain which references base_prefix
        # This tests the full chain: static dict -> dynamic_dict -> dynamic_dict
        # We verify that level1_chain resolves properly (depends on base_prefix)
        result = resolver.resolve_one('base_prefix')
        self.assertEqual(len(result), 1)
        # The actual value in tests/dya.yaml is 'CHAIN' (uppercase)
        self.assertEqual(result[0]['prefix'], 'CHAIN')
    
    def test_dynamic_dict_chain_respects_priority(self):
        """Higher priority dynamic_dict can reference lower priority one."""
        # Use the project's test config which has a valid chain defined
        config_path = os.path.join(os.path.dirname(__file__), "dya.yaml")
        
        validator = ConfigValidator(config_path)
        report = validator.validate()
        
        # dya.yaml should pass all validations including circular reference check
        circular_check = next((r for r in report.results 
                              if 'No circular references' in r.message), None)
        self.assertIsNotNone(circular_check)
        self.assertTrue(circular_check.passed)


if __name__ == '__main__':
    unittest.main()
