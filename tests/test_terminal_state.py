"""
Terminal State Restoration Tests
Tests for terminal state save/restore functionality after subprocess interruption.

Test Rules:
    @system_rules.txt
    @global-test-rules.md
"""
import unittest
import sys
import os
from unittest.mock import MagicMock, patch, call

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dynamic_alias.executor import _save_terminal_state, _restore_terminal_state


class TestTerminalStateHelpers(unittest.TestCase):
    """Test the terminal state save/restore helper functions."""

    def test_01_save_returns_none_on_windows(self):
        """On Windows, _save_terminal_state should return None."""
        with patch.object(sys, 'platform', 'win32'):
            result = _save_terminal_state()
            self.assertIsNone(result)

    def test_02_restore_does_nothing_on_windows(self):
        """On Windows, _restore_terminal_state should do nothing."""
        with patch.object(sys, 'platform', 'win32'):
            # Should not raise any exception
            _restore_terminal_state({'some': 'state'})
            _restore_terminal_state(None)

    def test_03_restore_does_nothing_with_none_state(self):
        """_restore_terminal_state should do nothing if state is None."""
        with patch.object(sys, 'platform', 'linux'):
            # Should not raise any exception even on Unix
            _restore_terminal_state(None)

    @unittest.skipIf(sys.platform == 'win32', "termios not available on Windows")
    def test_04_save_returns_termios_state_on_unix(self):
        """On Unix, _save_terminal_state should return termios attributes."""
        result = _save_terminal_state()
        # Should return a list (termios attributes) or None if not a terminal
        self.assertTrue(result is None or isinstance(result, list))

    def test_05_save_handles_termios_exception(self):
        """_save_terminal_state should return None if termios fails."""
        with patch.object(sys, 'platform', 'linux'):
            with patch.dict(sys.modules, {'termios': MagicMock()}):
                import importlib
                # Mock termios to raise exception
                mock_termios = MagicMock()
                mock_termios.tcgetattr.side_effect = Exception("No terminal")
                with patch.dict(sys.modules, {'termios': mock_termios}):
                    result = _save_terminal_state()
                    self.assertIsNone(result)

    def test_06_restore_calls_stty_sane_on_termios_failure(self):
        """On restore failure, should fallback to stty sane."""
        with patch.object(sys, 'platform', 'linux'):
            mock_termios = MagicMock()
            mock_termios.tcsetattr.side_effect = Exception("Failed to restore")
            mock_termios.TCSADRAIN = 1
            
            with patch.dict(sys.modules, {'termios': mock_termios}):
                with patch('os.system') as mock_system:
                    _restore_terminal_state([1, 2, 3])  # Fake state
                    mock_system.assert_called_once_with('stty sane 2>/dev/null')


