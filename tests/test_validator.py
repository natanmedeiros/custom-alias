"""
Config Validator Tests
Test Rules:
    @system_rules.txt
    @global-test-rules.md

Tests for:
- Rule 1.1.14: --dya-validate flag
- Rule 1.1.15: Check undefined dict/dynamic_dict references
- Rule 1.1.16: Check correct structure and keys
- Rule 1.1.17: User-friendly output
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

from dynamic_alias.validator import ConfigValidator, ValidationReport, ValidationResult


class TestValidatorFileChecks(unittest.TestCase):
    """Test file existence and YAML syntax validation."""
    
    def test_file_not_found(self):
        """Validator should fail if config file doesn't exist."""
        validator = ConfigValidator("/nonexistent/path/config.yaml")
        report = validator.validate()
        
        self.assertFalse(report.passed)
        self.assertEqual(report.failed_count, 1)
        self.assertIn("not found", report.results[0].message)
    
    def test_valid_yaml_syntax(self):
        """Validator should pass for valid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
config:
  verbose: true

---
type: dict
name: test
data:
  - key: value
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            # Check YAML syntax check passed
            yaml_check = next((r for r in report.results if 'YAML syntax' in r.message), None)
            self.assertIsNotNone(yaml_check)
            self.assertTrue(yaml_check.passed)
            
        os.unlink(f.name)
    
    def test_invalid_yaml_syntax(self):
        """Validator should fail for invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
config:
  verbose: true

---
type: dict
name: test
data:
  - key: value
    bad indentation here
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            self.assertFalse(report.passed)
            
        os.unlink(f.name)


class TestValidatorStructure(unittest.TestCase):
    """Test block structure validation (Rule 1.1.16)."""
    
    def test_dict_required_fields(self):
        """Dict must have type, name, data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dict
name: valid_dict
data:
  - key: value
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            # Should pass for valid dict
            dict_check = next((r for r in report.results 
                              if "valid_dict" in r.message and "required fields" in r.message), None)
            self.assertIsNotNone(dict_check)
            self.assertTrue(dict_check.passed)
            
        os.unlink(f.name)
    
    def test_dict_missing_data(self):
        """Dict without data should fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dict
name: incomplete_dict
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            self.assertFalse(report.passed)
            missing_check = next((r for r in report.results 
                                 if "missing required fields" in r.message), None)
            self.assertIsNotNone(missing_check)
            
        os.unlink(f.name)
    
    def test_dynamic_dict_required_fields(self):
        """Dynamic dict must have type, name, command, mapping."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: valid_dyn
command: echo '[]'
mapping:
  key: value
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            dyn_check = next((r for r in report.results 
                             if "valid_dyn" in r.message and "required fields" in r.message), None)
            self.assertIsNotNone(dyn_check)
            self.assertTrue(dyn_check.passed)
            
        os.unlink(f.name)
    
    def test_dynamic_dict_missing_mapping(self):
        """Dynamic dict without mapping should fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: incomplete_dyn
command: echo '[]'
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            self.assertFalse(report.passed)
            
        os.unlink(f.name)
    
    def test_command_required_fields(self):
        """Command must have type, name, alias, command."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: command
name: valid_cmd
alias: test
command: echo test
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            cmd_check = next((r for r in report.results 
                             if "valid_cmd" in r.message and "required fields" in r.message), None)
            self.assertIsNotNone(cmd_check)
            self.assertTrue(cmd_check.passed)
            
        os.unlink(f.name)
    
    def test_config_invalid_keys(self):
        """Config block with invalid keys should fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
config:
  verbose: true
  invalid-custom-key: test
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            config_check = next((r for r in report.results 
                                if "Unknown config keys" in r.message), None)
            self.assertIsNotNone(config_check)
            self.assertFalse(config_check.passed)
            
        os.unlink(f.name)


class TestValidatorReferences(unittest.TestCase):
    """Test undefined reference validation (Rule 1.1.15)."""
    
    def test_valid_references(self):
        """All references pointing to defined sources should pass."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dict
name: servers
data:
  - name: prod
    host: 10.0.0.1

---
type: command
name: SSH
alias: ssh $${servers.name}
command: ssh $${servers.host}
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            ref_check = next((r for r in report.results 
                             if "references are valid" in r.message), None)
            self.assertIsNotNone(ref_check)
            self.assertTrue(ref_check.passed)
            
        os.unlink(f.name)
    
    def test_undefined_reference_in_command(self):
        """Command referencing undefined source should fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: command
name: Bad Command
alias: test $${undefined_source.key}
command: echo test
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            self.assertFalse(report.passed)
            ref_check = next((r for r in report.results 
                             if "undefined source" in r.message), None)
            self.assertIsNotNone(ref_check)
            self.assertIn("undefined_source", ref_check.message)
            
        os.unlink(f.name)
    
    def test_undefined_reference_in_dynamic_dict(self):
        """Dynamic dict referencing undefined source should fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: bad_dyn
command: echo '$${undefined.key}'
mapping:
  key: key
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            self.assertFalse(report.passed)
            
        os.unlink(f.name)


class TestValidatorPriority(unittest.TestCase):
    """Test priority order validation for dynamic_dict chaining."""
    
    def test_valid_priority_order(self):
        """Higher priority dynamic_dict can reference lower priority one."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: first
