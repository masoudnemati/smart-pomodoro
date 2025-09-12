import sys
from PyQt5.QtWidgets import QApplication
from ui.circle_window import CircleWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = CircleWindow()
    window.show()


    
    # Print startup messages
    print("Enhanced Pomodoro Timer started!")
    
    # Start the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()