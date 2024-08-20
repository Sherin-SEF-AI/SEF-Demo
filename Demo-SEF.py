import sys
import os
import requests
import base64
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QProgressBar, QTextEdit, 
                             QMessageBox, QTabWidget, QListWidget, QSplitter, QDialog, QDialogButtonBox, 
                             QTreeWidget, QTreeWidgetItem, QLineEdit, QFormLayout)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

API_KEY = 'YOUR_API_KEY'  # Replace with your actual API key
API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent'

class SEFDemoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scenarios = {
            "Home Intrusion": "A scenario where an unauthorized person is attempting to enter a residential property.",
            "Car Following": "A situation where one vehicle is closely following another, potentially leading to dangerous driving conditions.",
            "Fire Outbreak": "A scenario depicting the early stages of a fire in a building or outdoor area.",
            "Medical Emergency": "A scenario where an individual is experiencing a critical health issue that requires immediate attention.",
            "Suspicious Package": "A scenario where an unattended package is found in a public place, raising concerns about its contents."
        }
        self.current_file = None
        self.history = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Enhanced SEF Interactive Demo")
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(QIcon('sef_icon.png'))  # Make sure you have this icon file in your project directory

        main_layout = QHBoxLayout()

        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Scenario selection
        self.scenario_combo = QComboBox(self)
        self.scenario_combo.addItems(["Select a Scenario"] + list(self.scenarios.keys()))
        self.scenario_combo.currentIndexChanged.connect(self.load_predefined_scenario)
        left_layout.addWidget(QLabel("Predefined Scenarios:"))
        left_layout.addWidget(self.scenario_combo)

        # File upload
        self.upload_btn = QPushButton("Upload Image/Video", self)
        self.upload_btn.clicked.connect(self.upload_file)
        left_layout.addWidget(self.upload_btn)

        # Analysis controls
        self.analyze_btn = QPushButton("Analyze Content", self)
        self.analyze_btn.clicked.connect(self.start_analysis)
        left_layout.addWidget(self.analyze_btn)

        # Real-time threat detection button
        self.threat_detection_btn = QPushButton("Simulate Real-Time Threat Detection", self)
        self.threat_detection_btn.clicked.connect(self.simulate_real_time_threat_detection)
        left_layout.addWidget(self.threat_detection_btn)

        self.progress_bar = QProgressBar(self)
        left_layout.addWidget(self.progress_bar)

        # Save & Export Button
        self.save_btn = QPushButton("Save Analysis Report", self)
        self.save_btn.clicked.connect(self.save_report)
        left_layout.addWidget(self.save_btn)

        # Walkthrough Button
        self.walkthrough_btn = QPushButton("Start Interactive Walkthrough", self)
        self.walkthrough_btn.clicked.connect(self.start_walkthrough)
        left_layout.addWidget(self.walkthrough_btn)

        # Notification system label
        self.notification_label = QLabel("", self)
        self.notification_label.setStyleSheet("color: red; font-weight: bold;")
        left_layout.addWidget(self.notification_label)

        left_layout.addStretch()

        # Right panel for content display and analysis
        right_panel = QTabWidget()

        # Media display tab
        media_tab = QWidget()
        media_layout = QVBoxLayout(media_tab)
        self.media_label = QLabel("No Image/Video Selected", self)
        self.media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        media_layout.addWidget(self.media_label)

        # Video player
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        media_layout.addWidget(self.video_widget)
        self.video_widget.hide()  # Initially hidden

        right_panel.addTab(media_tab, "Media")

        # Analysis result tab
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        self.analysis_text = QTextEdit(self)
        self.analysis_text.setReadOnly(True)
        analysis_layout.addWidget(self.analysis_text)
        right_panel.addTab(analysis_tab, "Analysis")

        # History tab
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_history_item)
        history_layout.addWidget(self.history_list)
        right_panel.addTab(history_tab, "History")

        # Interactive Map tab (Placeholder for now)
        map_tab = QWidget()
        map_layout = QVBoxLayout(map_tab)
        map_layout.addWidget(QLabel("Map Integration Coming Soon!"))
        right_panel.addTab(map_tab, "Map")

        # Add panels to main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 1000])  # Adjust the initial sizes as needed
        main_layout.addWidget(splitter)

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def load_predefined_scenario(self, index):
        if index > 0:
            scenario = self.scenario_combo.currentText()
            self.analysis_text.append(f"Loaded predefined scenario: {scenario}")
            self.analysis_text.append(f"Description: {self.scenarios[scenario]}")
            self.analyze_scenario(scenario)

    def upload_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open Image/Video File", "", "Image/Video Files (*.png *.jpg *.jpeg *.mp4 *.avi *.mov)")
        if file_path:
            self.current_file = file_path
            self.display_file(file_path)

    def display_file(self, file_path):
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            pixmap = QPixmap(file_path)
            self.media_label.setPixmap(pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio))
            self.video_widget.hide()
            self.media_label.show()
        elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.video_widget.show()
            self.media_label.hide()
        self.media_label.setText("")

    def start_analysis(self):
        if self.current_file:
            self.analyze_content(self.current_file)
        else:
            QMessageBox.warning(self, "No File Selected", "Please upload an image or video first.")

    def analyze_content(self, file_path):
        self.progress_bar.setValue(0)
        self.analysis_text.append("Analyzing content...")

        # Run the analysis in a separate thread
        self.analysis_thread = AnalysisThread(file_path)
        self.analysis_thread.progress_update.connect(self.update_progress)
        self.analysis_thread.analysis_complete.connect(self.display_analysis)
        self.analysis_thread.start()

    def analyze_scenario(self, scenario):
        self.progress_bar.setValue(0)
        self.analysis_text.append(f"Analyzing scenario: {scenario}")

        # Run the scenario analysis in a separate thread
        self.analysis_thread = ScenarioAnalysisThread(scenario, self.scenarios[scenario])
        self.analysis_thread.progress_update.connect(self.update_progress)
        self.analysis_thread.analysis_complete.connect(self.display_analysis)
        self.analysis_thread.start()

    def simulate_real_time_threat_detection(self):
        QMessageBox.information(self, "Real-Time Threat Detection", "Simulating real-time threat detection...")

        # Start a simulated real-time threat detection thread
        self.threat_thread = RealTimeThreatDetectionThread(self.scenarios)
        self.threat_thread.threat_detected.connect(self.notify_threat_detected)
        self.threat_thread.start()

    def notify_threat_detected(self, threat_info):
        self.notification_label.setText(threat_info)
        self.analysis_text.append(f"Real-Time Threat Detected: {threat_info}")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_analysis(self, analysis_result):
        if 'error' in analysis_result:
            self.analysis_text.append(f"Error: {analysis_result['error']}")
        else:
            insights = analysis_result.get('content', 'No insights generated by the AI.')
            self.analysis_text.append(insights)
            
            # Add to history
            history_item = f"Analysis {len(self.history) + 1}"
            self.history.append((self.current_file, insights))
            self.history_list.addItem(history_item)

    def save_report(self):
        report_text = self.analysis_text.toPlainText()
        if report_text:
            file_dialog = QFileDialog()
            save_path, _ = file_dialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt);;All Files (*)")
            if save_path:
                with open(save_path, 'w') as file:
                    file.write(report_text)
                QMessageBox.information(self, "Report Saved", f"Report successfully saved to {save_path}")
        else:
            QMessageBox.warning(self, "No Report", "There is no analysis report to save.")

    def start_walkthrough(self):
        walkthrough_steps = [
            "Welcome to the SEF Interactive Demo! This walkthrough will guide you through the main features of the application.",
            "On the left, you can select predefined scenarios or upload your own image or video for analysis.",
            "Use the 'Analyze Content' button to start analyzing the selected file or scenario.",
            "View the results of the analysis in the 'Analysis' tab, where AI-generated insights will be displayed.",
            "The 'History' tab keeps a record of all your analyses, allowing you to revisit previous results.",
            "Click 'Save Analysis Report' to export your findings to a text file.",
            "The notification system will alert you to any detected threats during the analysis.",
            "The 'Map' tab will soon allow you to visualize incidents on a map, providing a geographic context.",
            "This concludes the walkthrough. Feel free to explore the application and test different scenarios!"
        ]

        for step in walkthrough_steps:
            dlg = QDialog(self)
            dlg.setWindowTitle("Interactive Walkthrough")
            dlg.setFixedSize(400, 200)
            dlg_layout = QVBoxLayout(dlg)
            dlg_label = QLabel(step, dlg)
            dlg_label.setWordWrap(True)
            dlg_layout.addWidget(dlg_label)
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, dlg)
            button_box.accepted.connect(dlg.accept)
            dlg_layout.addWidget(button_box)
            dlg.exec()

    def load_history_item(self, item):
        index = self.history_list.row(item)
        file_path, analysis = self.history[index]
        if file_path:
            self.display_file(file_path)
        self.analysis_text.setText(analysis)