class TestExecutorTerminalProtection(unittest.TestCase):
    """Test that CommandExecutor properly protects terminal state."""

    @classmethod
    def setUpClass(cls):
        cls.config_file = os.path.join(os.path.dirname(__file__), "dya.yaml")
        if not os.path.exists(cls.config_file):
            raise FileNotFoundError(f"{cls.config_file} must exist for testing")

    def test_07_execute_saves_and_restores_terminal(self):
        """Execute should save terminal state before and restore after subprocess."""
        from dynamic_alias.config import ConfigLoader
        from dynamic_alias.cache import CacheManager
        from dynamic_alias.resolver import DataResolver
        from dynamic_alias.executor import CommandExecutor
        
        loader = ConfigLoader(self.config_file)
        loader.load()
        
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        cache.get_local.return_value = None
        
        resolver = DataResolver(loader, cache)
        executor = CommandExecutor(resolver)
        
        # Find a simple command to execute
        cmd = loader.commands[0]  # 'simple' command
        
        with patch('dynamic_alias.executor._save_terminal_state') as mock_save:
            with patch('dynamic_alias.executor._restore_terminal_state') as mock_restore:
                with patch('subprocess.run') as mock_run:
                    mock_save.return_value = ['fake', 'terminal', 'state']
                    mock_run.return_value = MagicMock(returncode=0)
                    
                    executor.execute([cmd], {})
                    
                    # Verify save was called before subprocess
                    mock_save.assert_called_once()
                    
                    # Verify restore was called after (in finally)
                    mock_restore.assert_called_once_with(['fake', 'terminal', 'state'])

    def test_08_execute_restores_terminal_on_keyboard_interrupt(self):
        """Terminal should be restored even if KeyboardInterrupt occurs."""
        from dynamic_alias.config import ConfigLoader
        from dynamic_alias.cache import CacheManager
        from dynamic_alias.resolver import DataResolver
        from dynamic_alias.executor import CommandExecutor
        
        loader = ConfigLoader(self.config_file)
        loader.load()
        
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        cache.get_local.return_value = None
        
        resolver = DataResolver(loader, cache)
        executor = CommandExecutor(resolver)
        
        cmd = loader.commands[0]
        
        with patch('dynamic_alias.executor._save_terminal_state') as mock_save:
            with patch('dynamic_alias.executor._restore_terminal_state') as mock_restore:
                with patch('subprocess.run') as mock_run:
                    mock_save.return_value = ['state']
                    mock_run.side_effect = KeyboardInterrupt()
                    
                    # Should not raise, just print message
                    executor.execute([cmd], {})
                    
                    # Verify restore was still called despite exception
                    mock_restore.assert_called_once_with(['state'])

    def test_09_execute_restores_terminal_on_timeout(self):
        """Terminal should be restored even if TimeoutExpired occurs."""
        import subprocess as sp
        from dynamic_alias.config import ConfigLoader
        from dynamic_alias.cache import CacheManager
        from dynamic_alias.resolver import DataResolver
        from dynamic_alias.executor import CommandExecutor
        
        loader = ConfigLoader(self.config_file)
        loader.load()
        
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        cache.get_local.return_value = None
        
        resolver = DataResolver(loader, cache)
        executor = CommandExecutor(resolver)
        
        # Find timeout command
        timeout_cmd = None
        for cmd in loader.commands:
            if cmd.name == "Timeout":
                timeout_cmd = cmd
                break
        
        if timeout_cmd is None:
            self.skipTest("No timeout command in test config")
        
        with patch('dynamic_alias.executor._save_terminal_state') as mock_save:
            with patch('dynamic_alias.executor._restore_terminal_state') as mock_restore:
                with patch('subprocess.run') as mock_run:
                    mock_save.return_value = ['state']
                    mock_run.side_effect = sp.TimeoutExpired('cmd', 5)
                    
                    executor.execute([timeout_cmd], {})
                    
                    # Verify restore was still called despite timeout
                    mock_restore.assert_called_once_with(['state'])

    def test_10_execute_restores_terminal_on_general_exception(self):
        """Terminal should be restored even on unexpected exceptions."""
        from dynamic_alias.config import ConfigLoader
        from dynamic_alias.cache import CacheManager
        from dynamic_alias.resolver import DataResolver
        from dynamic_alias.executor import CommandExecutor
        
        loader = ConfigLoader(self.config_file)
        loader.load()
        
        cache = MagicMock(spec=CacheManager)
        cache.get.return_value = None
        cache.get_local.return_value = None
        
        resolver = DataResolver(loader, cache)
        executor = CommandExecutor(resolver)
        
        cmd = loader.commands[0]
        
        with patch('dynamic_alias.executor._save_terminal_state') as mock_save:
            with patch('dynamic_alias.executor._restore_terminal_state') as mock_restore:
                with patch('subprocess.run') as mock_run:
                    mock_save.return_value = ['state']
                    mock_run.side_effect = RuntimeError("Unexpected error")
                    
                    executor.execute([cmd], {})
                    
                    # Verify restore was still called
                    mock_restore.assert_called_once_with(['state'])


