import subprocess
import json
from typing import Dict, List, Any
from .models import DynamicDictConfig
from .config import ConfigLoader
from .cache import CacheManager
from .utils import VariableResolver

class DataResolver:
    def __init__(self, config: ConfigLoader, cache: CacheManager):
        self.config = config
        self.cache = cache
        self.resolved_data: Dict[str, List[Dict[str, Any]]] = {}
        self.verbose_log_buffer: List[str] = []  # Buffer for verbose logs during interactive mode
        self._resolution_stack: set = set()  # Track currently resolving dicts for circular reference detection
    
    def add_verbose_log(self, message: str):
        """Add a verbose log message to the buffer (for interactive mode)."""
        if self.config.global_config.verbose:
            self.verbose_log_buffer.append(message)
    
    def flush_verbose_logs(self):
        """Print and clear all buffered verbose logs."""
        for msg in self.verbose_log_buffer:
            print(msg)
        self.verbose_log_buffer.clear()

    def resolve_all(self):
        """Resolve all dicts and dynamic_dicts at once (for non-interactive mode)."""
        for name, d in self.config.dicts.items():
            self.resolved_data[name] = d.data
        
        for name, dd in self.config.dynamic_dicts.items():
            data = self.cache.get(name, ttl=dd.cache_ttl)
            if data is None:
                data = self._execute_dynamic_source(dd)
                self.cache.set(name, data)
            self.resolved_data[name] = data

    def resolve_one(self, name: str) -> List[Dict[str, Any]]:
        """
        Resolve a single dict/dynamic_dict on-demand (lazy loading).
        Uses cache if available, otherwise executes command and caches result.
        """
        verbose = self.config.global_config.verbose
        
        # Already resolved - return result from memory (no verbose log - too noisy during autocomplete)
        if name in self.resolved_data:
            return self.resolved_data[name]
        
        # Check static dicts first (no circular reference risk)
        if name in self.config.dicts:
            self.resolved_data[name] = self.config.dicts[name].data
            return self.resolved_data[name]
        
        # Check dynamic dicts
        if name in self.config.dynamic_dicts:
            # Circular reference detection
            if name in self._resolution_stack:
                chain = ' -> '.join(self._resolution_stack) + f' -> {name}'
                print(f"Warning: Circular reference detected in dynamic dict resolution: {chain}")
                return []
            
            # Add to resolution stack
            self._resolution_stack.add(name)
            
            try:
                dd = self.config.dynamic_dicts[name]
                data = self.cache.get(name, ttl=dd.cache_ttl)
                if data is None:
                    import time
                    start_time = time.time()
                    data = self._execute_dynamic_source(dd)
                    elapsed = time.time() - start_time
                    if verbose:
                        self.add_verbose_log(f"[VERBOSE] Executed dynamic_dict '{name}' in {elapsed:.2f}s")
                    
                    # Warning log for null/empty results
                    if data is None:
                        print(f"Warning: dynamic_dict '{name}' returned null")
                        print(f"  Action: Executed command for dynamic resolution")
                        print(f"  Command: {dd.command[:100]}{'...' if len(dd.command) > 100 else ''}")
                        data = []
                    elif len(data) == 0:
                        print(f"Warning: dynamic_dict '{name}' returned empty list")
                        print(f"  Action: Executed command for dynamic resolution")
                        print(f"  Command: {dd.command[:100]}{'...' if len(dd.command) > 100 else ''}")
                    
                    self.cache.set(name, data)
                    self.cache.save()
                else:
                    # Warning log for cached empty results
                    if len(data) == 0:
                        print(f"Warning: dynamic_dict '{name}' has empty cached data")
                        print(f"  Suggestion: Run --dya-clear-cache to refresh")
                    if verbose:
                        self.add_verbose_log(f"[VERBOSE] Loaded dynamic_dict '{name}' from cache")
                self.resolved_data[name] = data
                return self.resolved_data[name]
            finally:
                # Remove from resolution stack
                self._resolution_stack.discard(name)
        
        # Warning for undefined source
        print(f"Warning: Source '{name}' not found in dicts or dynamic_dicts")
        print(f"  Action: Attempted to resolve data source")
        print(f"  Available dicts: {list(self.config.dicts.keys())}")
        print(f"  Available dynamic_dicts: {list(self.config.dynamic_dicts.keys())}")
        return []

    def _execute_dynamic_source(self, dd: DynamicDictConfig) -> List[Dict[str, Any]]:
        try:
            # Refactored to use VariableResolver (DRY)
            # Replaces substitution logic with centralized utility
            # Behavior preserved: resolver.py only supports "Direct Mode" (lazy resolution)
            cmd = VariableResolver.resolve_app_vars(
                dd.command, 
                resolver_func=self.resolve_one
            )
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=dd.timeout)
            if result.returncode != 0:
                print(f"Error executing dynamic dict '{dd.name}': {result.stderr}")
                return []

            # Validate JSON output
            stdout = result.stdout.strip()
            if not stdout:
                print(f"Error in dynamic dict '{dd.name}': Command produced no output")
                print(f"  Command: {cmd[:100]}{'...' if len(cmd) > 100 else ''}")
                print(f"  Expected: Valid JSON array or object")
                return []
            
            try:
                raw_json = json.loads(stdout)
            except json.JSONDecodeError as json_err:
                print(f"Error in dynamic dict '{dd.name}': Invalid JSON output")
                print(f"  Command: {cmd[:100]}{'...' if len(cmd) > 100 else ''}")
                print(f"  JSON Error: {json_err.msg} at position {json_err.pos}")
                # Show first 200 chars of output for debugging
                preview = stdout[:200]
                if len(stdout) > 200:
                    preview += "..."
                print(f"  Output: {preview}")
                return []
            
            mapped_data = []
            target_list = raw_json
            if isinstance(raw_json, dict):
                 pass # Heuristic handling
            
            if not isinstance(target_list, list):
                target_list = [target_list]

            for item in target_list:
                new_item = {}
                for internal_key, json_key in dd.mapping.items():
                    if json_key in item:
                        new_item[internal_key] = item[json_key]
                if new_item:
                    mapped_data.append(new_item)
            return mapped_data

        except subprocess.TimeoutExpired:
            print(f"Error in dynamic dict '{dd.name}': Command timed out after {dd.timeout}s")
            return []
        except Exception as e:
            print(f"Error in dynamic dict '{dd.name}': {e}")
            return []
