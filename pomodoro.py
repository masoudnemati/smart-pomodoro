from PyQt5.QtWidgets import QApplication, QWidget, QDesktopWidget, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
import sys
import json
import math
import os
from pynput import mouse, keyboard

class CircleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Load configuration first
        self.load_config()
        
        # Set window size from config
        self.setFixedSize(self.size, self.size)
        
        # Set window position from config
        if self.position_x is not None and self.position_y is not None:
            self.move(max(0, self.position_x), max(0, self.position_y))
        
        # Phase states: 'waiting', 'working', 'resting'
        self.phase = 'waiting'
        self.progress = 1.0  # Start full for waiting phase
        self.elapsed = 0
        self.is_paused = False  # Add pause state
        self.paused_time = 0
        self.is_locked = False  # Add lock state

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)  # update every second

        # Input listeners (only active during waiting phase)
        self.mouse_listener = None
        self.keyboard_listener = None
        self.start_listeners()
        
        # Drag and drop functionality (immediate)
        self.drag_start_position = QPoint()
        self.is_dragging = False

        # Animation properties
        self._animation_scale = 1.0
        self._animation_opacity = 1.0
        self._animation_rotation = 0.0
        self._shape_morph = 0.0
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_frame = 0
        
        # Screen completion animation functionality
        self.completion_animation_timer = None
        self.completion_frame = 0

        # Audio player for notification sound
        self.media_player = QMediaPlayer()

        self.start_waiting_animation()

    def load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                
                # Time settings
                self.work_duration = config.get('work_time_minutes', 25) * 60
                self.rest_duration = config.get('rest_time_minutes', 5) * 60
                
                # Size setting
                self.size = config.get('size', 60)
                
                # Color settings
                colors = config.get('colors', {})
                self.color_background = colors.get('background', 'rgba(50, 50, 50, 100)')
                self.color_working = colors.get('working', 'green')
                self.color_resting = colors.get('resting', 'yellow')
                self.color_waiting = colors.get('waiting', 'blue')
                
                # Position settings
                position = config.get('position', {})
                self.position_x = position.get('x')
                self.position_y = position.get('y')
                
                # Sound settings
                self.notification_sound = config.get('notification_sound', 'notification.mp3')
                
        except FileNotFoundError:
            print("config.json not found, using default values")
            self.work_duration = 25 * 60
            self.rest_duration = 5 * 60
            self.size = 60
            self.color_background = 'rgba(50, 50, 50, 100)'
            self.color_working = 'green'
            self.color_resting = 'yellow'
            self.color_waiting = 'blue'
            self.position_x = None
            self.position_y = None
            self.notification_sound = 'notification.mp3'

    def save_position(self):
        """Save current position to config.json"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            config['position'] = {
                'x': max(0, self.x()),
                'y': max(0, self.y())
            }
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
                
        except Exception as e:
            print(f"Error saving position: {e}")

    def parse_color(self, color_str):
        """Parse color string and return QColor"""
        if color_str.startswith('rgba'):
            # Parse rgba(r, g, b, a) format
            values = color_str.replace('rgba(', '').replace(')', '').split(',')
            if len(values) == 4:
                r, g, b, a = [int(v.strip()) for v in values]
                return QColor(r, g, b, a)
        return QColor(color_str)

    def get_time_remaining_text(self):
        """Get formatted time remaining text"""
        if self.phase == 'waiting':
            return "Waiting for activity..."
        elif self.phase == 'completing':
            return "Celebration!"
        elif self.phase == 'working':
            remaining = self.work_duration - self.elapsed
        else:  # resting
            remaining = self.rest_duration - self.elapsed
        
        if self.is_paused:
            remaining = remaining  # Show actual remaining time when paused
        
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{minutes:02d}:{seconds:02d}"

    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = QMenu(self)
        
        # Time remaining (disabled action as header)
        time_action = QAction(f"⏱️ {self.get_time_remaining_text()}", self)
        time_action.setEnabled(False)
        menu.addAction(time_action)
        
        # Phase info
        phase_text = f"📍 {self.phase.title()} Phase"
        if self.is_paused:
            phase_text += " (Paused)"
        phase_action = QAction(phase_text, self)
        phase_action.setEnabled(False)
        menu.addAction(phase_action)
        
        menu.addSeparator()
        
        # Pause/Resume button
        if self.phase in ['working', 'resting'] and not self.phase == 'completing':
            if self.is_paused:
                pause_action = QAction("▶️ Resume", self)
                pause_action.triggered.connect(self.resume_timer)
            else:
                pause_action = QAction("⏸️ Pause", self)
                pause_action.triggered.connect(self.pause_timer)
            menu.addAction(pause_action)
        
        # Skip to next phase
        if self.phase == 'working':
            skip_action = QAction("⏭️ Skip to Rest", self)
            skip_action.triggered.connect(self.skip_to_rest)
            menu.addAction(skip_action)
        elif self.phase == 'resting':
            skip_action = QAction("⏭️ Skip to Waiting", self)
            skip_action.triggered.connect(self.skip_to_waiting)
            menu.addAction(skip_action)
        elif self.phase == 'waiting':
            start_action = QAction("▶️ Start Work", self)
            start_action.triggered.connect(self.start_work_phase)
            menu.addAction(start_action)
        
        menu.addSeparator()
        
        # Lock/Unlock toggle
        if self.is_locked:
            lock_action = QAction("🔓 Unlock Position", self)
            lock_action.triggered.connect(self.toggle_lock)
        else:
            lock_action = QAction("🔒 Lock Position", self)
            lock_action.triggered.connect(self.toggle_lock)
        menu.addAction(lock_action)
        
        # Restart
        restart_action = QAction("⟳ Restart", self)
        restart_action.triggered.connect(self.restart_pomodoro)
        menu.addAction(restart_action)
        
        menu.addSeparator()
        
        # Exit
        exit_action = QAction("❌ Exit", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        
        # Show menu at cursor position
        menu.exec_(event.globalPos())

    def pause_timer(self):
        """Pause the current timer"""
        if self.phase in ['working', 'resting'] and not self.is_paused:
            self.is_paused = True
            self.paused_time = self.elapsed
            print(f"Timer paused at {self.get_time_remaining_text()}")

    def resume_timer(self):
        """Resume the paused timer"""
        if self.is_paused:
            self.is_paused = False
            print(f"Timer resumed with {self.get_time_remaining_text()} remaining")

    def skip_to_rest(self):
        """Skip work phase and go to rest"""
        if self.phase == 'working' or self.phase == 'completing':
            self.start_completion_animation()

    def skip_to_waiting(self):
        """Skip rest phase and go to waiting"""
        if self.phase == 'resting':
            self.start_waiting_phase()

    def toggle_lock(self):
        """Toggle lock state for drag and drop"""
        self.is_locked = not self.is_locked
        if self.is_locked:
            print("Pomodoro position locked")
        else:
            print("Pomodoro position unlocked")

    def restart_pomodoro(self):
        """Restart the pomodoro timer"""
        self.is_paused = False
        self.start_waiting_phase()
        print("Pomodoro restarted")

    def play_notification_sound(self):
        """Play notification sound when work ends"""
        try:
            sound_path = os.path.join('assets', 'notification-sound', self.notification_sound)
            if os.path.exists(sound_path):
                url = QUrl.fromLocalFile(os.path.abspath(sound_path))
                self.media_player.setMedia(QMediaContent(url))
                self.media_player.play()
            else:
                print(f"Sound file not found: {sound_path}")
        except Exception as e:
            print(f"Error playing sound: {e}")

    def start_completion_animation(self):
        """Start dizzy animation when work phase completes"""
        self.phase = 'completing'  # New phase for completion animation
        self.stop_animation()  # Stop any other animations
        self.play_notification_sound()  # Play sound when work ends
        self.completion_animation_timer = QTimer(self)
        self.completion_animation_timer.timeout.connect(self.update_completion_animation)
        self.completion_frame = 0
        self.completion_duration = 5000  # 5 seconds for better animation
        self.completion_animation_timer.start(33)  # 30 FPS for smoother animation
        print("Work completed! Starting celebration animation...")

    def update_completion_animation(self):
        """Update completion dizzy animation"""
        self.completion_frame += 1
        elapsed = self.completion_frame * 33  # milliseconds elapsed
        
        if elapsed >= self.completion_duration:
            self.completion_animation_timer.stop()
            self._animation_scale = 1.0
            self._animation_opacity = 1.0
            self._animation_rotation = 0.0
            self._shape_morph = 0.0
            self.start_rest_phase()  # Now start rest phase after animation completes
            return
        
        # Enhanced dizzy animation with multiple phases
        progress = elapsed / self.completion_duration
        
        # Phase 1: Rapid growth (0-20%)
        if progress < 0.2:
            phase_progress = progress / 0.2
            base_scale = 1.0 + 5.0 * phase_progress  # Grow to 6x size quickly
        # Phase 2: Maximum wobble (20-70%)
        elif progress < 0.7:
            phase_progress = (progress - 0.2) / 0.5
            base_scale = 6.0  # Stay at maximum size
        # Phase 3: Return to normal (70-100%)
        else:
            phase_progress = (progress - 0.7) / 0.3
            base_scale = 6.0 - 5.0 * phase_progress  # Shrink back to normal
        
        # Multiple wobble frequencies for dizzy effect
        wobble1 = 1.0 * math.sin(progress * math.pi * 18)  # Fast wobble
        wobble2 = 0.5 * math.sin(progress * math.pi * 28)  # Faster wobble
        wobble3 = 0.3 * math.sin(progress * math.pi * 40)  # Even faster wobble
        
        # Rotation effect - multiple rotations
        self._animation_rotation = progress * 720 + 180 * math.sin(progress * math.pi * 8)  # 2 full rotations + wobble
        
        # Shape morphing
        self._shape_morph = 0.8 * math.sin(progress * math.pi * 12)  # Morph between circle and oval
        
        self._animation_scale = base_scale + wobble1 + wobble2 + wobble3
        
        # Opacity pulsing with multiple frequencies
        opacity_pulse1 = 0.3 * math.sin(progress * math.pi * 15)
        opacity_pulse2 = 0.2 * math.sin(progress * math.pi * 25)
        self._animation_opacity = 0.6 + opacity_pulse1 + opacity_pulse2
        
        # Ensure values stay in reasonable bounds
        self._animation_scale = max(0.5, min(7.0, self._animation_scale))
        self._animation_opacity = max(0.3, min(1.0, self._animation_opacity))
        
        self.update()

    def start_waiting_animation(self):
        """Start slow breathing animation for waiting phase"""
        self.animation_timer.start(100)  # Slower update rate

    def start_resting_animation(self):
        """Start pulse animation for resting phase"""
        self.animation_timer.start(50)  # Faster update rate for pulse

    def stop_animation(self):
        """Stop all animations"""
        self.animation_timer.stop()
        self._animation_scale = 1.0
        self._animation_opacity = 1.0
        self._animation_rotation = 0.0
        self._shape_morph = 0.0

    def update_animation(self):
        """Update animation frame"""
        self.animation_frame += 1
        
        if self.phase == 'waiting':
            # Slow breathing animation (3 second cycle)
            cycle = (self.animation_frame * 0.1) % (2 * math.pi)
            self._animation_scale = 1.0 + 0.1 * math.sin(cycle * 0.5)  # Slower cycle
            self._animation_opacity = 0.7 + 0.3 * math.sin(cycle * 0.5)
            
        elif self.phase == 'resting':
            # Fast pulse animation (1 second cycle)
            cycle = (self.animation_frame * 0.05) % (2 * math.pi)
            self._animation_scale = 1.0 + 0.2 * math.sin(cycle * 2)  # Faster pulse
            self._animation_opacity = 0.6 + 0.4 * math.sin(cycle * 2)
        
        self.update()

    def create_blink_widget(self):
        """Create fullscreen blink widget"""
        pass

    def start_screen_blink(self):
        """Start screen blinking effect"""
        pass

    def toggle_blink(self):
        """Toggle blink visibility"""
        pass

    def stop_screen_blink(self):
        """Stop screen blinking effect"""
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Apply animation transformations
        painter.setOpacity(self._animation_opacity)
        
        # Calculate center and scale
        center_x = self.size // 2
        center_y = self.size // 2
        
        # Save painter state
        painter.save()
        painter.translate(center_x, center_y)
        painter.scale(self._animation_scale, self._animation_scale)
        painter.rotate(self._animation_rotation)  # Add rotation
        painter.translate(-center_x, -center_y)

        # Choose color based on phase
        if self.phase == 'working':
            color = self.parse_color(self.color_working)
        elif self.phase == 'resting':
            color = self.parse_color(self.color_resting)
        elif self.phase == 'completing':
            # Transition color from work to rest during animation
            if hasattr(self, 'completion_frame') and hasattr(self, 'completion_duration'):
                progress = min(1.0, (self.completion_frame * 33) / self.completion_duration)
                work_color = self.parse_color(self.color_working)
                rest_color = self.parse_color(self.color_resting)
                
                # Interpolate between work and rest colors
                r = int(work_color.red() + (rest_color.red() - work_color.red()) * progress)
                g = int(work_color.green() + (rest_color.green() - work_color.green()) * progress)
                b = int(work_color.blue() + (rest_color.blue() - work_color.blue()) * progress)
                color = QColor(r, g, b)
            else:
                color = self.parse_color(self.color_working)
        else:  # waiting
            color = self.parse_color(self.color_waiting)

        # Calculate circle dimensions
        margin = 5
        circle_size = self.size - 2 * margin
        radius = circle_size // 2

        if self.phase == 'working':
            # Draw progress as a filled pie slice
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)  # Remove border
            
            # Background circle (empty part)
            bg_color = self.parse_color(self.color_background)
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(margin, margin, circle_size, circle_size)
            
            # Progress pie slice
            painter.setBrush(QBrush(color))
            angle = int(360 * self.progress)
            painter.drawPie(margin, margin, circle_size, circle_size, 90 * 16, -angle * 16)
        elif self.phase == 'resting':
            # Draw progress as a filled pie slice for resting too
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)  # Remove border
            
            # Background circle (empty part)
            bg_color = self.parse_color(self.color_background)
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(margin, margin, circle_size, circle_size)
            
            # Progress pie slice
            painter.setBrush(QBrush(color))
            angle = int(360 * self.progress)
            painter.drawPie(margin, margin, circle_size, circle_size, 90 * 16, -angle * 16)
        elif self.phase == 'completing':
            # Draw as morphing shape during completion animation with rotation
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)  # Remove border
            
            # Apply shape morphing
            morph_offset = int(circle_size * 0.3 * self._shape_morph)
            ellipse_width = circle_size + morph_offset
            ellipse_height = circle_size - morph_offset
            
            x_offset = (circle_size - ellipse_width) // 2
            y_offset = (circle_size - ellipse_height) // 2
            
            painter.drawEllipse(margin + x_offset, margin + y_offset, ellipse_width, ellipse_height)
        else:
            # Draw as filled circle for waiting phase only
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)  # Remove border
            painter.drawEllipse(margin, margin, circle_size, circle_size)

        # Restore painter state
        painter.restore()

    def update_progress(self):
        if self.phase == 'waiting' or self.phase == 'completing' or self.is_paused:
            # Don't update progress when paused
            return
        
        self.elapsed += 1
        
        if self.phase == 'working':
            if self.elapsed >= self.work_duration:
                print("Work session completed! Starting completion animation...")
                self.start_completion_animation()  # Start dizzy animation first
                # Don't start rest phase immediately - wait for animation to complete
            else:
                # Progress decreases as time passes (starts full, goes to empty)
                self.progress = max(0.0, 1.0 - (self.elapsed / self.work_duration))
                
        elif self.phase == 'resting':
            if self.elapsed >= self.rest_duration:
                print("Rest completed! Waiting for next session...")
                self.start_waiting_phase()
            else:
                # Progress decreases as time passes (starts full, goes to empty)
                self.progress = max(0.0, 1.0 - (self.elapsed / self.rest_duration))

        self.update()

    def start_work_phase(self):
        """Start a work session"""
        self.phase = 'working'
        self.elapsed = 0
        self.progress = 1.0  # Start full
        self.is_paused = False
        self.stop_listeners()
        self.stop_animation()  # Stop animations during work
        print(f"Starting work session ({self.work_duration // 60} minutes)")

    def start_rest_phase(self):
        """Start a rest session"""
        self.phase = 'resting'
        self.elapsed = 0
        self.progress = 1.0  # Start full
        self.is_paused = False
        self.start_resting_animation()  # Start pulse animation
        print(f"Starting rest session ({self.rest_duration // 60} minutes)")

    def start_waiting_phase(self):
        """Wait for user input to start next work session"""
        self.phase = 'waiting'
        self.elapsed = 0
        self.progress = 1.0  # Full circle in blue
        self.is_paused = False
        self.start_listeners()
        self.start_waiting_animation()  # Start breathing animation
        print("Waiting for activity to start next work session...")

    def start_listeners(self):
        """Start mouse and keyboard listeners (only during waiting phase)"""
        if self.mouse_listener is None:
            def on_input(*args):
                if self.phase == 'waiting' and not self.is_dragging:
                    self.start_work_phase()
                # Don't respond to input during completion animation

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

    def stop_listeners(self):
        """Stop mouse and keyboard listeners"""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

    def mousePressEvent(self, event):
        """Handle mouse press for immediate drag functionality"""
        if event.button() == Qt.LeftButton and not self.is_locked:
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            self.is_dragging = True
            # Stop input listeners while dragging
            if self.phase == 'waiting':
                self.stop_listeners()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self.is_dragging and not self.is_locked:
            new_pos = event.globalPos() - self.drag_start_position
            # Constrain to screen bounds
            screen = QDesktopWidget().screenGeometry()
            new_x = max(0, min(new_pos.x(), screen.width() - self.width()))
            new_y = max(0, min(new_pos.y(), screen.height() - self.height()))
            self.move(new_x, new_y)

    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton and self.is_dragging and not self.is_locked:
            self.is_dragging = False
            self.save_position()
            # Restart listeners if in waiting phase
            if self.phase == 'waiting':
                self.start_listeners()

    def closeEvent(self, event):
        """Clean up listeners and timers when closing the app"""
        self.stop_listeners()
        self.stop_animation()
        if hasattr(self, 'completion_animation_timer') and self.completion_animation_timer:
            self.completion_animation_timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CircleWindow()
    window.show()
    print("Enhanced Pomodoro Timer started!")
    print("Blue circle = Waiting for activity to start (breathing animation)")
    print("Green circle = Work session in progress (progress pie)")
    print("Yellow circle = Rest session in progress (progress pie with pulse)")
    print("Ball will grow large with dizzy animation when work session ends")
    sys.exit(app.exec_())