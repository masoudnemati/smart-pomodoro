import json
from typing import Dict, Any, Optional
from utils.constants import DEFAULT_CONFIG


class ConfigManager:
    """Manages application configuration loading and saving"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
                
        except FileNotFoundError:
            print(f"{self.config_file} not found, using default values")
            return DEFAULT_CONFIG.copy()
        except json.JSONDecodeError as e:
            print(f"Error parsing {self.config_file}: {e}")
            return DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def update_position(self, x: int, y: int) -> None:
        """Update window position in config"""
        self.set('position.x', max(0, x))
        self.set('position.y', max(0, y))
        self.save_config()
    
    @property
    def work_duration(self) -> int:
        """Get work duration in seconds"""
        return self.get('work_time_minutes', 25) * 60
    
    @property
    def rest_duration(self) -> int:
        """Get rest duration in seconds"""
        return self.get('rest_time_minutes', 5) * 60
    
    @property
    def size(self) -> int:
        """Get window size"""
        return self.get('size', 60)
    
    @property
    def colors(self) -> Dict[str, str]:
        """Get color configuration"""
        return self.get('colors', DEFAULT_CONFIG['colors'])
    
    @property
    def position(self) -> Dict[str, Optional[int]]:
        """Get position configuration"""
        return self.get('position', {'x': None, 'y': None})
    
    @property
    def notification_sound(self) -> str:
        """Get notification sound filename"""
        return self.get('notification_sound', 'notification.mp3')