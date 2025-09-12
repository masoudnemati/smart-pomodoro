"""
Context Menu for Smart Pomodoro Timer
"""

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import QObject, pyqtSignal
from utils.constants import Phase, UI_CONSTANTS


class ContextMenu(QObject):
    """Handles right-click context menu"""
    
    # Signals
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    skip_to_rest_requested = pyqtSignal()
    skip_to_waiting_requested = pyqtSignal()
    start_work_requested = pyqtSignal()
    toggle_lock_requested = pyqtSignal()
    restart_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.icons = UI_CONSTANTS['menu_icons']
    
    def create_menu(self, phase: str, is_paused: bool, is_locked: bool, 
                   time_remaining: str) -> QMenu:
        """Create context menu based on current state"""
        menu = QMenu(self.parent)
        
        # Time remaining (disabled action as header)
        time_action = QAction(f"{self.icons['time']} {time_remaining}", menu)
        time_action.setEnabled(False)
        menu.addAction(time_action)
        
        # Phase info
        phase_text = f"{self.icons['phase']} {phase.title()} Phase"
        if is_paused:
            phase_text += " (Paused)"
        phase_action = QAction(phase_text, menu)
        phase_action.setEnabled(False)
        menu.addAction(phase_action)
        
        menu.addSeparator()
        
        # Pause/Resume button
        if phase in ['working', 'resting'] and phase != 'completing':
            if is_paused:
                pause_action = QAction(f"{self.icons['resume']} Resume", menu)
                pause_action.triggered.connect(self.resume_requested.emit)
            else:
                pause_action = QAction(f"{self.icons['pause']} Pause", menu)
                pause_action.triggered.connect(self.pause_requested.emit)
            menu.addAction(pause_action)
        
        # Skip to next phase
        if phase == 'working':
            skip_action = QAction(f"{self.icons['skip']} Skip to Rest", menu)
            skip_action.triggered.connect(self.skip_to_rest_requested.emit)
            menu.addAction(skip_action)
        elif phase == 'resting':
            skip_action = QAction(f"{self.icons['skip']} Skip to Waiting", menu)
            skip_action.triggered.connect(self.skip_to_waiting_requested.emit)
            menu.addAction(skip_action)
        elif phase == 'waiting':
            start_action = QAction(f"{self.icons['resume']} Start Work", menu)
            start_action.triggered.connect(self.start_work_requested.emit)
            menu.addAction(start_action)
        
        menu.addSeparator()
        
        # Lock/Unlock toggle
        if is_locked:
            lock_action = QAction(f"{self.icons['unlock']} Unlock Position", menu)
        else:
            lock_action = QAction(f"{self.icons['lock']} Lock Position", menu)
        lock_action.triggered.connect(self.toggle_lock_requested.emit)
        menu.addAction(lock_action)
        
        # Restart
        restart_action = QAction(f"{self.icons['restart']} Restart", menu)
        restart_action.triggered.connect(self.restart_requested.emit)
        menu.addAction(restart_action)
        
        menu.addSeparator()
        
        # Exit
        exit_action = QAction(f"{self.icons['exit']} Exit", menu)
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.addAction(exit_action)
        
        return menu