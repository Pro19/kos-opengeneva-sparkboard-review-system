"""
PyQt6-based GUI for the Ontology-Driven Hackathon Review System.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel


class MaterialColors:
    """Material Design color palette."""
    PRIMARY = "#2196F3"
    PRIMARY_DARK = "#1976D2"
    PRIMARY_LIGHT = "#BBDEFB"
    SURFACE = "#FFFFFF"
    BACKGROUND = "#FAFAFA"
    ON_SURFACE = "#212121"
    ON_BACKGROUND = "#424242"
    DIVIDER = "#E0E0E0"


def apply_material_style():
    """Apply Material Design styles."""
    return f"""
    QMainWindow {{
        background-color: {MaterialColors.BACKGROUND};
        color: {MaterialColors.ON_BACKGROUND};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {MaterialColors.DIVIDER};
        background-color: {MaterialColors.SURFACE};
        border-radius: 8px;
    }}
    
    QTabBar::tab {{
        background-color: {MaterialColors.SURFACE};
        color: {MaterialColors.ON_SURFACE};
        padding: 12px 24px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 500;
        min-width: 100px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {MaterialColors.PRIMARY};
        color: white;
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {MaterialColors.PRIMARY_LIGHT};
    }}
    
    QLabel {{
        color: {MaterialColors.ON_SURFACE};
    }}
    """


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

        # Apply Material Design styling
        self.setStyleSheet(apply_material_style())


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Hackathon Review System")

    # Apply Material Design styles
    apply_material_style()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
