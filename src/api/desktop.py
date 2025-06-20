"""
Modern Desktop GUI for OpenGeneva Sparkboard - Ontology-Driven Review System
Uses core modules directly (no API server required)
"""

import sys
import os
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QMessageBox, QComboBox, QCheckBox, QSpinBox, QFormLayout,
    QProgressBar, QTableWidget, QTableWidgetItem, QSplitter, QScrollArea,
    QFrame, QGridLayout, QPlainTextEdit, QListWidget, QListWidgetItem,
    QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor, QLinearGradient, QPainter, QBrush

# Import core modules directly
from src.core.ontology import Ontology
from src.core.project import Project, load_all_projects
from src.core.reviewer import ReviewerProfile
from src.core.review import ReviewAnalyzer
from src.core.feedback import FeedbackGenerator
from src.infrastructure.config import PATHS, SETTINGS
from src.infrastructure.logging_utils import logger


@dataclass
class SystemStatus:
    """System status data"""
    ontology_loaded: bool = False
    projects_dir: str = "projects"
    output_dir: str = "output"
    total_projects: int = 0
    total_reviews: int = 0
    last_update: Optional[datetime] = None


class ModernColors:
    """Modern color palette matching web UI"""
    PRIMARY = "#667eea"
    PRIMARY_DARK = "#764ba2"
    SURFACE = "#ffffff"
    BACKGROUND = "#f8fafc"
    CARD_BACKGROUND = "rgba(255, 255, 255, 0.95)"
    TEXT_PRIMARY = "#4a5568"
    TEXT_SECONDARY = "#666666"
    SUCCESS = "#22543d"
    ERROR = "#c53030"
    WARNING = "#d69e2e"


class GradientWidget(QWidget):
    """Widget with gradient background"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(ModernColors.PRIMARY))
        gradient.setColorAt(1, QColor(ModernColors.PRIMARY_DARK))
        painter.fillRect(self.rect(), QBrush(gradient))


class StatusCard(QFrame):
    """Modern status card widget"""
    
    def __init__(self, title: str, value: str = "0", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background: {ModernColors.CARD_BACKGROUND};
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                padding: 20px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {ModernColors.TEXT_SECONDARY}; font-size: 14px;")
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {ModernColors.TEXT_PRIMARY}; font-size: 28px; font-weight: bold;")
        
        # Subtitle
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(f"color: {ModernColors.TEXT_SECONDARY}; font-size: 12px;")
        
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_value(self, value: str, subtitle: str = None):
        self.value_label.setText(value)
        if subtitle:
            self.subtitle_label.setText(subtitle)


class ModernButton(QPushButton):
    """Modern styled button"""
    
    def __init__(self, text: str, primary: bool = True, parent=None):
        super().__init__(text, parent)
        self.primary = primary
        self.setMinimumHeight(40)
        self.update_style()
    
    def update_style(self):
        if self.primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {ModernColors.PRIMARY}, stop:1 {ModernColors.PRIMARY_DARK});
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #5a6fd8, stop:1 #6c4298);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4c5bc0, stop:1 #5d3a85);
                }}
                QPushButton:disabled {{
                    background: #e2e8f0;
                    color: #a0aec0;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: white;
                    color: {ModernColors.TEXT_PRIMARY};
                    border: 2px solid {ModernColors.PRIMARY};
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {ModernColors.PRIMARY};
                    color: white;
                }}
            """)


