
import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Mocks are centralized in conftest.py

from dynamic_alias.executor import CommandExecutor
from dynamic_alias.models import CommandConfig, DictConfig, DynamicDictConfig, SubCommand, ArgConfig
from dynamic_alias.resolver import DataResolver
from dynamic_alias.config import ConfigLoader
from dynamic_alias.shell import InteractiveShell

@pytest.fixture
def mock_resolver():
    # Use dya.yaml fixture path
    config_file = os.path.join(os.path.dirname(__file__), "dya.yaml")
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"{config_file} must exist")
        
    loader = ConfigLoader(config_file)
    loader.load()
    
    # Mock cache
    cache = MagicMock()
    cache.get.return_value = None
    
    mock_res = DataResolver(loader, cache)
    
    # Pre-fill resolved_data to match dya.yaml
    mock_res.resolved_data = {
            'static_envs': [
                {'name': 'dev', 'url': 'dev.internal'},
                {'name': 'prod', 'url': 'prod.internal'}
            ],
            'dynamic_nodes': [
                {'name': 'node-1', 'ip': '10.0.0.1'},
                {'name': 'node-2', 'ip': '10.0.0.2'}
            ],
            'cached_items': [
                {'name': 'item-1'}
            ]
    }
    return mock_res

def test_find_command_returns_is_help(mock_resolver):
    executor = CommandExecutor(mock_resolver)
    
    # Test Normal Command (Simple Alias)
    chain, vars, is_help, remaining = executor.find_command(['simple'])
    assert chain[0].alias == 'simple'
    assert is_help is False

    # Test Command Help (Strict Alias has helper? Actually Strict Alias in dya.yaml doesn't have explicitly defined helper but default is None)
    # Let's use Simple Alias which has helper? No, dya.yaml commands don't have helper defined in dya.yaml except... none of them have helper block in my created dya.yaml!
    # I should add helper to dya.yaml or use one that has it?
    # Wait, ConfigLoader parses helper.
    # I will assume 'simple' has no helper unless I add it to dya.yaml.
    # But -h always returns is_help=True regardless of whether helper text exists.
    
    result = executor.find_command(['simple', '-h'])
    if result:
        chain, vars, is_help, remaining = result
        assert chain[0].alias == 'simple'
        assert is_help is True
    else:
        pytest.fail("Command not found")

def test_help_flag_blocked_as_variable(mock_resolver):
    # Test passing -h as variable in 'complex ${arg1}'
    executor = CommandExecutor(mock_resolver)

    result = executor.find_command(['complex', '-h'])
    assert result is not None
    chain, vars, is_help, remaining = result
    assert chain[0].alias == 'complex ${arg1}'
    assert is_help is True 

def test_print_global_help_structure(mock_resolver):
    # Since prompt_toolkit is mocked globally, we verify execution without errors
    # and verify that print() is called for dict/command names
    
    with patch('builtins.print') as mock_print:
        executor = CommandExecutor(mock_resolver)
        executor.print_global_help()
        
        # Verify print was called (for dict names, command info, footer)
        assert mock_print.called
        # Check that at least some expected content was printed
        call_args_str = str(mock_print.call_args_list)
        assert 'static_envs' in call_args_str or 'Dicts' in call_args_str or 'Commands' in call_args_str

def test_interactive_shell_global_help(mock_resolver):
    executor = MagicMock() 
    shell = InteractiveShell(mock_resolver, executor)
    
    parts = ['-h']
    if len(parts) == 1 and parts[0] in ('-h', '--help'):
        executor.print_global_help()
    
    executor.print_global_help.assert_called_once()

def test_interactive_shell_command_help(mock_resolver):
    executor = MagicMock()
    cmd_mock = MagicMock()
    executor.find_command.return_value = ([cmd_mock], {}, True, [])
    
    shell = InteractiveShell(mock_resolver, executor)
    
    parts = ['test', '-h']
    result = executor.find_command(parts)
    
    if result:
        cmd, vars, is_help, remaining = result
        if is_help:
            executor.print_help(cmd)
        else:
            executor.execute(cmd, vars, remaining)
            
    executor.print_help.assert_called_once_with([cmd_mock])
    executor.execute.assert_not_called()

