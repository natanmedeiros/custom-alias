import re
import os
from typing import List, Dict, Any, Callable, Optional, Tuple, Set
from .constants import REGEX_APP_VAR, REGEX_USER_VAR

class VariableResolver:
    """Helper class for variable substitution (DRY compliance)."""
    
    @staticmethod
    def extract_app_vars(text: str) -> Set[Tuple[str, str]]:
        """Extract all $${source.key} references."""
        if not isinstance(text, str):
            return set()
        return set(re.findall(REGEX_APP_VAR, text))

    @staticmethod
    def resolve_app_vars(text: str, resolver_func: Callable[[str], List[Dict]], 
                         context_vars: Dict[str, Any] = None, use_local_cache: Callable[[str], Any] = None) -> str:
        """
        Replace $${source.key} in text specific resolver logic.
        
        Args:
            text: The text string to process
            resolver_func: Callback(source_name) -> List[Dict] (returns data list or empty list)
            context_vars: Optional dict of variables already resolved context (e.g. from alias match)
            use_local_cache: Optional callback(key) -> value for resolving $${locals.key}
        """
        if context_vars is None:
            context_vars = {}

        def replace(match):
            source = match.group(1)
            key = match.group(2)
            
            # 1. Handle locals (priority 1) - Rule 1.2.25
            if source == 'locals' and use_local_cache:
                val = use_local_cache(key)
                if val is not None:
                    return str(val)
                return match.group(0)

            # 2. Handle context vars (priority 2) - List Mode
            # If source is in context, use the specific item matched previously
            if source in context_vars:
                item = context_vars[source]
                if isinstance(item, dict):
                    return str(item.get(key, match.group(0)))
            
            # 3. Handle lazy resolution (priority 3) - Direct Mode
            # Resolve source on demand and use first item
            data_list = resolver_func(source)
            if data_list:
                # Direct mode: always access first item
                return str(data_list[0].get(key, match.group(0)))
                
            return match.group(0)
            
        return re.sub(REGEX_APP_VAR, replace, text)

    @staticmethod
    def resolve_user_vars(text: str, variables: Dict[str, str]) -> str:
        """Replace ${var} with values from variables dict."""
        def replace(match):
            key = match.group(1)
            if key in variables and isinstance(variables[key], str):
                return variables[key]
            return match.group(0)
        
        return re.sub(REGEX_USER_VAR, replace, text)

    @staticmethod
    def parse_app_var(text: str) -> Optional[Tuple[str, str]]:
        """Check if text is $${source.key} and return (source, key)."""
        match = re.fullmatch(REGEX_APP_VAR, text)
        if match:
            return match.group(1), match.group(2)
        return None

    @staticmethod
    def parse_user_var(text: str) -> Optional[str]:
        """Check if text is ${var} and return var_name."""
        match = re.fullmatch(REGEX_USER_VAR, text)
        if match:
            return match.group(1)
        return None


def resolve_path(options: List[str], default: str) -> str:
    """Resolve path from options, checking existence, fallback to default."""
    return next((p for p in map(os.path.expanduser, options) 
                if os.path.exists(p)), os.path.expanduser(default))
