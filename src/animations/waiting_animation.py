import math
from .base_animation import BaseAnimation
from utils.constants import ANIMATION_CONSTANTS


class WaitingAnimation(BaseAnimation):
    """Slow breathing animation for waiting phase"""
    
    def __init__(self):
        config = ANIMATION_CONSTANTS['waiting']
        super().__init__(config['update_rate'])
        
        self.scale_amplitude = config['scale_amplitude']
        self.opacity_base = config['opacity_base']
        self.opacity_amplitude = config['opacity_amplitude']
        self.cycle_speed = config['cycle_speed']
    
    def update_animation(self) -> None:
        """Update breathing animation"""
        # Slow breathing cycle (3 second cycle)
        cycle = (self.frame * (self.update_rate / 1000.0)) % (2 * math.pi)
        cycle_adjusted = cycle * self.cycle_speed
        
        # Breathing scale effect
        self.scale = 1.0 + self.scale_amplitude * math.sin(cycle_adjusted)
        
        # Breathing opacity effect
        self.opacity = self.opacity_base + self.opacity_amplitude * math.sin(cycle_adjusted)
        
        # Ensure values stay in bounds
        self.scale = max(0.5, min(2.0, self.scale))
        self.opacity = max(0.1, min(1.0, self.opacity))
    
    def on_start(self) -> None:
        """Called when waiting animation starts"""
        print("Starting waiting animation (breathing effect)")
    
    def on_stop(self) -> None:
        """Called when waiting animation stops"""
        print("Stopping waiting animation")