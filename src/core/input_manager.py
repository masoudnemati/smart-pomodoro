from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from pynput import mouse, keyboard
import threading
import time
from utils.constants import Phase


class InputManager(QObject):
    """Manages mouse and keyboard input detection"""
    
    # Signals
    activity_detected = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.mouse_listener = None
        self.keyboard_listener = None
        self.is_active = False
        self.ignore_next_input = False
        self.last_activity_time = 0
        self.activity_cooldown = 1.0  # 1 second cooldown between detections
    
    def start_listening(self) -> None:
        """Start mouse and keyboard listeners"""
        if not self.is_active:
            self.is_active = True
            self.ignore_next_input = False
            print("Starting input listeners...")
            
            # Use a timer to start listeners to avoid blocking the main thread
            QTimer.singleShot(100, self._create_listeners)
    
    def stop_listening(self) -> None:
        """Stop mouse and keyboard listeners"""
        if self.is_active:
            self._stop_listeners()
            self.is_active = False
            print("Input listeners stopped")
    
    def set_ignore_input(self, ignore: bool) -> None:
        """Set flag to ignore input (used during dragging)"""
        self.ignore_next_input = ignore
    
    def _create_listeners(self) -> None:
        """Create mouse and keyboard listeners"""
        try:
            def on_input(*args):
                current_time = time.time()
                if (not self.ignore_next_input and 
                    current_time - self.last_activity_time > self.activity_cooldown):
                    self.last_activity_time = current_time
                    print(f"Activity detected! {args[0] if args else 'Unknown event'}")
                    self.activity_detected.emit()
            
            # Mouse listener
            self.mouse_listener = mouse.Listener(
                on_move=on_input,
                on_click=on_input,
                on_scroll=on_input
            )
            self.mouse_listener.start()
            
            # Keyboard listener
            self.keyboard_listener = keyboard.Listener(
                on_press=on_input,
                on_release=on_input
            )
            self.keyboard_listener.start()
            
            print("Input listeners started successfully")
            
        except Exception as e:
            print(f"Error starting input listeners: {e}")
            self.is_active = False
    
    def _stop_listeners(self) -> None:
        """Stop all listeners"""
        try:
            if self.mouse_listener and self.mouse_listener.is_alive():
                self.mouse_listener.stop()
            
            if self.keyboard_listener and self.keyboard_listener.is_alive():
                self.keyboard_listener.stop()
                
            self.mouse_listener = None
            self.keyboard_listener = None
            
        except Exception as e:
            print(f"Error stopping listeners: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        self.stop_listening()