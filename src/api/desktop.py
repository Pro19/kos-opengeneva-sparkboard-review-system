import sys
import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QMessageBox, QFileDialog, QComboBox, QCheckBox, QSpinBox,
    QFormLayout, QProgressBar, QTableWidget, QTableWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# Import the existing modules
from src.core.project import load_all_projects
from src.infrastructure.config import PATHS, SETTINGS, LLM_CONFIG
from src.infrastructure.logging_utils import logger


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

        # Add instruction label
        instruction_label = QLabel(
            "✅ Check the projects you want to analyze, then click 'Analyze Selected Projects'")
        instruction_label.setStyleSheet(
            "color: #666; margin: 5px;")
        list_layout.addWidget(instruction_label)

        self.project_list = QTreeWidget()
        self.project_list.setHeaderLabels(["Project", "Reviews", "Status"])
        self.project_list.setAlternatingRowColors(True)

        list_layout.addWidget(self.project_list)
        list_group.setLayout(list_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)

        self.analyze_btn = QPushButton("🚀 Analyze Selected Projects")
        self.analyze_btn.clicked.connect(self.parent.start_analysis)

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

        # Save button
        save_layout = QHBoxLayout()
        self.save_config_btn = QPushButton("💾 Save Configuration")
        self.save_config_btn.clicked.connect(self.save_config)
        save_layout.addStretch()
        save_layout.addWidget(self.save_config_btn)

        # Layout assembly
        layout.addWidget(llm_group)
        layout.addWidget(general_group)
        layout.addLayout(save_layout)
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

    def save_config(self):
        """Save configuration changes."""
        try:
            import json
            import os

            # Update the global configuration dictionaries
            current_provider = self.provider_combo.currentText()
            LLM_CONFIG["provider"] = current_provider

            # Update provider-specific settings
            if current_provider not in LLM_CONFIG:
                LLM_CONFIG[current_provider] = {}

            LLM_CONFIG[current_provider]["api_key"] = self.api_key_edit.text()
            LLM_CONFIG[current_provider]["model"] = self.model_edit.text()
            LLM_CONFIG[current_provider]["max_tokens"] = self.max_tokens_spin.value()

            # Update general settings
            SETTINGS["update_ontology"] = self.update_ontology_check.isChecked()
            SETTINGS["generate_charts"] = self.generate_charts_check.isChecked()
            PATHS["output_dir"] = self.output_dir_edit.text()

            # Save to config.py (this is a simplified approach)
            # In a real application, you'd want to save to a separate config file
            QMessageBox.information(
                self, "Configuration Saved",
                "Configuration has been updated for this session.\n"
                "Note: Changes will be lost when the application is restarted.\n"
                "For permanent changes, modify config.py directly.")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration: {str(e)}")