class CoreManager:
    """Manages core modules and system state"""
    
    def __init__(self):
        self.ontology = None
        self.projects = []
        self.status = SystemStatus()
        self.reviewer_profiler = None
        self.review_analyzer = None
        self.feedback_generator = None
        
        # Initialize from environment or defaults
        self.status.projects_dir = os.environ.get("SPARKBOARD_PROJECTS_DIR", "projects")
        self.status.output_dir = os.environ.get("SPARKBOARD_OUTPUT_DIR", "output")
        
        self.initialize_core()
    
    def initialize_core(self):
        """Initialize core modules"""
        try:
            # Set matplotlib to use non-interactive backend for thread safety
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            # Load ontology
            self.ontology = Ontology(load_existing=True)
            self.status.ontology_loaded = True
            
            # Initialize processing components
            self.reviewer_profiler = ReviewerProfile(self.ontology)
            self.review_analyzer = ReviewAnalyzer(self.ontology, self.reviewer_profiler)
            self.feedback_generator = FeedbackGenerator(self.ontology)
            
            logger.info("✅ Core modules initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize core modules: {e}")
            self.status.ontology_loaded = False
    
    def get_ontology_stats(self) -> Dict[str, Any]:
        """Get ontology statistics"""
        if self.ontology:
            return self.ontology.get_stats()
        return {"total_domains": 0, "total_dimensions": 0}
    
    def load_projects(self) -> List[Project]:
        """Load projects from directory"""
        try:
            # Update PATHS with current directory
            PATHS["projects_dir"] = self.status.projects_dir
            
            self.projects = load_all_projects()
            self.status.total_projects = len(self.projects)
            self.status.total_reviews = sum(len(p.reviews) for p in self.projects)
            self.status.last_update = datetime.now()
            
            logger.info(f"📂 Loaded {len(self.projects)} projects")
            return self.projects
            
        except Exception as e:
            logger.error(f"❌ Failed to load projects: {e}")
            return []
    
    def create_project(self, title: str, description: str, domain: str = None) -> bool:
        """Create a new project with proper markdown structure"""
        try:
            # Create project directory
            projects_dir = Path(self.status.projects_dir)
            projects_dir.mkdir(exist_ok=True)
            
            # Generate project ID (clean filename)
            project_id = title.lower().replace(" ", "-").replace("/", "-")
            project_id = "".join(c for c in project_id if c.isalnum() or c in "-_")
            project_dir = projects_dir / project_id
            project_dir.mkdir(exist_ok=True)
            
            # Create description.md file with proper markdown structure
            desc_file = project_dir / "description.md"
            desc_content = f"""# Project Name

{title}

## Project Description (max 400 words)

{description}

## Hackathon ID

hackathon-2024

## Explain the work you've done so far

Work in progress. This project was created via the desktop GUI.
"""
            
            if domain:
                desc_content += f"\n## Domain\n\n{domain}\n"
            
            desc_file.write_text(desc_content)
            
            logger.info(f"✅ Created project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create project: {e}")
            return False
    
    def submit_review(self, project: Project, reviewer_name: str, reviewer_expertise: str, content: str) -> bool:
        """Submit a review for a project with proper markdown structure"""
        try:
            # Create review file with proper naming
            project_dir = Path(self.status.projects_dir) / project.project_id
            review_files = list(project_dir.glob("review*.md"))
            review_num = len(review_files) + 1
            
            review_file = project_dir / f"review{review_num}.md"
            
            # Create review content with expected markdown structure
            review_content = f"""# Reviewer name

{reviewer_name}

## Text review of the project (max 400 words)

{content}

## Confidence score (0-100) _How much confidence do you have in your own review?_

85

## Links

- Reviewer expertise: {reviewer_expertise}
- Submitted via: Desktop GUI
- Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            review_file.write_text(review_content)
            
            logger.info(f"✅ Submitted review for project: {project.project_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to submit review: {e}")
            return False
    
    def process_project(self, project: Project, progress_callback=None) -> Dict[str, Any]:
        """Process a project through the analysis pipeline (same as CLI)"""
        try:
            if not self.status.ontology_loaded:
                raise Exception("Ontology not loaded")
            
            results = {}
            
            if progress_callback:
                progress_callback("Analyzing reviewer profiles...", 20)
            
            # Step 1: Get reviewer insights before processing
            initial_insights = self.reviewer_profiler.get_reviewer_insights(project)
            logger.info(f"Initial reviewer analysis: {initial_insights['total_reviewers']} reviewers across {len(initial_insights['domain_coverage'])} domains")
            results["reviewer_insights"] = initial_insights
            
            if progress_callback:
                progress_callback("Analyzing reviews with RDF ontology...", 40)
            
            # Step 2: Analyze all reviews for the project using RDF ontology
            self.review_analyzer.analyze_project_reviews(project)
            
            if progress_callback:
                progress_callback("Generating feedback report...", 60)
            
            # Step 3: Generate feedback report with dynamic dimensions (same as CLI)
            output_dir = self.status.output_dir
            feedback_report_path = self.feedback_generator.generate_feedback_report(project, output_dir)
            results["feedback_report_path"] = feedback_report_path
            
            if progress_callback:
                progress_callback("Saving additional results...", 80)
            
            # Step 4: Save additional metadata
            self.save_additional_results(project, initial_insights)
            
            if progress_callback:
                progress_callback("Analysis completed!", 100)
            
            logger.info(f"✅ Successfully processed project: {project.project_id}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to process project: {e}")
            if progress_callback:
                progress_callback(f"Error: {e}", 0)
            raise e
    
    def save_additional_results(self, project: Project, initial_insights):
        """Save additional metadata (the main report is saved by FeedbackGenerator)"""
        try:
            # Create output directory
            output_dir = Path(self.status.output_dir)
            output_dir.mkdir(exist_ok=True)
            
            project_output_dir = output_dir / project.project_id
            project_output_dir.mkdir(exist_ok=True)
            
            # Save reviewer insights
            insights_file = project_output_dir / "reviewer_insights.json"
            with open(insights_file, 'w') as f:
                json.dump(initial_insights, f, indent=2, default=str)
            
            # Save project metadata
            metadata = {
                "project_id": project.project_id,
                "project_data": project.project_data,
                "total_reviews": len(project.reviews),
                "human_reviews": len([r for r in project.reviews if not r.get("is_artificial", False)]),
                "analysis_timestamp": datetime.now().isoformat(),
                "feedback_scores": getattr(project, 'feedback_scores', {}),
                "domain_relevance_scores": getattr(project, 'domain_relevance_scores', {})
            }
            
            metadata_file = project_output_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"💾 Saved additional results to: {project_output_dir}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save additional results: {e}")
    
    def get_project_results(self, project: Project) -> Dict[str, Any]:
        """Get saved results for a project"""
        try:
            # Try to load the main feedback report (markdown)
            results_file = Path(self.status.output_dir) / project.project_id / f"{project.project_id}_feedback.md"
            if results_file.exists():
                results = {
                    "feedback_report_md": results_file.read_text(),
                    "has_results": True
                }
                
                # Try to load JSON metadata if available
                json_file = Path(self.status.output_dir) / project.project_id / f"{project.project_id}_feedback.json"
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        json_data = json.load(f)
                        results.update(json_data)
                
                # Try to load additional metadata
                metadata_file = Path(self.status.output_dir) / project.project_id / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        results["metadata"] = metadata
                
                return results
            else:
                return {"has_results": False}
                
        except Exception as e:
            logger.error(f"❌ Failed to load results: {e}")
            return {"has_results": False, "error": str(e)}


class SystemStatusWidget(QFrame):
    """System status indicator"""
    
    def __init__(self, core_manager: CoreManager, parent=None):
        super().__init__(parent)
        self.core_manager = core_manager
        self.setup_ui()
        
        # Setup timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(10000)  # Update every 10 seconds
        
        self.update_status()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.ontology_icon = QLabel("●")
        self.ontology_text = QLabel("Ontology")
        
        self.projects_text = QLabel("Projects: 0")
        
        layout.addWidget(QLabel("System Status:"))
        layout.addWidget(self.ontology_icon)
        layout.addWidget(self.ontology_text)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.projects_text)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_status(self):
        """Update status display"""
        status = self.core_manager.status
        
        # Ontology status
        if status.ontology_loaded:
            self.ontology_icon.setStyleSheet(f"color: {ModernColors.SUCCESS}; font-size: 16px;")
            self.ontology_text.setText("Ontology Loaded")
            self.ontology_text.setStyleSheet(f"color: {ModernColors.SUCCESS};")
        else:
            self.ontology_icon.setStyleSheet(f"color: {ModernColors.ERROR}; font-size: 16px;")
            self.ontology_text.setText("Ontology Error")
            self.ontology_text.setStyleSheet(f"color: {ModernColors.ERROR};")
        
        # Projects status
        self.projects_text.setText(f"Projects: {status.total_projects} | Reviews: {status.total_reviews}")


class DashboardTab(QWidget):
    """Dashboard tab with statistics and overview"""
    
    def __init__(self, core_manager: CoreManager, parent=None):
        super().__init__(parent)
        self.core_manager = core_manager
        self.setup_ui()
        self.refresh_stats()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("OpenGeneva Sparkboard")
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {ModernColors.TEXT_PRIMARY};
            margin-bottom: 10px;
        """)
        
        subtitle = QLabel("Ontology-driven review system")
        subtitle.setStyleSheet(f"color: {ModernColors.TEXT_SECONDARY}; font-size: 16px;")
        
        refresh_btn = ModernButton("🔄 Refresh", primary=False)
        refresh_btn.clicked.connect(self.refresh_stats)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        
        # Stats cards
        self.stats_layout = QGridLayout()
        self.stats_layout.setSpacing(15)
        
        self.projects_card = StatusCard("Total Projects", "0", "In projects directory")
        self.reviews_card = StatusCard("Total Reviews", "0", "Submitted reviews") 
        self.domains_card = StatusCard("Domains", "0", "Knowledge domains")
        self.dimensions_card = StatusCard("Dimensions", "0", "Evaluation dimensions")
        
        self.stats_layout.addWidget(self.projects_card, 0, 0)
        self.stats_layout.addWidget(self.reviews_card, 0, 1)
        self.stats_layout.addWidget(self.domains_card, 0, 2)
        self.stats_layout.addWidget(self.dimensions_card, 0, 3)
        
        # System info
        info_group = QGroupBox("System Information")
        info_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 16px;
                color: {ModernColors.TEXT_PRIMARY};
                border: 2px solid {ModernColors.PRIMARY};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        
        info_layout = QVBoxLayout()
        self.info_display = QPlainTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setMaximumHeight(150)
        self.info_display.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background: transparent;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        
        info_layout.addWidget(self.info_display)
        info_group.setLayout(info_layout)
        
        # Layout assembly
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(self.stats_layout)
        layout.addWidget(info_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def refresh_stats(self):
        """Refresh statistics from core modules"""
        try:
            # Load projects (synchronous - this is fast)
            projects = self.core_manager.load_projects()
            
            # Get ontology stats (synchronous - this is fast)
            ontology_stats = self.core_manager.get_ontology_stats()
            
            # Update display
            self.update_stats_display(projects, ontology_stats)
            
        except Exception as e:
            logger.error(f"Failed to refresh stats: {e}")
            self.update_system_info()
    
    def update_stats_display(self, projects: List, ontology_stats: Dict):
        """Update stats display"""
        # Update cards
        self.projects_card.update_value(str(len(projects)))
        total_reviews = sum(len(p.reviews) for p in projects)
        self.reviews_card.update_value(str(total_reviews))
        self.domains_card.update_value(str(ontology_stats.get('total_domains', 0)))
        self.dimensions_card.update_value(str(ontology_stats.get('total_dimensions', 0)))
        
        # Update system info
        self.update_system_info()
    
    def update_system_info(self):
        """Update system information display"""
        status = self.core_manager.status
        info_text = f"""Projects Directory: {status.projects_dir}
Output Directory: {status.output_dir}
Ontology Status: {'✅ Loaded' if status.ontology_loaded else '❌ Error'}
Last Update: {status.last_update.strftime('%Y-%m-%d %H:%M:%S') if status.last_update else 'Never'}
Core Modules: {'✅ Ready' if self.core_manager.reviewer_profiler else '❌ Not Ready'}"""
        
        self.info_display.setPlainText(info_text)


class ProjectsTab(QWidget):
    """Projects management tab"""
    
    project_created = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, core_manager: CoreManager, parent=None):
        super().__init__(parent)
        self.core_manager = core_manager
        self.setup_ui()
        self.refresh_projects()
        
        # Connect signal
        self.project_created.connect(self.on_project_created)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with actions
        header_layout = QHBoxLayout()
        
        title = QLabel("Project Management")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ModernColors.TEXT_PRIMARY};")
        
        # Directory controls with info
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Projects Directory:"))
        
        self.dir_path = QLineEdit(self.core_manager.status.projects_dir)
        self.dir_browse_btn = ModernButton("📁 Browse", primary=False)
        self.dir_browse_btn.clicked.connect(self.browse_directory)
        
        # Add info about expected structure
        info_btn = ModernButton("ℹ️ Structure", primary=False)
        info_btn.clicked.connect(self.show_structure_info)
        
        dir_layout.addWidget(self.dir_path, 1)
        dir_layout.addWidget(self.dir_browse_btn)
        dir_layout.addWidget(info_btn)
        
        self.refresh_btn = ModernButton("🔄 Refresh", primary=False)
        self.refresh_btn.clicked.connect(self.refresh_projects)
        
        self.new_project_btn = ModernButton("➕ New Project")
        self.new_project_btn.clicked.connect(self.show_new_project_dialog)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        header_layout.addWidget(self.new_project_btn)
        
        # Projects table
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(4)
        self.projects_table.setHorizontalHeaderLabels([
            "Project ID", "Description", "Reviews", "Status"
        ])
        self.projects_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e2e8f0;
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f7fafc;
            }
            QTableWidget::item:selected {
                background-color: #e6fffa;
            }
            QHeaderView::section {
                background-color: #f7fafc;
                padding: 12px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Layout assembly
        layout.addLayout(header_layout)
        layout.addLayout(dir_layout)
        layout.addWidget(self.projects_table)
        
        self.setLayout(layout)
    
    def browse_directory(self):
        """Browse for projects directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Projects Directory", self.core_manager.status.projects_dir)
        if directory:
            self.dir_path.setText(directory)
            self.core_manager.status.projects_dir = directory
            self.refresh_projects()
    
    def refresh_projects(self):
        """Refresh projects from directory"""
        try:
            # Update projects directory
            self.core_manager.status.projects_dir = self.dir_path.text()
            
            # Load projects (synchronous - this is fast)
            projects = self.core_manager.load_projects()
            self.update_projects_table(projects)
            
        except Exception as e:
            logger.error(f"Failed to refresh projects: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load projects: {e}")
    
    def update_projects_table(self, projects: List[Project]):
        """Update the projects table"""
        self.projects_table.setRowCount(len(projects))
        
        for row, project in enumerate(projects):
            # Project ID
            self.projects_table.setItem(row, 0, QTableWidgetItem(project.project_id))
            
            # Description (from proper markdown structure)
            desc = project.project_data.get("description", "No description found")
            if len(desc) > 100:
                desc = desc[:100] + "..."
            self.projects_table.setItem(row, 1, QTableWidgetItem(desc))
            
            # Reviews count (only .md files)
            reviews_count = len(project.reviews)
            self.projects_table.setItem(row, 2, QTableWidgetItem(str(reviews_count)))
            
            # Status (check for proper markdown structure)
            if not project.project_data.get("description"):
                status = "⚠️ No description.md"
            elif reviews_count == 0:
                status = "📝 No reviews"
            else:
                status = "✅ Ready for Analysis"
            self.projects_table.setItem(row, 3, QTableWidgetItem(status))
        
        self.projects_table.resizeColumnsToContents()
    
    def show_new_project_dialog(self):
        """Show new project creation dialog"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Project")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Form fields
        form_layout = QFormLayout()
        
        title_edit = QLineEdit()
        title_edit.setPlaceholderText("Enter project title")
        
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText("Enter project description")
        desc_edit.setMaximumHeight(150)
        
        domain_combo = QComboBox()
        domain_combo.addItems(["healthcare", "fintech", "sustainability", "education", "other"])
        
        form_layout.addRow("Title*:", title_edit)
        form_layout.addRow("Description*:", desc_edit)
        form_layout.addRow("Domain:", domain_combo)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if title_edit.text() and desc_edit.toPlainText():
                self.create_project(
                    title_edit.text(),
                    desc_edit.toPlainText(),
                    domain_combo.currentText()
                )
            else:
                QMessageBox.warning(self, "Error", "Please fill in all required fields")
    
    def create_project(self, title: str, description: str, domain: str):
        """Create a new project"""
        def run_create():
            try:
                success = self.core_manager.create_project(title, description, domain)
                if success:
                    # Use signal to update GUI safely
                    self.project_created.emit(True, "Project created successfully!")
                else:
                    self.project_created.emit(False, "Failed to create project")
            except Exception as e:
                logger.error(f"Failed to create project: {e}")
                self.project_created.emit(False, f"Failed to create project: {e}")
        
        threading.Thread(target=run_create, daemon=True).start()
    
    def on_project_created(self, success: bool, message: str):
        """Handle project creation result"""
        if success:
            QMessageBox.information(self, "Success", message)
            self.refresh_projects()
        else:
            QMessageBox.warning(self, "Error", message)
    
    def show_structure_info(self):
        """Show information about expected project structure"""
        info_text = """Expected Project Structure:

projects/
├── project-name/
│   ├── description.md     # Required
│   ├── review1.md         # At least one required
│   ├── review2.md
│   └── ...

Description.md format:
- # Project Name
- ## Project Description (max 400 words)
- ## Hackathon ID
- ## Explain the work you've done so far

Review.md format:
- # Reviewer name
- ## Text review of the project (max 400 words)
- ## Confidence score (0-100)
- ## Links

This matches the existing markdown structure used by the CLI and web interfaces."""
        
        QMessageBox.information(self, "Project Structure", info_text)


