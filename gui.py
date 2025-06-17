"""
PyQt6-based GUI for the Ontology-Driven Hackathon Review System.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QMessageBox, QFileDialog, QComboBox, QCheckBox, QSpinBox,
    QFormLayout
)
from PyQt6.QtCore import Qt

# Import the existing modules
from project import load_all_projects
from config import PATHS, SETTINGS, LLM_CONFIG
from logging_utils import logger


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


class ProjectTab(QWidget):
    """Tab for project management and selection."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.projects = []
        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        """Set up the project tab UI."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Project directory selection
        dir_group = QGroupBox("📁 Project Directory")
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(12)

        self.dir_path = QLineEdit(PATHS.get("projects_dir", "projects/"))
        self.dir_browse_btn = QPushButton("Browse")
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_projects)
        self.dir_browse_btn.clicked.connect(self.browse_directory)

        dir_layout.addWidget(QLabel("Directory:"))
        dir_layout.addWidget(self.dir_path, 1)
        dir_layout.addWidget(self.dir_browse_btn)
        dir_layout.addWidget(self.refresh_btn)
        dir_group.setLayout(dir_layout)

        # Project list
        list_group = QGroupBox("📋 Available Projects")
        list_layout = QVBoxLayout()

        self.project_list = QTreeWidget()
        self.project_list.setHeaderLabels(["Project", "Reviews", "Status"])
        self.project_list.setAlternatingRowColors(True)

        list_layout.addWidget(self.project_list)
        list_group.setLayout(list_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)

        self.analyze_btn = QPushButton("🚀 Analyze Selected Projects")

        action_layout.addStretch()
        action_layout.addWidget(self.analyze_btn)

        # Layout assembly
        layout.addWidget(dir_group)
        layout.addWidget(list_group, 1)
        layout.addLayout(action_layout)

        self.setLayout(layout)

    def browse_directory(self):
        """Browse for project directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Projects Directory")
        if directory:
            self.dir_path.setText(directory)
            self.load_projects()

    def load_projects(self):
        """Load projects from the specified directory."""
        try:
            # Update PATHS with current directory
            PATHS["projects_dir"] = self.dir_path.text()

            # Load projects
            self.projects = load_all_projects()

            # Clear and populate tree
            self.project_list.clear()

            for project in self.projects:
                item = QTreeWidgetItem([
                    project.project_id,
                    str(len(project.reviews)),
                    "Ready"
                ])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Unchecked)
                item.setData(0, Qt.ItemDataRole.UserRole, project)

                self.project_list.addTopLevelItem(item)

            logger.info(f"Loaded {len(self.projects)} projects")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load projects: {str(e)}")


class ConfigTab(QWidget):
    """Tab for system configuration."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """Set up the configuration tab UI."""
        layout = QVBoxLayout()

        # LLM Configuration
        llm_group = QGroupBox("LLM Configuration")
        llm_layout = QFormLayout()

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["ollama", "claude", "chatgpt", "groq"])

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.model_edit = QLineEdit()
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 10000)
        self.max_tokens_spin.setValue(1000)

        llm_layout.addRow("Provider:", self.provider_combo)
        llm_layout.addRow("API Key:", self.api_key_edit)
        llm_layout.addRow("Model:", self.model_edit)
        llm_layout.addRow("Max Tokens:", self.max_tokens_spin)

        llm_group.setLayout(llm_layout)

        # General Settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()

        self.update_ontology_check = QCheckBox()
        self.generate_charts_check = QCheckBox()

        self.output_dir_edit = QLineEdit()

        general_layout.addRow("Update Ontology:", self.update_ontology_check)
        general_layout.addRow("Generate Charts:", self.generate_charts_check)
        general_layout.addRow("Output Directory:", self.output_dir_edit)

        general_group.setLayout(general_layout)

        # Layout assembly
        layout.addWidget(llm_group)
        layout.addWidget(general_group)
        layout.addStretch()

        self.setLayout(layout)

    def load_config(self):
        """Load configuration from config file."""
        try:
            # LLM Config
            current_provider = LLM_CONFIG.get("provider", "ollama")
            self.provider_combo.setCurrentText(current_provider)

            provider_config = LLM_CONFIG.get(current_provider, {})
            self.api_key_edit.setText(provider_config.get("api_key", ""))
            self.model_edit.setText(provider_config.get("model", ""))
            self.max_tokens_spin.setValue(
                provider_config.get("max_tokens", 1000))

            # General Settings
            self.update_ontology_check.setChecked(
                SETTINGS.get("update_ontology", False))
            self.generate_charts_check.setChecked(
                SETTINGS.get("generate_charts", True))
            self.output_dir_edit.setText(PATHS.get("output_dir", "output/"))

        except Exception as e:
            QMessageBox.warning(
                self, "Warning", f"Error loading configuration: {str(e)}")


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
        # Create tab widget with placeholder tabs
        central_widget.setLayout(layout)
        tab_widget = QTabWidget()

        # Add the ProjectTab as the first tab
        self.project_tab = ProjectTab(self)
        tab_widget.addTab(self.project_tab, "Projects")

        # Add the ConfigTab as the second tab
        self.config_tab = ConfigTab(self)
        tab_widget.addTab(self.config_tab, "Configuration")

        # Add placeholder tabs
        for name in ["Analysis", "Results"]:
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
