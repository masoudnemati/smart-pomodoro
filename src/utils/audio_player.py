import os
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from utils.constants import SOUND_CONSTANTS


class AudioPlayer:
    """Handles audio playback for notifications"""
    
    def __init__(self):
        self.media_player = QMediaPlayer()
    
    def play_notification(self, sound_file: str = None) -> bool:
        """Play notification sound
        
        Args:
            sound_file: Optional sound file name. If None, uses default.
            
        Returns:
            bool: True if sound was played successfully, False otherwise
        """
        if sound_file is None:
            sound_file = SOUND_CONSTANTS['default_sound']
        
        try:
            sound_path = os.path.join(
                SOUND_CONSTANTS['assets_path'],
                sound_file
            )
            
            if not os.path.exists(sound_path):
                print(f"Sound file not found: {sound_path}")
                return False
            
            url = QUrl.fromLocalFile(os.path.abspath(sound_path))
            self.media_player.setMedia(QMediaContent(url))
            self.media_player.play()
            return True
            
        except Exception as e:
            print(f"Error playing sound: {e}")
            return False
    
    def stop(self) -> None:
        """Stop current playback"""
        self.media_player.stop()
    
    def set_volume(self, volume: int) -> None:
        """Set playback volume
        
        Args:
            volume: Volume level (0-100)
        """
        self.media_player.setVolume(max(0, min(100, volume)))