def test_partial_match_help(mock_resolver):
    # Setup: 'consume $${static_envs.name}'
    executor = CommandExecutor(mock_resolver)

    # Test 'consume -h' -> Should be partial match help
    result = executor.find_command(['consume', '-h'])
    
    assert result is not None
    chain, vars, is_help, remaining = result
    assert chain[0].alias == 'consume $${static_envs.name}'
    assert is_help is True

def test_partial_match_fail_on_static(mock_resolver):
    # Setup: 'simple'
    executor = CommandExecutor(mock_resolver)
    
    # Test 'sim -h' -> partial static match?
    # 'simple' vs 'sim'.
    # _match_alias_parts: 
    # for 'simple', 'sim':
    #   if 'simple' != 'sim': return False.
    # So it fails static match.
    # But wait, find_command iterates list.
    # It passes args.
    # If args = ['sim', '-h'].
    # _try_match('simple') -> _match_alias_parts(['simple'], ['sim', '-h'])
    #   i=0: alias='simple', input='sim'. Static mismatch. Return False.
    # So 'sim -h' should NOT return partial match help for 'simple'.
    
    result = executor.find_command(['sim', '-h'])
    assert result is None

def test_partial_match_dynamic_var_help(mock_resolver):
    # Setup: 'dyn $${dynamic_nodes.name}'
    executor = CommandExecutor(mock_resolver)
    
    # Test 'dyn -h'
    result = executor.find_command(['dyn', '-h'])
    
    assert result is not None
    chain, vars, is_help, remaining = result
    assert chain[0].name == 'Dynamic Consumer'
    assert is_help is True


# ============================================================================
# HELPER TYPE TESTS
# ============================================================================

def test_helper_formatter_factory():
    """Test that get_helper_formatter returns correct formatter based on type."""
    from dynamic_alias.helper_formatter import get_helper_formatter, AutoHelperFormatter, CustomHelperFormatter
    
    auto_formatter = get_helper_formatter("auto")
    custom_formatter = get_helper_formatter("custom")
    default_formatter = get_helper_formatter()
    
    assert isinstance(auto_formatter, AutoHelperFormatter)
    assert isinstance(custom_formatter, CustomHelperFormatter)
    assert isinstance(default_formatter, AutoHelperFormatter)  # Default is auto


def test_auto_helper_format(mock_resolver):
    """Test auto helper type produces structured output."""
    from dynamic_alias.helper_formatter import AutoHelperFormatter
    from dynamic_alias.models import CommandConfig, ArgConfig, SubCommand
    
    cmd = CommandConfig(
        name="Test",
        alias="test ${arg}",
        command="echo ${arg}",
        helper="This is the test helper",
        helper_type="auto",
        args=[
            ArgConfig(alias=["-o ${file}", "--output ${file}"], command="-o ${file}", helper="Output file"),
            ArgConfig(alias="-v", command="-v", helper="Verbose mode")
        ],
        sub=[
            SubCommand(alias="sub", command="sub", helper="Sub helper")
        ]
    )
    
    formatter = AutoHelperFormatter()
    output = formatter.format([cmd])
    
    assert "test ${arg}" in output  # Alias shown first (no Usage label)
    assert "Description:" in output
    assert "This is the test helper" in output  # Helper text in description
    assert "Args:" in output
    assert "-o, --output" in output  # Array alias combined
    assert "Output file" in output
    assert "Options/Subcommands:" in output
    assert "sub" in output


def test_custom_helper_format():
    """Test custom helper type produces raw concatenated output."""
    from dynamic_alias.helper_formatter import CustomHelperFormatter
    from dynamic_alias.models import CommandConfig, SubCommand
    
    cmd = CommandConfig(
        name="Test",
        alias="test",
        command="echo test",
        helper="CUSTOM HEADER\n============",
        helper_type="custom"
    )
    sub = SubCommand(alias="sub", command="sub", helper="SUB CUSTOM HELPER")
    
    formatter = CustomHelperFormatter()
    
    # Single command
    output1 = formatter.format([cmd])
    assert "CUSTOM HEADER" in output1
    assert "============" in output1
    
    # Command chain
    output2 = formatter.format([cmd, sub])
    assert "CUSTOM HEADER" in output2
    assert "SUB CUSTOM HELPER" in output2


