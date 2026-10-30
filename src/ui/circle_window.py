from PyQt5.QtWidgets import QWidget, QDesktopWidget, QInputDialog
from PyQt5.QtDBus import QDBusConnection  
from PyQt5.QtCore import Qt, QPoint, pyqtSlot, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetricsF
from config.config_manager import ConfigManager
from core.input_manager import InputManager
from core.pomodoro_timer import PomodoroTimer
from ui.context_menu import ContextMenu
from animations.waiting_animation import WaitingAnimation
from animations.resting_animation import RestingAnimation
from animations.completion_animation import CompletionAnimation
from utils.audio_player import AudioPlayer
from utils.constants import Phase, UI_CONSTANTS


class CircleWindow(QWidget):
    """Main circular window for the Pomodoro timer"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.config = ConfigManager()
        self.pomodoros_completed = int(
            self.config.get('pomodoros_completed', 0)
        )
        self.pomodoro_goal = int(
            self.config.get('pomodoro_goal', 4)
        )
        self.setup_window()
        
        # Core components
        self.timer = PomodoroTimer(self.config)
        self.input_manager = InputManager()
        self.context_menu = ContextMenu(self)
        self.audio_player = AudioPlayer()
        
        # Animation components
        self.waiting_animation = WaitingAnimation()
        self.resting_animation = RestingAnimation()
        self.completion_animation = CompletionAnimation()
        self.current_animation = None
        
        # State
        self.current_phase = Phase.WAITING.value
        self.current_progress = 1.0
        self.is_locked = False
        self.is_dragging = False
        self.drag_start_position = QPoint()
        
        # Animation properties
        self.animation_scale = 1.0
        self.animation_opacity = 1.0
        self.animation_rotation = 0.0
        self.animation_shape_morph = 0.0
        
        self.connect_signals()
        self.start_initial_state()

        # ---------- suspend/resume detection ----------
        bus = QDBusConnection.systemBus()
        if bus.isConnected():
            result = bus.connect(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager",
                "PrepareForSleep",
                self._on_system_sleep_signal   # we'll define this method next
            )
            if result:
                print("✅ Suspend/resume detection enabled!")
            else:
                print("❌ Failed to connect signal")
        else:
            print("❌ System D-Bus not available")
    
    def setup_window(self):
        """Setup window properties"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set size and position from config
        size = self.config.size
        self.setFixedSize(size, size)
        
        position = self.config.position
        if position['x'] is not None and position['y'] is not None:
            self.move(max(0, position['x']), max(0, position['y']))
    
    def connect_signals(self):
        """Connect all component signals"""
        # Timer signals
        self.timer.phase_changed.connect(self.on_phase_changed)
        self.timer.progress_updated.connect(self.on_progress_updated)
        self.timer.work_completed.connect(self.on_work_completed)
        self.timer.rest_completed.connect(self.on_rest_completed)
        
        # Input manager signals
        self.input_manager.activity_detected.connect(self.on_activity_detected)

        
        # Context menu signals
        self.context_menu.pause_requested.connect(self.timer.pause_timer)
        self.context_menu.resume_requested.connect(self.timer.resume_timer)
        self.context_menu.skip_to_rest_requested.connect(self.timer.skip_to_rest)
        self.context_menu.skip_to_waiting_requested.connect(self.timer.skip_to_waiting)
        self.context_menu.start_work_requested.connect(self.timer.start_work_phase)
        self.context_menu.toggle_lock_requested.connect(self.toggle_lock)
        self.context_menu.restart_requested.connect(self.timer.restart)
        self.context_menu.exit_requested.connect(self.close)
        
        # Animation signals
        self.waiting_animation.animation_updated.connect(self.update_animation_properties)
        self.resting_animation.animation_updated.connect(self.update_animation_properties)
        self.completion_animation.animation_updated.connect(self.update_animation_properties)
        self.completion_animation.animation_finished.connect(self.on_completion_finished)

        self.timer.pomodoro_completed.connect(self.on_pomodoro_completed)
        self.context_menu.change_goal_requested.connect(self.change_pomodoro_goal)
    
    def start_initial_state(self):
        """Start in waiting state"""
        self.timer.start_waiting_phase()
        self.input_manager.start_listening() 

    
    def on_phase_changed(self, phase: str):
        """Handle phase change"""
        self.current_phase = phase
        
        # Stop current animation
        if self.current_animation:
            self.current_animation.stop()
        
        # Start appropriate animation
        if phase == Phase.WAITING.value:
            self.current_animation = self.waiting_animation
            self.current_animation.start()
            self.input_manager.start_listening()
        elif phase == Phase.WORKING.value:
            self.input_manager.stop_listening()
            self.current_animation = None
        elif phase == Phase.RESTING.value:
            self.current_animation = self.resting_animation
            self.current_animation.start()
        elif phase == Phase.COMPLETING.value:
            self.current_animation = self.completion_animation
            self.current_animation.start()
        
        self.update()
    
    def draw_shadow(self, painter: QPainter):
        """Draw a centered, soft shadow that acts like a subtle border + 2px glow."""
        shadow_color = self.get_shadow_color()
        base_alpha = shadow_color.alpha()

        margin = UI_CONSTANTS['circle_margin']
        circle_size = self.width() - 2 * margin

        painter.save()

        # Layer 1: the "1px border" – almost solid at the exact edge
        c1 = QColor(shadow_color)
        c1.setAlpha(base_alpha)                        # full shadow opacity (e.g. 40)
        painter.setBrush(c1)
        painter.setPen(Qt.NoPen)
        # Slightly larger to overlap the circle edge → looks like a 1px border
        painter.drawEllipse(margin - 1, margin - 1, circle_size + 2, circle_size + 2)

        # Layer 2: the "2px spread" – wider, more transparent
        c2 = QColor(shadow_color)
        c2.setAlpha(base_alpha // 3)                   # much fainter
        painter.setBrush(c2)
        painter.drawEllipse(margin - 3, margin - 3, circle_size + 6, circle_size + 6)

        painter.restore()

    def on_progress_updated(self, progress: float):
        """Handle progress update"""
        self.current_progress = progress
        self.update()
    
    def on_work_completed(self):
        """Handle work completion"""
        self.audio_player.play_notification(self.config.notification_sound)
    
    def on_rest_completed(self):
        """Handle rest completion"""
        pass
    
    def on_activity_detected(self):
        """Handle user activity detection"""
        if self.current_phase == Phase.WAITING.value and not self.is_dragging:
            self.timer.start_work_phase()
    
    def on_completion_finished(self):
        """Handle completion animation finished"""
        self.timer.start_rest_phase()
    
    def update_animation_properties(self, properties: dict):
        """Update animation properties and redraw"""
        self.animation_scale = properties.get('scale', 1.0)
        self.animation_opacity = properties.get('opacity', 1.0)
        self.animation_rotation = properties.get('rotation', 0.0)
        self.animation_shape_morph = properties.get('shape_morph', 0.0)
        self.update()
    
    def toggle_lock(self):
        """Toggle position lock"""
        self.is_locked = not self.is_locked
        print(f"Position {'locked' if self.is_locked else 'unlocked'}")
    
    def parse_color(self, color_str: str) -> QColor:
        """Parse color string and return QColor"""
        if color_str.startswith('rgba'):
            values = color_str.replace('rgba(', '').replace(')', '').split(',')
            if len(values) == 4:
                r, g, b, a = [int(v.strip()) for v in values]
                return QColor(r, g, b, a)
        return QColor(color_str)
    
    def get_phase_color(self) -> QColor:
        """Get color for current phase"""
        colors = self.config.colors
        
        if self.current_phase == Phase.WORKING.value:
            return self.parse_color(colors['working'])
        elif self.current_phase == Phase.RESTING.value:
            return self.parse_color(colors['resting'])
        elif self.current_phase == Phase.COMPLETING.value:
            # Transition from work to rest color during completion
            work_color = self.parse_color(colors['working'])
            rest_color = self.parse_color(colors['resting'])
            # Simple interpolation (could be enhanced)
            return rest_color
        else:  # waiting
            return self.parse_color(colors['waiting'])

    def get_shadow_color(self) -> QColor:
        """Return the shadow color from config, or a default if not set."""
        shadow_str = self.config.colors.get('shadow', 'rgba(0, 0, 0, 40)')
        return self.parse_color(shadow_str)

    def paintEvent(self, event):
        """Paint the circular timer"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        #  Draw the shadow first (so it appears behind the circle)
        self.draw_shadow(painter)
        
        # Apply animation properties
        painter.setOpacity(self.animation_opacity)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Apply transformations
        painter.save()
        painter.translate(center_x, center_y)
        painter.scale(self.animation_scale, self.animation_scale)
        painter.rotate(self.animation_rotation)
        painter.translate(-center_x, -center_y)
        
        # Get colors and dimensions
        color = self.get_phase_color()
        margin = UI_CONSTANTS['circle_margin']
        circle_size = self.width() - 2 * margin
        
        # Draw based on phase
        if self.current_phase in [Phase.WORKING.value, Phase.RESTING.value]:
            self.draw_progress_pie(painter, margin, circle_size, color)
        elif self.current_phase == Phase.COMPLETING.value:
            self.draw_morphing_circle(painter, margin, circle_size, color)
        else:  # waiting
            self.draw_full_circle(painter, margin, circle_size, color)
        
        painter.restore()
        self.draw_pomodoro_counter(painter)
    
    def draw_progress_pie(self, painter: QPainter, margin: int, size: int, color: QColor):
        """Draw progress pie chart"""
        # Background circle
        bg_color = self.parse_color(self.config.colors['background'])
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(margin, margin, size, size)
        
        # Progress pie
        painter.setBrush(QBrush(color))
        angle = int(360 * self.current_progress)
        painter.drawPie(margin, margin, size, size, 90 * 16, -angle * 16)
    
    def draw_morphing_circle(self, painter: QPainter, margin: int, size: int, color: QColor):
        """Draw morphing ellipse during completion"""
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        # Apply morphing
        morph_offset = int(size * 0.3 * self.animation_shape_morph)
        ellipse_width = size + morph_offset
        ellipse_height = size - morph_offset
        
        x_offset = (size - ellipse_width) // 2
        y_offset = (size - ellipse_height) // 2
        
        painter.drawEllipse(margin + x_offset, margin + y_offset, ellipse_width, ellipse_height)
    
    def draw_full_circle(self, painter: QPainter, margin: int, size: int, color: QColor):
        """Draw full circle"""
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(margin, margin, size, size)
    
    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = self.context_menu.create_menu(
            self.current_phase,
            self.timer.is_paused,
            self.is_locked,
            self.timer.get_time_remaining_text(),
            self.pomodoros_completed,
            self.pomodoro_goal
        )
        menu.exec_(event.globalPos())
    
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton and not self.is_locked:
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            self.is_dragging = True
            self.input_manager.set_ignore_input(True)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event.buttons() == Qt.LeftButton and self.is_dragging and not self.is_locked:
            new_pos = event.globalPos() - self.drag_start_position
            screen = QDesktopWidget().screenGeometry()
            new_x = max(0, min(new_pos.x(), screen.width() - self.width()))
            new_y = max(0, min(new_pos.y(), screen.height() - self.height()))
            self.move(new_x, new_y)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if event.button() == Qt.LeftButton and self.is_dragging and not self.is_locked:
            self.is_dragging = False
            self.input_manager.set_ignore_input(False)
            self.config.update_position(self.x(), self.y())
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.current_animation:
            self.current_animation.cleanup()
        self.timer.cleanup()
        self.input_manager.cleanup()
        event.accept()

    @pyqtSlot(bool)
    def _on_system_sleep_signal(self, sleeping: bool):
        """Called when system suspends or wakes up."""
        print(f"D-Bus signal received! sleeping={sleeping}")
        if not sleeping:                # waking up
            print("System resumed from sleep – restarting Pomodoro.")
            self.timer.restart()

    def on_pomodoro_completed(self):
        """Increment and save completed Pomodoros"""
        self.pomodoros_completed += 1

        self.config.set('pomodoros_completed', self.pomodoros_completed)
        self.config.save_config()


    def change_pomodoro_goal(self):
        """Allow the user to change the Pomodoro goal"""
        goal, accepted = QInputDialog.getInt(
            self,
            "Pomodoro Goal",
            "Number of Pomodoros:",
            self.pomodoro_goal,
            1,
            99
        )

        if accepted:
            self.pomodoro_goal = goal

            self.config.set('pomodoro_goal', self.pomodoro_goal)
            self.config.save_config()

    def draw_pomodoro_counter(self, painter: QPainter):
        """Draw Pomodoro counter in the exact center of the circle"""
        painter.save()
        painter.setOpacity(1.0)

        center_x = self.width() / 2
        center_y = self.height() / 2

        margin = UI_CONSTANTS['circle_margin']
        circle_diameter = min(self.width(), self.height()) - 2 * margin

        diameter = circle_diameter * 0.90

        counter_rect = QRectF(
            center_x - diameter / 2,
            center_y - diameter / 2,
            diameter,
            diameter
        )

        # Counter background
        bg_color = self.parse_color(
            self.config.colors.get(
                'counter_background', 'rgba(0, 0, 0, 180)'
            )
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawEllipse(counter_rect)

        # Counter text
        text_color = self.parse_color(
            self.config.colors.get('counter_text', 'white')
        )

        counter_text = f"{self.pomodoros_completed}/{self.pomodoro_goal}"

        font = QFont()
        font.setBold(True)

        font_size = max(9, int(diameter * 0.56))
        font.setPixelSize(font_size)

        # Ensure text fits inside the background circle
        metrics = QFontMetricsF(font)
        max_text_width = diameter * 0.90
        text_width = metrics.horizontalAdvance(counter_text)

        if text_width > max_text_width:
            font.setPixelSize(
                max(8, int(font_size * max_text_width / text_width))
            )

        painter.setFont(font)
        painter.setPen(text_color)

        # Center text horizontally and vertically
        painter.drawText(counter_rect, Qt.AlignCenter, counter_text)

        painter.restore()