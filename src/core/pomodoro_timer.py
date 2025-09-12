from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from utils.constants import Phase, TIMER_UPDATE_INTERVAL
from config.config_manager import ConfigManager

class PomodoroTimer(QObject):
    """Core timer logic for Pomodoro sessions"""
    
    # Signals
    phase_changed = pyqtSignal(str)  # Phase.value
    progress_updated = pyqtSignal(float)  # Progress (0.0 to 1.0)
    work_completed = pyqtSignal()
    rest_completed = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        
        # Timer state
        self.phase = Phase.WAITING
        self.progress = 1.0
        self.elapsed = 0
        self.is_paused = False
        
        # Setup timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)
        self.timer.start(TIMER_UPDATE_INTERVAL)
    
    def start_work_phase(self) -> None:
        """Start a work session"""
        self._set_phase(Phase.WORKING)
        self.elapsed = 0
        self.progress = 1.0
        self.is_paused = False
        print(f"Starting work session ({self.config.work_duration // 60} minutes)")
    
    def start_rest_phase(self) -> None:
        """Start a rest session"""
        self._set_phase(Phase.RESTING)
        self.elapsed = 0
        self.progress = 1.0
        self.is_paused = False
        print(f"Starting rest session ({self.config.rest_duration // 60} minutes)")
    
    def start_waiting_phase(self) -> None:
        """Wait for user input to start next work session"""
        self._set_phase(Phase.WAITING)
        self.elapsed = 0
        self.progress = 1.0
        self.is_paused = False
        print("Waiting for activity to start next work session...")
    
    def start_completion_phase(self) -> None:
        """Start completion animation phase"""
        self._set_phase(Phase.COMPLETING)
        self.work_completed.emit()
        print("Work completed! Starting celebration animation...")
    
    def pause_timer(self) -> bool:
        """Pause the current timer"""
        if self.phase in [Phase.WORKING, Phase.RESTING] and not self.is_paused:
            self.is_paused = True
            print(f"Timer paused at {self.get_time_remaining_text()}")
            return True
        return False
    
    def resume_timer(self) -> bool:
        """Resume the paused timer"""
        if self.is_paused:
            self.is_paused = False
            print(f"Timer resumed with {self.get_time_remaining_text()} remaining")
            return True
        return False
    
    def skip_to_rest(self) -> None:
        """Skip work phase and go to rest"""
        if self.phase == Phase.WORKING:
            self.start_completion_phase()
    
    def skip_to_waiting(self) -> None:
        """Skip rest phase and go to waiting"""
        if self.phase == Phase.RESTING:
            self.start_waiting_phase()
    
    def restart(self) -> None:
        """Restart the pomodoro timer"""
        self.is_paused = False
        self.start_waiting_phase()
        print("Pomodoro restarted")
    
    def get_time_remaining_text(self) -> str:
        """Get formatted time remaining text"""
        if self.phase == Phase.WAITING:
            return "Waiting for activity..."
        elif self.phase == Phase.COMPLETING:
            return "Celebration!"
        elif self.phase == Phase.WORKING:
            remaining = self.config.work_duration - self.elapsed
        else:  # resting
            remaining = self.config.rest_duration - self.elapsed
        
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_phase_text(self) -> str:
        """Get formatted phase text"""
        phase_text = f"{self.phase.value.title()} Phase"
        if self.is_paused:
            phase_text += " (Paused)"
        return phase_text
    
    def _set_phase(self, new_phase: Phase) -> None:
        """Set new phase and emit signal"""
        if self.phase != new_phase:
            self.phase = new_phase
            self.phase_changed.emit(new_phase.value)
    
    def _update_timer(self) -> None:
        """Update timer progress"""
        if self.phase in [Phase.WAITING, Phase.COMPLETING] or self.is_paused:
            return
        
        self.elapsed += 1
        
        if self.phase == Phase.WORKING:
            if self.elapsed >= self.config.work_duration:
                self.start_completion_phase()
            else:
                # Progress decreases as time passes (starts full, goes to empty)
                self.progress = max(0.0, 1.0 - (self.elapsed / self.config.work_duration))
                
        elif self.phase == Phase.RESTING:
            if self.elapsed >= self.config.rest_duration:
                self.rest_completed.emit()
                self.start_waiting_phase()
            else:
                # Progress decreases as time passes (starts full, goes to empty)
                self.progress = max(0.0, 1.0 - (self.elapsed / self.config.rest_duration))
        
        self.progress_updated.emit(self.progress)
    
    def cleanup(self) -> None:
        """Clean up timer resources"""
        if self.timer.isActive():
            self.timer.stop()