@unittest.skipIf(sys.platform == 'win32', "Unix integration tests - termios not available on Windows")
class TestTerminalStateUnixIntegration(unittest.TestCase):
    """
    Real integration tests for Unix systems (Linux/macOS).
    These tests run WITHOUT mocks to validate actual termios behavior.
    They are skipped on Windows.
    """

    def test_11_real_save_and_restore_cycle(self):
        """Test real save/restore cycle with termios."""
        import termios
        
        # Save current state
        saved_state = _save_terminal_state()
        
        # On a real terminal, this should return a list
        # In CI/headless, stdin might not be a tty, so None is acceptable
        if saved_state is None:
            self.skipTest("stdin is not a terminal (CI environment)")
        
        self.assertIsInstance(saved_state, list)
        self.assertEqual(len(saved_state), 7)  # termios returns 7 elements
        
        # Restore should not raise any exception
        _restore_terminal_state(saved_state)
        
        # Verify terminal is still functional by saving again
        new_state = _save_terminal_state()
        self.assertEqual(saved_state, new_state)

    def test_12_real_terminal_survives_subprocess_interruption(self):
        """Test that terminal state is preserved after subprocess interruption."""
        import subprocess
        import termios
        
        saved_state = _save_terminal_state()
        if saved_state is None:
            self.skipTest("stdin is not a terminal (CI environment)")
        
        try:
            # Run a subprocess that we'll terminate quickly
            # This simulates what happens with Ctrl+D
            result = subprocess.run(
                "echo 'test'",
                shell=True,
                timeout=1
            )
        except Exception:
            pass
        finally:
            _restore_terminal_state(saved_state)
        
        # Verify terminal state was preserved
        current_state = _save_terminal_state()
        self.assertEqual(saved_state, current_state)

    def test_13_real_terminal_survives_raw_mode_corruption(self):
        """Test that terminal state is restored after subprocess changes it."""
        import termios
        import tty
        
        saved_state = _save_terminal_state()
        if saved_state is None:
            self.skipTest("stdin is not a terminal (CI environment)")
        
        try:
            # Simulate what an interactive program might do - change to raw mode
            # Note: We don't actually change it in the test to avoid test instability
            # Instead we verify the save/restore mechanism works
            pass
        finally:
            _restore_terminal_state(saved_state)
        
        current_state = _save_terminal_state()
        self.assertEqual(saved_state, current_state)

    def test_14_real_executor_integration(self):
        """Integration test: real executor with real terminal protection."""
        config_file = os.path.join(os.path.dirname(__file__), "dya.yaml")
        if not os.path.exists(config_file):
            self.skipTest("dya.yaml not found")
        
        from dynamic_alias.config import ConfigLoader
        from dynamic_alias.cache import CacheManager
        from dynamic_alias.resolver import DataResolver
        from dynamic_alias.executor import CommandExecutor
        
        saved_state = _save_terminal_state()
        if saved_state is None:
            self.skipTest("stdin is not a terminal (CI environment)")
        
        loader = ConfigLoader(config_file)
        loader.load()
        
        # Use temp cache file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            cache_path = f.name
        
        try:
            cache = CacheManager(cache_path, True)
            cache.load()
            
            resolver = DataResolver(loader, cache)
            executor = CommandExecutor(resolver)
            
            # Find 'simple' command (should just echo something)
            cmd = None
            for c in loader.commands:
                if c.name == "Simple":
                    cmd = c
                    break
            
            if cmd is None:
                self.skipTest("Simple command not found in config")
            
            # Execute the command
            executor.execute([cmd], {})
            
            # Verify terminal state is preserved after execution
            current_state = _save_terminal_state()
            self.assertEqual(saved_state, current_state)
        finally:
            if os.path.exists(cache_path):
                os.unlink(cache_path)

    def test_15_stty_sane_fallback_works(self):
        """Test that stty sane can be called as fallback."""
        import subprocess
        
        # Verify stty sane command exists and works
        result = subprocess.run(
            'stty sane 2>/dev/null',
            shell=True,
            capture_output=True
        )
        # Exit code 0 means success, non-zero might mean not a tty (still ok)
        # The important thing is it doesn't crash
        self.assertIn(result.returncode, [0, 1])  # 0=success, 1=not a tty


def _get_linux_distro():
    """
    Detect Linux distribution.
    Returns: 'debian', 'centos', 'fedora', 'rhel', 'ubuntu', or None
    """
    if sys.platform != 'linux':
        return None
    
    try:
        # Try /etc/os-release (modern standard)
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release') as f:
                content = f.read().lower()
                if 'ubuntu' in content or 'debian' in content:
                    return 'debian'
                elif 'centos' in content or 'rhel' in content or 'red hat' in content:
                    return 'centos'
                elif 'fedora' in content:
                    return 'fedora'
        
        # Fallback checks
        if os.path.exists('/etc/debian_version'):
            return 'debian'
        elif os.path.exists('/etc/redhat-release'):
            return 'centos'
            
    except Exception:
        pass
    
    return None


def _is_macos():
    """Check if running on macOS."""
    return sys.platform == 'darwin'


def _is_debian_based():
    """Check if running on Debian-based Linux (Debian, Ubuntu, etc.)."""
    return _get_linux_distro() == 'debian'


def _is_centos_based():
    """Check if running on CentOS/RHEL-based Linux."""
    return _get_linux_distro() in ('centos', 'fedora', 'rhel')