class ReviewsTab(QWidget):
    """Reviews management tab"""
    
    review_submitted = pyqtSignal(bool, str)  # success, message
    projects_loaded = pyqtSignal(list)  # projects list
    
    def __init__(self, core_manager: CoreManager, parent=None):
        super().__init__(parent)
        self.core_manager = core_manager
        self.selected_project = None
        self.setup_ui()
        self.refresh_projects()
        
        # Connect signals
        self.review_submitted.connect(self.on_review_submitted)
        self.projects_loaded.connect(self.update_projects_combo)
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        title = QLabel("Submit Reviews")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ModernColors.TEXT_PRIMARY};")
        
        # Project selection
        project_group = QGroupBox("Select Project")
        project_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {ModernColors.TEXT_PRIMARY};
                border: 2px solid {ModernColors.PRIMARY};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }}
        """)
        
        project_layout = QHBoxLayout()
        
        self.project_combo = QComboBox()
        self.project_combo.setMinimumHeight(40)
        self.project_combo.currentTextChanged.connect(self.on_project_selected)
        
        refresh_projects_btn = ModernButton("🔄 Refresh", primary=False)
        refresh_projects_btn.clicked.connect(self.refresh_projects)
        
        project_layout.addWidget(QLabel("Project:"))
        project_layout.addWidget(self.project_combo, 1)
        project_layout.addWidget(refresh_projects_btn)
        project_group.setLayout(project_layout)
        
        # Review form
        self.review_group = QGroupBox("Submit Review")
        self.review_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {ModernColors.TEXT_PRIMARY};
                border: 2px solid {ModernColors.PRIMARY};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }}
        """)
        self.review_group.setEnabled(False)
        
        review_layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.reviewer_name = QLineEdit()
        self.reviewer_name.setPlaceholderText("Your name")
        
        self.reviewer_expertise = QComboBox()
        self.reviewer_expertise.addItems([
            "healthcare", "fintech", "sustainability", "education", 
            "AI/ML", "blockchain", "mobile", "web", "other"
        ])
        
        self.review_text = QTextEdit()
        self.review_text.setPlaceholderText("Enter your detailed review here...")
        self.review_text.setMinimumHeight(150)
        
        form_layout.addRow("Reviewer Name*:", self.reviewer_name)
        form_layout.addRow("Expertise Domain:", self.reviewer_expertise)
        form_layout.addRow("Review Text*:", self.review_text)
        
        # Submit button
        submit_layout = QHBoxLayout()
        self.submit_btn = ModernButton("📝 Submit Review")
        self.submit_btn.clicked.connect(self.submit_review)
        submit_layout.addStretch()
        submit_layout.addWidget(self.submit_btn)
        
        review_layout.addLayout(form_layout)
        review_layout.addLayout(submit_layout)
        self.review_group.setLayout(review_layout)
        
        # Layout assembly
        layout.addWidget(title)
        layout.addWidget(project_group)
        layout.addWidget(self.review_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def refresh_projects(self):
        """Refresh projects list"""
        try:
            projects = self.core_manager.load_projects()
            self.update_projects_combo(projects)
        except Exception as e:
            logger.error(f"Failed to refresh projects: {e}")
    
    def update_projects_combo(self, projects: List[Project]):
        """Update projects combo box"""
        self.project_combo.clear()
        self.project_combo.addItem("-- Select a project --", None)
        
        for project in projects:
            # Only show projects with proper description structure
            if project.project_data.get("description"):
                project_name = project.project_data.get("name", project.project_id)
                reviews_count = len(project.reviews)
                display_text = f"{project_name} ({reviews_count} reviews)"
                self.project_combo.addItem(display_text, project)
            else:
                # Show problematic projects but mark them
                display_text = f"⚠️ {project.project_id} (no description.md)"
                self.project_combo.addItem(display_text, None)  # Don't allow selection
    
    def on_project_selected(self):
        """Handle project selection"""
        current_data = self.project_combo.currentData()
        self.selected_project = current_data
        self.review_group.setEnabled(current_data is not None)
    
    def submit_review(self):
        """Submit review"""
        if not self.selected_project:
            QMessageBox.warning(self, "Error", "Please select a project first")
            return
        
        if not self.reviewer_name.text() or not self.review_text.toPlainText():
            QMessageBox.warning(self, "Error", "Please fill in all required fields")
            return
        
        def run_submit():
            try:
                success = self.core_manager.submit_review(
                    self.selected_project,
                    self.reviewer_name.text(),
                    self.reviewer_expertise.currentText(),
                    self.review_text.toPlainText()
                )
                
                if success:
                    self.review_submitted.emit(True, "Review submitted successfully!")
                else:
                    self.review_submitted.emit(False, "Failed to submit review")
            except Exception as e:
                logger.error(f"Failed to submit review: {e}")
                self.review_submitted.emit(False, f"Failed to submit review: {e}")
        
        threading.Thread(target=run_submit, daemon=True).start()
    
    def on_review_submitted(self, success: bool, message: str):
        """Handle review submission result"""
        if success:
            QMessageBox.information(self, "Success", message)
            self.clear_form()
            self.refresh_projects()  # Refresh to show updated review count
        else:
            QMessageBox.warning(self, "Error", message)
    
    def clear_form(self):
        """Clear the review form"""
        self.reviewer_name.clear()
        self.review_text.clear()
        self.reviewer_expertise.setCurrentIndex(0)


class ResultsLoadingThread(QThread):
    """Thread for loading results without blocking UI"""
    
    results_loaded = pyqtSignal(dict, str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, core_manager: CoreManager, project: Project):
        super().__init__()
        self.core_manager = core_manager
        self.project = project
    
    def run(self):
        """Load results in background thread"""
        try:
            results = self.core_manager.get_project_results(self.project)
            self.results_loaded.emit(results, self.project.project_id)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ProcessingThread(QThread):
    """Thread for background processing"""
    
    progress_updated = pyqtSignal(str, int)
    finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, core_manager: CoreManager, project: Project):
        super().__init__()
        self.core_manager = core_manager
        self.project = project
    
    def run(self):
        """Run the processing"""
        try:
            def progress_callback(message, progress):
                self.progress_updated.emit(message, progress)
            
            results = self.core_manager.process_project(self.project, progress_callback)
            self.finished.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    """Thread for background processing"""
    
    progress_updated = pyqtSignal(str, int)
    finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, core_manager: CoreManager, project: Project):
        super().__init__()
        self.core_manager = core_manager
        self.project = project
    
    def run(self):
        """Run the processing"""
        try:
            def progress_callback(message, progress):
                self.progress_updated.emit(message, progress)
            
            results = self.core_manager.process_project(self.project, progress_callback)
            self.finished.emit(results)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class AnalysisTab(QWidget):
    """Analysis processing tab"""
    
    def __init__(self, core_manager: CoreManager, parent=None):
        super().__init__(parent)
        self.core_manager = core_manager
        self.processing_thread = None
        self.setup_ui()
        self.refresh_projects()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        title = QLabel("Analysis & Processing")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ModernColors.TEXT_PRIMARY};")
        
        # Project selection
        selection_layout = QHBoxLayout()
        
        self.analysis_project_combo = QComboBox()
        self.analysis_project_combo.setMinimumHeight(40)
        
        refresh_btn = ModernButton("🔄 Refresh", primary=False)
        refresh_btn.clicked.connect(self.refresh_projects)
        
        self.process_btn = ModernButton("🚀 Start Analysis")
        self.process_btn.clicked.connect(self.start_analysis)
        
        selection_layout.addWidget(QLabel("Select Project:"))
        selection_layout.addWidget(self.analysis_project_combo, 1)
        selection_layout.addWidget(refresh_btn)
        selection_layout.addWidget(self.process_btn)
        
        # Progress section
        progress_group = QGroupBox("Analysis Progress")
        progress_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {ModernColors.TEXT_PRIMARY};
                border: 2px solid {ModernColors.PRIMARY};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }}
        """)
        
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                text-align: center;
                background-color: #f7fafc;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ModernColors.PRIMARY}, stop:1 {ModernColors.PRIMARY_DARK});
                border-radius: 6px;
            }}
        """)
        
        self.status_label = QLabel("Ready to start analysis")
        self.status_label.setStyleSheet(f"color: {ModernColors.TEXT_SECONDARY}; font-style: italic;")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_group.setLayout(progress_layout)
        
        # Logs section
        logs_group = QGroupBox("Analysis Logs")
        logs_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {ModernColors.TEXT_PRIMARY};
                border: 2px solid {ModernColors.PRIMARY};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }}
        """)
        
        logs_layout = QVBoxLayout()
        
        self.logs_display = QPlainTextEdit()
        self.logs_display.setReadOnly(True)
        self.logs_display.setMaximumHeight(200)
        self.logs_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a202c;
                color: #e2e8f0;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        
        logs_layout.addWidget(self.logs_display)
        logs_group.setLayout(logs_layout)
        
        # Layout assembly
        layout.addWidget(title)
        layout.addLayout(selection_layout)
        layout.addWidget(progress_group)
        layout.addWidget(logs_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def refresh_projects(self):
        """Refresh projects list"""
        try:
            projects = self.core_manager.load_projects()
            self.update_analysis_combo(projects)
        except Exception as e:
            logger.error(f"Failed to refresh projects: {e}")
    
    def update_analysis_combo(self, projects: List[Project]):
        """Update analysis projects combo"""
        self.analysis_project_combo.clear()
        self.analysis_project_combo.addItem("-- Select a project --", None)
        
        for project in projects:
            reviews_count = len(project.reviews)
            # Only show projects with reviews and proper description
            if reviews_count > 0 and project.project_data.get("description"):
                display_text = f"{project.project_id} ({reviews_count} reviews)"
                self.analysis_project_combo.addItem(display_text, project)
    
    def start_analysis(self):
        """Start analysis process"""
        selected_project = self.analysis_project_combo.currentData()
        if not selected_project:
            QMessageBox.warning(self, "Error", "Please select a project first")
            return
        
        if not self.core_manager.status.ontology_loaded:
            QMessageBox.warning(
                self, 
                "Error", 
                "Ontology not loaded. Cannot start analysis.\n\n"
                "Check the Dashboard tab for ontology status."
            )
            return
        
        # Check if project has proper structure
        if not selected_project.project_data.get("description"):
            QMessageBox.warning(
                self,
                "Error", 
                "Selected project doesn't have proper description.md structure.\n\n"
                "Please check the Projects tab for structure information."
            )
            return
        
        self.process_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.logs_display.clear()
        
        # Start processing thread
        self.processing_thread = ProcessingThread(self.core_manager, selected_project)
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.finished.connect(self.analysis_finished)
        self.processing_thread.error_occurred.connect(self.analysis_error)
        self.processing_thread.start()
    
    def update_progress(self, message: str, progress: int):
        """Update progress display"""
        self.status_label.setText(message)
        self.progress_bar.setValue(progress)
        self.add_log(message)
    
    def analysis_finished(self, results: Dict):
        """Handle analysis completion"""
        self.add_log("✅ Analysis completed successfully!")
        self.progress_bar.setValue(100)
        self.status_label.setText("Analysis completed")
        self.process_btn.setEnabled(True)
        QMessageBox.information(self, "Success", "Analysis completed successfully!")
    
    def analysis_error(self, error_message: str):
        """Handle analysis error"""
        self.add_log(f"❌ Error: {error_message}")
        self.status_label.setText("Analysis failed")
        self.process_btn.setEnabled(True)
        QMessageBox.warning(self, "Error", f"Analysis failed: {error_message}")
    
    def add_log(self, message: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.logs_display.appendPlainText(log_message)


class ResultsTab(QWidget):
    """Results viewing tab"""
    
    def __init__(self, core_manager: CoreManager, parent=None):
        super().__init__(parent)
        self.core_manager = core_manager
        self.loading_thread = None
        self.setup_ui()
        self.refresh_projects()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        title = QLabel("Analysis Results")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {ModernColors.TEXT_PRIMARY};")
        
        # Project selection
        selection_layout = QHBoxLayout()
        
        self.results_project_combo = QComboBox()
        self.results_project_combo.setMinimumHeight(40)
        self.results_project_combo.currentTextChanged.connect(self.on_project_selection_changed)
        
        refresh_btn = ModernButton("🔄 Refresh", primary=False)
        refresh_btn.clicked.connect(self.refresh_projects)
        
        open_folder_btn = ModernButton("📁 Open Results Folder", primary=False)
        open_folder_btn.clicked.connect(self.open_results_folder)
        
        selection_layout.addWidget(QLabel("Select Project:"))
        selection_layout.addWidget(self.results_project_combo, 1)
        selection_layout.addWidget(refresh_btn)
        selection_layout.addWidget(open_folder_btn)
        
        # Loading indicator
        self.loading_label = QLabel("Select a project to view results")
        self.loading_label.setStyleSheet(f"color: {ModernColors.TEXT_SECONDARY}; font-style: italic; text-align: center;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        
        # Layout assembly
        layout.addWidget(title)
        layout.addLayout(selection_layout)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.results_display, 1)
        
        self.setLayout(layout)
    
    def refresh_projects(self):
        """Refresh projects list"""
        try:
            projects = self.core_manager.load_projects()
            self.update_results_combo(projects)
        except Exception as e:
            logger.error(f"Failed to refresh projects: {e}")
            QMessageBox.warning(self, "Error", f"Failed to refresh projects: {e}")
    
    def update_results_combo(self, projects: List[Project]):
        """Update results projects combo"""
        self.results_project_combo.clear()
        self.results_project_combo.addItem("-- Select a project --", None)
        
        for project in projects:
            # Check if results exist
            results_file = Path(self.core_manager.status.output_dir) / project.project_id / f"{project.project_id}_feedback.md"
            
            if results_file.exists():
                # Has results
                self.results_project_combo.addItem(f"✅ {project.project_id} (analyzed)", project)
            elif project.project_data.get("description") and len(project.reviews) > 0:
                # Ready for analysis but no results yet
                self.results_project_combo.addItem(f"📊 {project.project_id} (ready)", project)
            else:
                # Not ready or no proper structure
                self.results_project_combo.addItem(f"⚠️ {project.project_id} (incomplete)", project)
    
    def on_project_selection_changed(self):
        """Handle project selection change"""
        selected_project = self.results_project_combo.currentData()
        if not selected_project:
            self.results_display.clear()
            self.loading_label.setText("Select a project to view results")
            return
        
        self.load_results(selected_project)
    
    def load_results(self, project: Project):
        """Load results for selected project using background thread"""
        # Show loading state
        self.loading_label.setText("Loading results...")
        self.results_display.clear()
        
        # Stop any existing loading thread
        if self.loading_thread and self.loading_thread.isRunning():
            self.loading_thread.quit()
            self.loading_thread.wait()
        
        # Start new loading thread
        self.loading_thread = ResultsLoadingThread(self.core_manager, project)
        self.loading_thread.results_loaded.connect(self.on_results_loaded)
        self.loading_thread.error_occurred.connect(self.on_results_error)
        self.loading_thread.start()
    
    def on_results_loaded(self, results: Dict, project_id: str):
        """Handle results loaded signal (runs on main thread)"""
        self.loading_label.setText("")
        self.display_results(results, project_id)
    
    def on_results_error(self, error_message: str):
        """Handle results loading error (runs on main thread)"""
        self.loading_label.setText("Error loading results")
        self.results_display.setPlainText(f"Error loading results: {error_message}")
        logger.error(f"Failed to load results: {error_message}")
    
    def display_results(self, results: Dict, project_id: str):
        """Display results in formatted view (runs on main thread)"""
        if not results.get("has_results", False):
            self.results_display.setPlainText(
                f"No results available for project: {project_id}\n\n"
                "Please run analysis first in the Analysis tab.\n\n"
                "The system expects:\n"
                "- Project with description.md file\n"
                "- At least one review*.md file\n"
                "- Analysis completed successfully"
            )
            return
        
        # Check if we have the markdown report
        if "feedback_report_md" in results:
            # Display the markdown report directly (it's already well-formatted)
            markdown_content = results["feedback_report_md"]
            
            # Convert some markdown to HTML for better display
            html_content = markdown_content.replace("# ", "<h1>").replace("\n", "<br>")
            html_content = html_content.replace("## ", "<h2>").replace("### ", "<h3>")
            html_content = html_content.replace("**", "<b>").replace("**", "</b>")
            
            # Add some styling
            styled_html = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: {ModernColors.TEXT_PRIMARY};">
            <h2 style="color: {ModernColors.PRIMARY};">📊 Analysis Results for {project_id}</h2>
            <hr style="margin: 20px 0; border: 1px solid #e2e8f0;">
            
            {html_content}
            
            <hr style="margin: 20px 0; border: 1px solid #e2e8f0;">
            <p style="color: {ModernColors.TEXT_SECONDARY}; font-size: 12px;">
            Results saved in: {self.core_manager.status.output_dir}/{project_id}/
            </p>
            </div>
            """
            
            self.results_display.setHtml(styled_html)
        else:
            # Fallback to basic display if no markdown available
            self.results_display.setPlainText(f"Results loaded for {project_id}, but report format not recognized.")
            
        # Log what we found
        if "metadata" in results:
            metadata = results["metadata"]
            logger.info(f"Loaded results: {metadata.get('total_reviews', 0)} reviews, analysis: {metadata.get('analysis_timestamp', 'unknown')}")
    
    def open_results_folder(self):
        """Open results folder in file explorer"""
        selected_project = self.results_project_combo.currentData()
        if not selected_project:
            QMessageBox.warning(self, "Error", "Please select a project first")
            return
        
        results_folder = Path(self.core_manager.status.output_dir) / selected_project.project_id
        
        if results_folder.exists():
            import subprocess
            import platform
            
            try:
                if platform.system() == "Windows":
                    subprocess.run(["explorer", str(results_folder)])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(results_folder)])
                else:  # Linux
                    subprocess.run(["xdg-open", str(results_folder)])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open folder: {e}")
        else:
            QMessageBox.information(self, "Info", "No results folder found for this project")


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.core_manager = CoreManager()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the main UI"""
        self.setWindowTitle("OpenGeneva Sparkboard - Desktop Client v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply modern styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {ModernColors.BACKGROUND};
            }}
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: white;
                color: {ModernColors.TEXT_PRIMARY};
                padding: 15px 25px;
                margin-right: 2px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-weight: 600;
                font-size: 14px;
                min-width: 120px;
                border: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ModernColors.PRIMARY}, stop:1 {ModernColors.PRIMARY_DARK});
                color: white;
                border: 2px solid {ModernColors.PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {ModernColors.SURFACE};
                border: 2px solid {ModernColors.PRIMARY};
            }}
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Status widget
        self.system_status = SystemStatusWidget(self.core_manager)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.dashboard_tab = DashboardTab(self.core_manager)
        self.projects_tab = ProjectsTab(self.core_manager)
        self.reviews_tab = ReviewsTab(self.core_manager)
        self.analysis_tab = AnalysisTab(self.core_manager)
        self.results_tab = ResultsTab(self.core_manager)
        
        self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")
        self.tab_widget.addTab(self.projects_tab, "📋 Projects")
        self.tab_widget.addTab(self.reviews_tab, "📝 Reviews")
        self.tab_widget.addTab(self.analysis_tab, "🔬 Analysis")
        self.tab_widget.addTab(self.results_tab, "📈 Results")
        
        # Layout assembly
        main_layout.addWidget(self.system_status)
        main_layout.addWidget(self.tab_widget)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready - OpenGeneva Sparkboard Desktop Client")
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background-color: {ModernColors.SURFACE};
                color: {ModernColors.TEXT_SECONDARY};
                border-top: 1px solid #e2e8f0;
                padding: 5px;
            }}
        """)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Ontology driven hackathon review system")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Université de Genève")
    
    # Apply modern font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    logger.info("🚀 Desktop GUI started successfully")
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()