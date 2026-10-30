from enum import Enum


class Phase(Enum):
    """Pomodoro timer phases"""
    WAITING = 'waiting'
    WORKING = 'working'
    RESTING = 'resting'
    COMPLETING = 'completing'


# Default configuration
DEFAULT_CONFIG = {
    'work_time_minutes': 25,
    'rest_time_minutes': 5,
    'size': 60,
   'colors': {
        'background': 'rgba(50, 50, 50, 100)',
        'working': 'lightgray',
        'resting': 'red',
        'waiting': 'green',
        'shadow': 'rgba(0, 0, 0, 40)',
        'counter_background': 'rgba(0, 0, 0, 180)',
        'counter_text': 'white'
},
    'position': {
        'x': None,
        'y': None
    },
    'notification_sound': 'notification.mp3'
}

# Animation constants
ANIMATION_CONSTANTS = {
    'waiting': {
        'update_rate': 100,  # ms
        'scale_amplitude': 0.1,
        'opacity_base': 0.7,
        'opacity_amplitude': 0.3,
        'cycle_speed': 0.5
    },
    'resting': {
        'update_rate': 50,  # ms
        'scale_amplitude': 0.2,
        'opacity_base': 0.6,
        'opacity_amplitude': 0.4,
        'cycle_speed': 2.0
    },
    'completion': {
        'duration': 5000,  # ms
        'update_rate': 33,  # ms (30 FPS)
        'max_scale': 6.0,
        'rotation_cycles': 2,
        'morph_amplitude': 0.8
    }
}

# UI constants
UI_CONSTANTS = {
    'circle_margin': 5,
    'drag_threshold': 3,  # pixels
    'menu_icons': {
        'time': '⏱️',
        'phase': '📍',
        'pause': '⏸️',
        'resume': '▶️',
        'skip': '⏭️',
        'lock': '🔒',
        'unlock': '🔓',
        'restart': '⟳',
        'exit': '❌'
    }
}

# Timer update interval
TIMER_UPDATE_INTERVAL = 1000  # ms (1 second)

# Sound settings
SOUND_CONSTANTS = {
    'assets_path': 'assets/notification-sound/',
    'default_sound': 'notification.mp3'
}