priority: 1
command: echo '[]'
mapping:
  key: key

---
type: dynamic_dict
name: second
priority: 2
command: echo '$${first.key}'
mapping:
  key: key
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            # With lazy loading, priority check is just informational
            priority_check = next((r for r in report.results 
                                  if "Priority order checked" in r.message), None)
            self.assertIsNotNone(priority_check)
            self.assertTrue(priority_check.passed)
            
        os.unlink(f.name)
    
    def test_invalid_priority_order(self):
        """Lower priority referencing higher priority should show warning but pass."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: dynamic_dict
name: first
priority: 2
command: echo '[]'
mapping:
  key: key

---
type: dynamic_dict
name: second
priority: 1
command: echo '$${first.key}'
mapping:
  key: key
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            # With lazy loading, priority order is just a warning, validation passes
            # Check for the WARNING message
            warning_check = next((r for r in report.results 
                                 if "WARNING" in r.message and "priority" in r.message.lower()), None)
            self.assertIsNotNone(warning_check)
            self.assertTrue(warning_check.passed)  # Warnings have passed=True
            
        os.unlink(f.name)
    
    def test_static_dict_always_available(self):
        """Dynamic dict can always reference static dict regardless of priority."""
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
            
            # Should not have priority errors (static dicts have implicit priority 0)
            priority_failures = [r for r in report.results 
                                if "priority" in r.message.lower() and not r.passed]
            self.assertEqual(len(priority_failures), 0)
            
        os.unlink(f.name)


class TestValidatorReport(unittest.TestCase):
    """Test validation report structure (Rule 1.1.17)."""
    
    def test_report_has_passed_count(self):
        """Report should track passed and failed counts."""
        report = ValidationReport(config_path="test.yaml")
        report.add(ValidationResult(passed=True, message="Test 1"))
        report.add(ValidationResult(passed=False, message="Test 2"))
        report.add(ValidationResult(passed=True, message="Test 3"))
        
        self.assertEqual(report.passed_count, 2)
        self.assertEqual(report.failed_count, 1)
        self.assertFalse(report.passed)
    
    def test_result_has_hint_and_location(self):
        """Validation result can include hint and location."""
        result = ValidationResult(
            passed=False,
            message="Test error",
            hint="Fix this way",
            location="Block 5"
        )
        
        self.assertEqual(result.hint, "Fix this way")
        self.assertEqual(result.location, "Block 5")
    
    def test_full_validation_on_test_config(self):
        """Full validation on tests/dya.yaml should pass."""
        config_path = os.path.join(os.path.dirname(__file__), "dya.yaml")
        
        validator = ConfigValidator(config_path)
        report = validator.validate()
        
        self.assertTrue(report.passed, 
                       f"Validation failed: {[r.message for r in report.results if not r.passed]}")


class TestValidatorArrayAlias(unittest.TestCase):
    """Test args.alias array validation."""
    
    def test_valid_array_alias_same_vars(self):
        """Array aliases with same variable structure should pass."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: command
name: Valid Array
alias: test
command: echo test
args:
  - alias: ["-o ${file}", "--output ${file}"]
    command: -o ${file}
    helper: Output file
  - alias: ["-v", "--verbose"]
    command: --verbose
    helper: Verbose mode
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            # Should not have array alias errors
            array_errors = [r for r in report.results 
                          if "inconsistent variable structure" in r.message]
            self.assertEqual(len(array_errors), 0)
            
        os.unlink(f.name)
    
    def test_invalid_array_alias_different_vars(self):
        """Array aliases with different variable structure should fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: command
name: Invalid Array
alias: test
command: echo test
args:
  - alias: ["-o ${file}", "--output"]
    command: -o ${file}
    helper: Output file - INVALID
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            # Should have array alias error
            array_errors = [r for r in report.results 
                          if "inconsistent variable structure" in r.message]
            self.assertEqual(len(array_errors), 1)
            self.assertFalse(array_errors[0].passed)
            
        os.unlink(f.name)
    
    def test_invalid_array_alias_different_var_count(self):
        """Array aliases with different number of variables should fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
---
type: command
name: Invalid Var Count
alias: test
command: echo test
args:
  - alias: ["-i ${input} ${output}", "--input ${input}"]
    command: -i ${input}
    helper: Input file - INVALID (different var count)
""")
            f.flush()
            
            validator = ConfigValidator(f.name)
            report = validator.validate()
            
            # Should have array alias error
            array_errors = [r for r in report.results 
                          if "inconsistent variable structure" in r.message]
            self.assertEqual(len(array_errors), 1)
            
        os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()

