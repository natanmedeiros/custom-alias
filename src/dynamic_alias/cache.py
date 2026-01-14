import os
import json
from typing import Dict, List, Any, Optional

class CacheManager:
    def __init__(self, cache_file: str, enabled: bool):
        self.cache_file = cache_file
        self.enabled = enabled
        self.cache: Dict[str, List[Dict[str, Any]]] = {}

    def load(self):
        if not self.enabled:
            return
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}")

    def save(self):
        if not self.enabled:
            return
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")

    def get(self, key: str, ttl: int = 300) -> Optional[List[Dict[str, Any]]]:
        if not self.enabled:
            return None
        
        entry = self.cache.get(key)
        if not entry or not isinstance(entry, dict):
            # Backward compatibility or empty
            return None
            
        timestamp = entry.get('timestamp', 0)
        data = entry.get('data')
        
        if data is None:
            return None
            
        import time
        current_time = int(time.time())
        if current_time - timestamp > ttl:
            return None # Expired
            
        return data

    def set(self, key: str, value: List[Dict[str, Any]]):
        if self.enabled:
            import time
            self.cache[key] = {
                'timestamp': int(time.time()),
                'data': value
            }

    def add_history(self, command: str, limit: int = 20):
        if not self.enabled:
            return

        if '_history' not in self.cache:
            self.cache['_history'] = []
            
        history = self.cache['_history']
        
        # Rule 1.2.20: Append and shift
        # Only add if distinct from last command ?? Rules don't specify uniqueness, but standard shell usually does.
        # Rules say: "appended and shifted only if exceeds history-size"
        
        history.append(command)
        
        if len(history) > limit:
            history[:] = history[-limit:]
            
        self.cache['_history'] = history
        
    def get_history(self) -> List[str]:
        if not self.enabled:
            return []
        return self.cache.get('_history', [])
    
    def clear_cache(self) -> int:
        """
        Rule 1.2.21: Purge cache entries that do not start with underscore "_".
        Returns number of entries purged.
        """
        if not self.enabled:
            return 0
        
        keys_to_remove = [k for k in self.cache.keys() if not k.startswith('_')]
        count = len(keys_to_remove)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        self.save()
        return count
    
    def clear_history(self) -> bool:
        """
        Rule 1.2.23: Purge cache _history entry.
        Returns True if history was removed.
        """
        if not self.enabled:
            return False
        
        if '_history' in self.cache:
            del self.cache['_history']
            self.save()
            return True
        return False
    
    def delete_all(self) -> bool:
        """
        Rule 1.2.24: Delete the entire cache file.
        Returns True if file was deleted.
        """
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            self.cache = {}
            return True
        return False
    
    def purge_expired(self, ttl_map: Dict[str, int] = None) -> int:
        """
        Rule 1.2.22: Purge expired cache entries.
        ttl_map is a dict mapping cache key names to their TTL.
        Returns number of entries purged.
        """
        if not self.enabled or ttl_map is None:
            return 0
        
        import time
        current_time = int(time.time())
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            if key.startswith('_'):
                continue  # Skip internal entries like _history
            
            if not isinstance(entry, dict):
                continue
            
            timestamp = entry.get('timestamp', 0)
            ttl = ttl_map.get(key, 300)  # Default 5 min TTL
            
            if current_time - timestamp > ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        if keys_to_remove:
            self.save()
        
        return len(keys_to_remove)

