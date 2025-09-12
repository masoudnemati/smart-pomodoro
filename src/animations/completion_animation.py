"""
Completion Animation - Dizzy celebration effect
"""

import math
from .base_animation import BaseAnimation
from utils.constants import ANIMATION_CONSTANTS


class CompletionAnimation(BaseAnimation):
    """Dizzy celebration animation when work completes"""
    
    def __init__(self):
        config = ANIMATION_CONSTANTS['completion']
        super().__init__(config['update_rate'])
        
        self.duration = config['duration']
        self.max_scale = config['max_scale']
        self.rotation_cycles = config['rotation_cycles']
        self.morph_amplitude = config['morph_amplitude']
        self.start_time = 0
    
    def start(self) -> None:
        """Start completion animation with timer"""
        super().start()
        self.start_time = 0
    
    def update_animation(self) -> None:
        """Update dizzy celebration animation"""
        elapsed = self.frame * self.update_rate
        
        if elapsed >= self.duration:
            self.animation_finished.emit()
            self.stop()
            return
        
        # Progress through animation (0.0 to 1.0)
        progress = elapsed / self.duration
        
        # Phase 1: Rapid growth (0-20%)
        if progress < 0.2:
            phase_progress = progress / 0.2
            base_scale = 1.0 + (self.max_scale - 1.0) * phase_progress
        # Phase 2: Maximum wobble (20-70%)
        elif progress < 0.7:
            base_scale = self.max_scale
        # Phase 3: Return to normal (70-100%)
        else:
            phase_progress = (progress - 0.7) / 0.3
            base_scale = self.max_scale - (self.max_scale - 1.0) * phase_progress
        
        # Multiple wobble frequencies for dizzy effect
        wobble1 = 1.0 * math.sin(progress * math.pi * 18)
        wobble2 = 0.5 * math.sin(progress * math.pi * 28)
        wobble3 = 0.3 * math.sin(progress * math.pi * 40)
        
        # Rotation effect - multiple rotations with wobble
        self.rotation = (progress * 360 * self.rotation_cycles + 
                        180 * math.sin(progress * math.pi * 8))
        
        # Shape morphing between circle and oval
        self.shape_morph = self.morph_amplitude * math.sin(progress * math.pi * 12)
        
        # Scale with wobbles
        self.scale = base_scale + wobble1 + wobble2 + wobble3
        
        # Opacity pulsing with multiple frequencies
        opacity_pulse1 = 0.3 * math.sin(progress * math.pi * 15)
        opacity_pulse2 = 0.2 * math.sin(progress * math.pi * 25)
        self.opacity = 0.6 + opacity_pulse1 + opacity_pulse2
        
        # Ensure values stay in reasonable bounds
        self.scale = max(0.5, min(7.0, self.scale))
        self.opacity = max(0.3, min(1.0, self.opacity))
    
    def on_start(self) -> None:
        """Called when completion animation starts"""
        print("Starting completion animation (dizzy celebration)")
    
    def on_stop(self) -> None:
        """Called when completion animation stops"""
        print("Completion animation finished")