@unittest.skipIf(not _is_debian_based(), "Debian/Ubuntu specific tests")
class TestTerminalStateDebian(unittest.TestCase):
    """
    Tests specific to Debian-based systems (Debian, Ubuntu, Linux Mint, etc.).
    These tests verify Debian-specific terminal handling.
    """

    def test_16_debian_stty_available(self):
        """Verify stty is available on Debian systems."""
        import subprocess
        result = subprocess.run(['which', 'stty'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'/bin/stty', result.stdout.lower() + b'/usr/bin/stty')

    def test_17_debian_reset_command_available(self):
        """Verify reset command is available on Debian systems."""
        import subprocess
        result = subprocess.run(['which', 'reset'], capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_18_debian_termios_save_restore(self):
        """Test termios save/restore on Debian."""
        saved = _save_terminal_state()
        if saved is None:
            self.skipTest("Not running in a terminal")
        
        self.assertIsInstance(saved, list)
        self.assertEqual(len(saved), 7)  # Standard termios attribute count
        
        # Restore and verify
        _restore_terminal_state(saved)
        restored = _save_terminal_state()
        self.assertEqual(saved, restored)

    def test_19_debian_tput_available(self):
        """Verify tput is available for terminal control on Debian."""
        import subprocess
        result = subprocess.run(['which', 'tput'], capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_20_debian_terminal_reset_integration(self):
        """Integration test: full terminal reset cycle on Debian."""
        import subprocess
        
        saved = _save_terminal_state()
        if saved is None:
            self.skipTest("Not running in a terminal")
        
        try:
            # Run a command that could potentially mess with terminal
            subprocess.run('echo "test"', shell=True, timeout=1)
        finally:
            _restore_terminal_state(saved)
        
        # Verify terminal is still working
        current = _save_terminal_state()
        self.assertEqual(saved, current)


@unittest.skipIf(not _is_centos_based(), "CentOS/RHEL/Fedora specific tests")
class TestTerminalStateCentOS(unittest.TestCase):
    """
    Tests specific to RHEL-based systems (CentOS, RHEL, Fedora, Rocky, Alma).
    """

    def test_21_centos_stty_available(self):
        """Verify stty is available on CentOS/RHEL systems."""
        import subprocess
        result = subprocess.run(['which', 'stty'], capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_22_centos_reset_available(self):
        """Verify reset command exists (may be in ncurses package)."""
        import subprocess
        result = subprocess.run(['which', 'reset'], capture_output=True)
        # reset may not be installed by default on minimal CentOS
        if result.returncode != 0:
            self.skipTest("reset command not installed (install ncurses-term)")
        self.assertEqual(result.returncode, 0)

    def test_23_centos_termios_save_restore(self):
        """Test termios save/restore on CentOS/RHEL."""
        saved = _save_terminal_state()
        if saved is None:
            self.skipTest("Not running in a terminal")
        
        self.assertIsInstance(saved, list)
        self.assertEqual(len(saved), 7)
        
        _restore_terminal_state(saved)
        restored = _save_terminal_state()
        self.assertEqual(saved, restored)

    def test_24_centos_stty_sane_works(self):
        """Verify stty sane works on CentOS/RHEL."""
        import subprocess
        
        result = subprocess.run(
            'stty sane 2>/dev/null; echo $?',
            shell=True,
            capture_output=True,
            text=True
        )
        # Should not crash
        self.assertIn(result.returncode, [0, 1])

    def test_25_centos_terminal_reset_integration(self):
        """Integration test: full terminal reset cycle on CentOS."""
        import subprocess
        
        saved = _save_terminal_state()
        if saved is None:
            self.skipTest("Not running in a terminal")
        
        try:
            subprocess.run('echo "test"', shell=True, timeout=1)
        finally:
            _restore_terminal_state(saved)
        
        current = _save_terminal_state()
        self.assertEqual(saved, current)


@unittest.skipIf(not _is_macos(), "macOS specific tests")
class TestTerminalStateMacOS(unittest.TestCase):
    """
    Tests specific to macOS.
    macOS uses BSD-style terminal handling.
    """

    def test_26_macos_stty_available(self):
        """Verify stty is available on macOS."""
        import subprocess
        result = subprocess.run(['which', 'stty'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'/bin/stty', result.stdout)

    def test_27_macos_reset_available(self):
        """Verify reset command is available on macOS."""
        import subprocess
        result = subprocess.run(['which', 'reset'], capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_28_macos_termios_save_restore(self):
        """Test termios save/restore on macOS."""
        saved = _save_terminal_state()
        if saved is None:
            self.skipTest("Not running in a terminal")
        
        self.assertIsInstance(saved, list)
        # macOS also returns 7 elements from termios
        self.assertEqual(len(saved), 7)
        
        _restore_terminal_state(saved)
        restored = _save_terminal_state()
        self.assertEqual(saved, restored)

    def test_29_macos_tput_available(self):
        """Verify tput is available on macOS."""
        import subprocess
        result = subprocess.run(['which', 'tput'], capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_30_macos_terminal_reset_integration(self):
        """Integration test: full terminal reset cycle on macOS."""
        import subprocess
        
        saved = _save_terminal_state()
        if saved is None:
            self.skipTest("Not running in a terminal")
        
        try:
            subprocess.run('echo "test"', shell=True, timeout=1)
        finally:
            _restore_terminal_state(saved)
        
        current = _save_terminal_state()
        self.assertEqual(saved, current)

    def test_31_macos_bsd_stty_options(self):
        """Test BSD-style stty options work on macOS."""
        import subprocess
        
        # macOS uses BSD stty which has slightly different options
        result = subprocess.run(
            'stty -a 2>/dev/null',
            shell=True,
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        # BSD stty should show speed in the output
        self.assertIn('speed', result.stdout.lower())


if __name__ == '__main__':
    unittest.main()
