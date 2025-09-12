import math
from abc import ABC, abstractmethod
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

# Create a compatible metaclass that combines both QObject and ABC metaclasses
class QABCMeta(type(QObject), type(ABC)):
    pass

class BaseAnimation(QObject, ABC, metaclass=QABCMeta):
    """Abstract base class for animations"""
    
    # Signals
    animation_updated = pyqtSignal(dict)  # Dict with animation properties
    animation_finished = pyqtSignal()
    
    def __init__(self, update_rate: int = 50):
        super().__init__()
        self.update_rate = update_rate
        self.frame = 0
        self.is_active = False
        
        # Animation properties
        self.scale = 1.0
        self.opacity = 1.0
        self.rotation = 0.0
        self.shape_morph = 0.0
        
        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
    
    def start(self) -> None:
        """Start the animation"""
        if not self.is_active:
            self.is_active = True
            self.frame = 0
            self.timer.start(self.update_rate)
            self.on_start()
    
    def stop(self) -> None:
        """Stop the animation"""
        if self.is_active:
            self.is_active = False
            self.timer.stop()
            self.reset_properties()
            self.on_stop()
    
    def pause(self) -> None:
        """Pause the animation"""
        if self.is_active:
            self.timer.stop()
    
    def resume(self) -> None:
        """Resume the animation"""
        if self.is_active:
            self.timer.start(self.update_rate)
    
    def reset_properties(self) -> None:
        """Reset animation properties to defaults"""
        self.scale = 1.0
        self.opacity = 1.0
        self.rotation = 0.0
        self.shape_morph = 0.0
    
    def get_properties(self) -> dict:
        """Get current animation properties"""
        return {
            'scale': self.scale,
            'opacity': self.opacity,
            'rotation': self.rotation,
            'shape_morph': self.shape_morph
        }
    
    def _update_frame(self) -> None:
        """Update animation frame (called by timer)"""
        if self.is_active:
            self.frame += 1
            self.update_animation()
            self.animation_updated.emit(self.get_properties())
    
    @abstractmethod
    def update_animation(self) -> None:
        """Update animation properties - to be implemented by subclasses"""
        pass
    
    def on_start(self) -> None:
        """Called when animation starts - can be overridden"""
        pass
    
    def on_stop(self) -> None:
        """Called when animation stops - can be overridden"""
        pass
    
    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        """Sine easing function"""
        return -(math.cos(math.pi * t) - 1) / 2
    
    @staticmethod
    def ease_bounce(t: float) -> float:
        """Bounce easing function"""
        if t < 1/2.75:
            return 7.5625 * t * t
        elif t < 2/2.75:
            return 7.5625 * (t - 1.5/2.75) * (t - 1.5/2.75) + 0.75
        elif t < 2.5/2.75:
            return 7.5625 * (t - 2.25/2.75) * (t - 2.25/2.75) + 0.9375
        else:
            return 7.5625 * (t - 2.625/2.75) * (t - 2.625/2.75) + 0.984375
    
    def cleanup(self) -> None:
        """Clean up resources"""
        self.stop()