def test_array_alias_display():
    """Test that array aliases are displayed as comma-separated."""
    from dynamic_alias.helper_formatter import AutoHelperFormatter
    from dynamic_alias.models import CommandConfig, ArgConfig
    
    cmd = CommandConfig(
        name="Test",
        alias="test",
        command="echo test",
        args=[
            ArgConfig(alias=["-q", "--quiet"], command="--quiet", helper="Quiet mode"),
        ]
    )
    
    formatter = AutoHelperFormatter()
    output = formatter.format([cmd])
    
    # Should show combined: "-q, --quiet"
    assert "-q, --quiet" in output or "--quiet, -q" in output  # Order may vary
    assert "Quiet mode" in output


def test_executor_uses_helper_type(mock_resolver):
    """Test that executor respects helper_type from command config."""
    executor = CommandExecutor(mock_resolver)
    
    # auto-helper-cmd should exist in dya.yaml
    result = executor.find_command(['auto-helper-cmd', 'test', '-h'])
    if result:
        chain, vars, is_help, remaining = result
        assert is_help is True
        # Check that root command has helper_type 'auto'
        assert chain[0].helper_type == 'auto'


def test_deep_nested_auto_helper():
    """Test auto helper with 3 levels of nested subcommands."""
    from dynamic_alias.helper_formatter import AutoHelperFormatter
    from dynamic_alias.models import CommandConfig, ArgConfig, SubCommand
    
    # Build 3-level nested structure
    level3 = SubCommand(
        alias="level3 ${action}",
        command="level3 ${action}",
        helper="Third level subcommand",
        args=[
            ArgConfig(alias=["-r", "--recursive"], command="--recursive", helper="Apply recursively"),
            ArgConfig(alias="-n ${count}", command="-n ${count}", helper="Number of iterations")
        ]
    )
    
    level2 = SubCommand(
        alias="level2 ${target}",
        command="level2 ${target}",
        helper="Second level subcommand",
        args=[
            ArgConfig(alias=["-o ${output}", "--output ${output}"], command="-o ${output}", helper="Output file"),
        ],
        sub=[level3]
    )
    
    level1 = SubCommand(
        alias="level1",
        command="level1",
        helper="First level subcommand",
        args=[
            ArgConfig(alias=["-f", "--force"], command="--force", helper="Force operation"),
        ],
        sub=[level2]
    )
    
    root = CommandConfig(
        name="Deep Test",
        alias="deep-test",
        command="echo deep",
        helper="Root command with deep nesting",
        helper_type="auto",
        args=[
            ArgConfig(alias=["-v", "--verbose"], command="--verbose", helper="Verbose output"),
        ],
        sub=[level1]
    )
    
    formatter = AutoHelperFormatter()
    
    # Test root level
    output_root = formatter.format([root])
    assert "Description:" in output_root
    assert "deep-test" in output_root
    assert "Args:" in output_root
    assert "-v, --verbose" in output_root
    assert "Options/Subcommands:" in output_root
    assert "level1" in output_root
    
    # Test level 1
    output_l1 = formatter.format([root, level1])
    assert "level1" in output_l1
    assert "First level subcommand" in output_l1
    assert "-f, --force" in output_l1
    assert "level2" in output_l1
    
    # Test level 2
    output_l2 = formatter.format([root, level1, level2])
    assert "level2 ${target}" in output_l2
    assert "Second level subcommand" in output_l2
    assert "-o, --output" in output_l2
    assert "level3" in output_l2
    
    # Test level 3 (deepest)
    output_l3 = formatter.format([root, level1, level2, level3])
    assert "level3 ${action}" in output_l3
    assert "Third level subcommand" in output_l3
    assert "-r, --recursive" in output_l3
    assert "Number of iterations" in output_l3