class AnalysisThread(QThread):
    progress_update = pyqtSignal(int)
    analysis_complete = pyqtSignal(dict)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        for i in range(1, 101):
            self.msleep(20)
            self.progress_update.emit(i)

        analysis_result = self.perform_analysis(self.file_path)
        self.analysis_complete.emit(analysis_result)

    def perform_analysis(self, file_path):
        headers = {'Content-Type': 'application/json'}
        
        with open(file_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        payload = {
            "contents": [{
                "parts": [
                    {"text": "Analyze this image for safety and security concerns. Provide a detailed assessment of potential risks and recommended actions."},
                    {"inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_data
                    }}
                ]
            }]
        }

        try:
            response = requests.post(f'{API_URL}?key={API_KEY}', headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            content = response_data['candidates'][0]['content']['parts'][0]['text']
            return {"content": content}
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

class ScenarioAnalysisThread(QThread):
    progress_update = pyqtSignal(int)
    analysis_complete = pyqtSignal(dict)

    def __init__(self, scenario, description):
        super().__init__()
        self.scenario = scenario
        self.description = description

    def run(self):
        for i in range(1, 101):
            self.msleep(20)
            self.progress_update.emit(i)

        analysis_result = self.perform_analysis()
        self.analysis_complete.emit(analysis_result)

    def perform_analysis(self):
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"Analyze the following safety and security scenario: {self.scenario}\n\nDescription: {self.description}\n\nProvide a detailed assessment of potential risks, recommended actions, and preventive measures."
                }]
            }]
        }

        try:
            response = requests.post(f'{API_URL}?key={API_KEY}', headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            content = response_data['candidates'][0]['content']['parts'][0]['text']
            return {"content": content}
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}

class RealTimeThreatDetectionThread(QThread):
    threat_detected = pyqtSignal(str)

    def __init__(self, scenarios):
        super().__init__()
        self.scenarios = scenarios

    def run(self):
        for i in range(1, 101):
            self.msleep(100)  # Simulate time taken for threat detection
            if i == 50:  # Simulate threat detection at 50% progress
                self.threat_detected.emit("Potential threat detected in real-time simulation.")

def main():
    app = QApplication(sys.argv)
    demo = SEFDemoApp()
    demo.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

