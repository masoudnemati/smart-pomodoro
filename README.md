# Smart Pomodoro

⚡ Smart Pomodoro is an activity-aware Pomodoro timer that starts automatically when it detects mouse or keyboard input. No need to click "Start" — just start working.

## Features

- **🎯 Activity Detection**: Automatically starts when it detects mouse or keyboard activity
- **⏰ Pomodoro Technique**: Classic work + rest cycles (25min work, 5min rest by default)
- **🚀 No Manual Start**: Just start working - no buttons to click
- **🎨 Visual Feedback**: Color-coded animations for each phase
- **🔊 Audio Notifications**: Sound alerts for phase transitions
- **⏸️ Pause/Resume**: Full timer control via right-click menu
- **📍 Draggable**: Move anywhere on screen with position memory
- **🔒 Lock Mode**: Prevent accidental movement
- **🔄 Sleep/Wake Detection**: Automatically restarts the timer when the system wakes up from suspend
- **⚙️ Configurable**: Customize colors, durations, sounds via JSON

## Requirements

- Python 3.7+
- PyQt5
- pynput

## Setup

```bash
# Clone repo
git clone https://github.com/masoudnemati/smart-pomodoro.git
cd smart-pomodoro

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run (NEW - updated for modular structure)
python src/main.py
```

## Usage

1. Navigate to project directory: `cd smart-pomodoro`
2. Activate virtual environment: `source venv/bin/activate` (On Windows: `venv\Scripts\activate`)
3. Run `python src/main.py`

## Configuration

Edit `config.json` to customize:

- Work/rest durations
- Colors and size
- Notification sounds
- Window position
