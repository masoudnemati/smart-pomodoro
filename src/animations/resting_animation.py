import math
from .base_animation import BaseAnimation
from utils.constants import ANIMATION_CONSTANTS


class RestingAnimation(BaseAnimation):
    """Fast pulse animation for resting phase"""
    
    def __init__(self):
        config = ANIMATION_CONSTANTS['resting']
        super().__init__(config['update_rate'])
        
        self.scale_amplitude = config['scale_amplitude']
        self.opacity_base = config['opacity_base']
        self.opacity_amplitude = config['opacity_amplitude']
        self.cycle_speed = config['cycle_speed']
    
    def update_animation(self) -> None:
        """Update pulse animation"""
        # Fast pulse cycle (1 second cycle)
        cycle = (self.frame * (self.update_rate / 1000.0)) % (2 * math.pi)
        cycle_adjusted = cycle * self.cycle_speed
        
        # Pulse scale effect
        self.scale = 1.0 + self.scale_amplitude * math.sin(cycle_adjusted)
        
        # Pulse opacity effect
        self.opacity = self.opacity_base + self.opacity_amplitude * math.sin(cycle_adjusted)
        
        # Ensure values stay in bounds
        self.scale = max(0.5, min(2.0, self.scale))
        self.opacity = max(0.1, min(1.0, self.opacity))
    
    def on_start(self) -> None:
        """Called when resting animation starts"""
        print("Starting resting animation (pulse effect)")
    
    def on_stop(self) -> None:
        """Called when resting animation stops"""
        print("Stopping resting animation")