class AnalysisTab(QWidget):
    """Tab for running analysis and monitoring progress."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Set up the analysis tab UI."""
        layout = QVBoxLayout()

        # Status group
        status_group = QGroupBox("Analysis Status")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("Ready to analyze projects")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        status_group.setLayout(status_layout)

        # Log output
        log_group = QGroupBox("Analysis Log")
        log_layout = QVBoxLayout()

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))

        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)

        # Control buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Analysis")
        self.stop_btn = QPushButton("Stop Analysis")
        self.clear_log_btn = QPushButton("Clear Log")

        self.start_btn.clicked.connect(self.parent.start_analysis)
        self.stop_btn.clicked.connect(self.parent.stop_analysis)
        self.clear_log_btn.clicked.connect(self.clear_log)

        self.stop_btn.setEnabled(False)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.clear_log_btn)

        # Layout assembly
        layout.addWidget(status_group)
        layout.addWidget(log_group, 1)
        layout.addLayout(control_layout)

        self.setLayout(layout)

    def add_log_message(self, message):
        """Add a message to the log output."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")

    def clear_log(self):
        """Clear the log output."""
        self.log_output.clear()

    def set_analysis_running(self, running):
        """Set the analysis running state."""
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.progress_bar.setVisible(running)

        if running:
            self.status_label.setText("Analysis in progress...")
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        else:
            self.status_label.setText("Analysis completed")
            self.progress_bar.setVisible(False)


class ResultsTab(QWidget):
    """Tab for viewing analysis results."""

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Set up the results tab UI."""
        layout = QVBoxLayout()

        # Results selection
        selection_group = QGroupBox("Analysis Results")
        selection_layout = QHBoxLayout()

        self.results_combo = QComboBox()
        self.refresh_results_btn = QPushButton("Refresh Results")
        self.refresh_results_btn.clicked.connect(self.refresh_results)
        self.results_combo.currentTextChanged.connect(
            self.load_project_results)

        selection_layout.addWidget(QLabel("Project:"))
        selection_layout.addWidget(self.results_combo)
        selection_layout.addWidget(self.refresh_results_btn)
        selection_layout.addStretch()

        selection_group.setLayout(selection_layout)

        # Results display
        display_group = QGroupBox("Project Results")
        display_layout = QVBoxLayout()

        # Create splitter for scores and report
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Scores table
        scores_widget = QWidget()
        scores_layout = QVBoxLayout()
        scores_layout.addWidget(QLabel("Feedback Scores:"))

        self.scores_table = QTableWidget()
        self.scores_table.setColumnCount(2)
        self.scores_table.setHorizontalHeaderLabels(["Dimension", "Score"])

        scores_layout.addWidget(self.scores_table)
        scores_widget.setLayout(scores_layout)

        # Report display
        report_widget = QWidget()
        report_layout = QVBoxLayout()
        report_layout.addWidget(QLabel("Final Review:"))

        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)

        report_layout.addWidget(self.report_display)
        report_widget.setLayout(report_layout)

        splitter.addWidget(scores_widget)
        splitter.addWidget(report_widget)
        splitter.setSizes([300, 500])

        display_layout.addWidget(splitter)
        display_group.setLayout(display_layout)

        # Layout assembly
        layout.addWidget(selection_group)
        layout.addWidget(display_group, 1)

        self.setLayout(layout)

        # Load initial results
        self.refresh_results()

    def refresh_results(self):
        """Refresh the list of available results."""
        import os
        import glob

        self.results_combo.clear()

        # Look for JSON feedback files in the results directory
        results_dir = "results/"
        if os.path.exists(results_dir):
            feedback_files = glob.glob(
                os.path.join(results_dir, "*_feedback.json"))
            for file_path in feedback_files:
                filename = os.path.basename(file_path)
                project_id = filename.replace("_feedback.json", "")
                self.results_combo.addItem(project_id)

    def load_project_results(self, project_id):
        """Load and display results for a specific project."""
        if not project_id:
            return

        import os
        import json

        try:
            # Load the feedback JSON file
            feedback_file = os.path.join(
                "results", f"{project_id}_feedback.json")
            if not os.path.exists(feedback_file):
                self.report_display.setPlainText(
                    f"No results found for project: {project_id}")
                return

            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)

            # Populate scores table
            feedback_scores = feedback_data.get("feedback_scores", {})
            self.scores_table.setRowCount(len(feedback_scores))

            row = 0
            for dimension, score in feedback_scores.items():
                if dimension != "overall_sentiment":  # Skip overall sentiment
                    dimension_name = dimension.replace("_", " ").title()
                    self.scores_table.setItem(
                        row, 0, QTableWidgetItem(dimension_name))
                    self.scores_table.setItem(
                        row, 1, QTableWidgetItem(str(score)))
                    row += 1

            self.scores_table.setRowCount(row)  # Adjust row count
            self.scores_table.resizeColumnsToContents()

            # Display final review
            final_review = feedback_data.get(
                "final_review", "No final review available.")
            self.report_display.setPlainText(final_review)

        except Exception as e:
            self.report_display.setPlainText(
                f"Error loading results: {str(e)}")
            logger.error(f"Error loading project results: {str(e)}")


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

        # Add the AnalysisTab as the third tab
        self.analysis_tab = AnalysisTab(self)
        tab_widget.addTab(self.analysis_tab, "Analysis")

        # Add the ResultsTab as the fourth tab
        self.results_tab = ResultsTab(self)
        tab_widget.addTab(self.results_tab, "Results")

        layout.addWidget(tab_widget)
        self.statusBar().showMessage("Ready")

        # Apply Material Design styling
        self.setStyleSheet(apply_material_style())

    def start_analysis(self):
        """Start the analysis of selected projects."""
        try:
            # Get selected projects
            selected_items = []
            root = self.project_tab.project_list.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                if item.checkState(0) == Qt.CheckState.Checked:
                    selected_items.append(item)

            if not selected_items:
                QMessageBox.warning(
                    self, "No Projects Selected", "Please select one or more projects to analyze.")
                return

            projects_to_analyze = [
                item.data(0, Qt.ItemDataRole.UserRole) for item in selected_items]

            # Update status and start analysis in a new thread
            self.analysis_tab.add_log_message(
                "Starting analysis of selected projects...")
            self.analysis_tab.set_analysis_running(True)

            # Update project status to "Analyzing"
            for item in selected_items:
                item.setText(2, "Analyzing...")

            # Real analysis process
            def run_analysis():
                try:
                    from src.core.ontology import Ontology
                    from src.core.reviewer import ReviewerProfile
                    from src.core.review import ReviewAnalyzer
                    from src.core.feedback import FeedbackGenerator
                    import os

                    # Initialize components
                    self.analysis_tab.add_log_message(
                        "Initializing analysis components...")
                    ontology = Ontology()
                    reviewer_profiler = ReviewerProfile(ontology)
                    review_analyzer = ReviewAnalyzer(
                        ontology, reviewer_profiler)
                    feedback_generator = FeedbackGenerator(ontology)

                    # Create output directory
                    output_dir = "results/"
                    os.makedirs(output_dir, exist_ok=True)

                    # Process each selected project
                    for i, project in enumerate(projects_to_analyze):
                        project_name = project.project_id
                        self.analysis_tab.add_log_message(
                            f"Processing project {i+1}/{len(projects_to_analyze)}: {project_name}")

                        # Step 1: Analyze reviews
                        self.analysis_tab.add_log_message(
                            f"  - Analyzing reviews for {project_name}")
                        review_analyzer.analyze_project_reviews(project)

                        # Step 2: Generate feedback report
                        self.analysis_tab.add_log_message(
                            f"  - Generating feedback report for {project_name}")
                        report_path = feedback_generator.generate_feedback_report(
                            project, output_dir)
                        self.analysis_tab.add_log_message(
                            f"  - Report saved to: {report_path}")

                        # Step 3: Generate visualization data
                        self.analysis_tab.add_log_message(
                            f"  - Generating visualization data for {project_name}")
                        viz_data = feedback_generator.visualize_feedback(
                            project)
                        viz_path = os.path.join(
                            output_dir, f"{project.project_id}_visualization.json")
                        with open(viz_path, 'w', encoding='utf-8') as f:
                            import json
                            json.dump(viz_data, f, indent=2)
                        self.analysis_tab.add_log_message(
                            f"  - Visualization data saved to: {viz_path}")

                    # Analysis completed
                    self.analysis_tab.add_log_message(
                        f"Analysis completed successfully for {len(projects_to_analyze)} project(s).")
                    logger.info("Analysis completed successfully.")

                    # Update project status to "Completed"
                    for item in selected_items:
                        item.setText(2, "Completed")

                    # Refresh results tab
                    self.results_tab.refresh_results()

                except Exception as e:
                    self.analysis_tab.add_log_message(
                        f"Error during analysis: {str(e)}")
                    logger.error(f"Error during analysis: {str(e)}")

                    # Update project status to "Error"
                    for item in selected_items:
                        item.setText(2, "Error")

                finally:
                    self.analysis_tab.set_analysis_running(False)

            # Run the analysis in a separate thread
            threading.Thread(target=run_analysis, daemon=True).start()

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to start analysis: {str(e)}")

    def stop_analysis(self):
        """Stop the analysis process."""
        # For now, just log and update the UI
        self.analysis_tab.add_log_message("Analysis stopped by user.")
        logger.info("Analysis stopped by user.")
        self.analysis_tab.set_analysis_running(False)


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
