"""
PyQt6-based GUI for the Ontology-Driven Hackathon Review System.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle("Hackathon Review System")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create tab widget with placeholder tabs
        tab_widget = QTabWidget()

        # Add placeholder tabs
        for name in ["Projects", "Configuration", "Analysis", "Results"]:
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab_layout.addWidget(QLabel(f"{name} - Coming soon!"))
            tab.setLayout(tab_layout)
            tab_widget.addTab(tab, name)

        layout.addWidget(tab_widget)
        self.statusBar().showMessage("Ready")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Hackathon Review System")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
