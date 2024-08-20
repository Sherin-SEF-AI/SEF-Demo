import sys
import os
import requests
import base64
import json
import random
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QProgressBar, QTextEdit, 
                             QMessageBox, QTabWidget, QListWidget, QSplitter, QDialog, QDialogButtonBox, 
                             QTreeWidget, QTreeWidgetItem, QLineEdit, QFormLayout, QStackedWidget, 
                             QScrollArea, QFrame, QSlider, QCheckBox, QCalendarWidget)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor, QPalette, QPainter
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl, QTimer, QPointF
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QScatterSeries
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium
from folium.plugins import HeatMap

API_KEY = ''  # Replace with your actual API key
API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent'

class DarkPalette(QPalette):
    def __init__(self):
        super().__init__()
        self.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        self.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        self.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        self.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        self.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        self.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        self.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        self.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        self.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        self.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        self.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        self.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        self.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

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
        self.threat_level = 0
        self.incidents = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Advanced SEF Interactive Demo")
        self.setGeometry(100, 100, 1800, 1000)
        self.setWindowIcon(QIcon('sef_icon.png'))

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
        self.threat_detection_btn = QPushButton("Start Real-Time Threat Detection", self)
        self.threat_detection_btn.clicked.connect(self.toggle_real_time_threat_detection)
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

        # Settings Button
        self.settings_btn = QPushButton("Settings", self)
        self.settings_btn.clicked.connect(self.open_settings)
        left_layout.addWidget(self.settings_btn)

        # Threat level indicator
        self.threat_level_label = QLabel("Threat Level: Low", self)
        self.threat_level_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(self.threat_level_label)

        left_layout.addStretch()

        # Right panel for content display and analysis
        right_panel = QTabWidget()

        # Dashboard tab
        dashboard_tab = self.create_dashboard_tab()
        right_panel.addTab(dashboard_tab, "Dashboard")

        # Media display tab
        media_tab = self.create_media_tab()
        right_panel.addTab(media_tab, "Media")

        # Analysis result tab
        analysis_tab = self.create_analysis_tab()
        right_panel.addTab(analysis_tab, "Analysis")

        # History tab
        history_tab = self.create_history_tab()
        right_panel.addTab(history_tab, "History")

        # Interactive Map tab
        map_tab = self.create_map_tab()
        right_panel.addTab(map_tab, "Map")

        # Incident Report tab
        incident_report_tab = self.create_incident_report_tab()
        right_panel.addTab(incident_report_tab, "Incident Report")

        # Add panels to main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 1400])
        main_layout.addWidget(splitter)

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Setup a timer for periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(5000)  # Update every 5 seconds

        # Initialize real-time threat detection
        self.real_time_detection_active = False
        self.threat_detection_thread = None

    def create_dashboard_tab(self):
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)

        # Threat level chart
        self.threat_chart = self.create_threat_level_chart()
        layout.addWidget(self.threat_chart)

        # Incident trend chart
        self.incident_trend_chart = self.create_incident_trend_chart()
        layout.addWidget(self.incident_trend_chart)

        # Recent incidents list
        self.recent_incidents = QListWidget()
        layout.addWidget(QLabel("Recent Incidents:"))
        layout.addWidget(self.recent_incidents)

        return dashboard

    def create_media_tab(self):
        media_tab = QWidget()
        layout = QVBoxLayout(media_tab)

        self.media_label = QLabel("No Image/Video Selected", self)
        self.media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_label.setStyleSheet("background-color: #2C3E50; color: white; border-radius: 10px; padding: 20px;")
        layout.addWidget(self.media_label)

        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)
        self.video_widget.hide()

        return media_tab

    def create_analysis_tab(self):
        analysis_tab = QWidget()
        layout = QVBoxLayout(analysis_tab)

        self.analysis_text = QTextEdit(self)
        self.analysis_text.setReadOnly(True)
        layout.addWidget(self.analysis_text)

        return analysis_tab

    def create_history_tab(self):
        history_tab = QWidget()
        layout = QVBoxLayout(history_tab)

        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_history_item)
        layout.addWidget(self.history_list)

        return history_tab

    def create_map_tab(self):
        map_tab = QWidget()
        layout = QVBoxLayout(map_tab)

        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        self.update_map()

        return map_tab

    def create_incident_report_tab(self):
        incident_tab = QWidget()
        layout = QVBoxLayout(incident_tab)

        form_layout = QFormLayout()
        self.incident_type = QComboBox()
        self.incident_type.addItems(["Select Type", "Burglary", "Fire", "Traffic Accident", "Medical Emergency", "Suspicious Activity"])
        form_layout.addRow("Incident Type:", self.incident_type)

        self.incident_location = QLineEdit()
        form_layout.addRow("Location:", self.incident_location)

        self.incident_date = QCalendarWidget()
        form_layout.addRow("Date:", self.incident_date)

        self.incident_description = QTextEdit()
        form_layout.addRow("Description:", self.incident_description)

        layout.addLayout(form_layout)

        submit_btn = QPushButton("Submit Incident Report")
        submit_btn.clicked.connect(self.submit_incident_report)
        layout.addWidget(submit_btn)

        return incident_tab

    def create_threat_level_chart(self):
        series = QPieSeries()
        series.append("Low", 60)
        series.append("Medium", 30)
        series.append("High", 10)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Current Threat Level Distribution")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        return chart_view

    def create_incident_trend_chart(self):
        series = QLineSeries()
        
        # Sample data - replace with actual historical data in a real application
        for i in range(7):
            date = QPointF(i, random.randint(5, 20))
            series.append(date)

        chart = QChart()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setTitle("7-Day Incident Trend")

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        return chart_view

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

        self.analysis_thread = AnalysisThread(file_path)
        self.analysis_thread.progress_update.connect(self.update_progress)
        self.analysis_thread.analysis_complete.connect(self.display_analysis)
        self.analysis_thread.start()

    def analyze_scenario(self, scenario):
        self.progress_bar.setValue(0)
        self.analysis_text.append(f"Analyzing scenario: {scenario}")

        self.analysis_thread = ScenarioAnalysisThread(scenario, self.scenarios[scenario])
        self.analysis_thread.progress_update.connect(self.update_progress)
        self.analysis_thread.analysis_complete.connect(self.display_analysis)
        self.analysis_thread.start()

    def toggle_real_time_threat_detection(self):
        if not self.real_time_detection_active:
            self.start_real_time_threat_detection()
        else:
            self.stop_real_time_threat_detection()

    def start_real_time_threat_detection(self):
        self.real_time_detection_active = True
        self.threat_detection_btn.setText("Stop Real-Time Threat Detection")
        self.threat_detection_thread = RealTimeThreatDetectionThread(self.scenarios)
        self.threat_detection_thread.threat_detected.connect(self.notify_threat_detected)
        self.threat_detection_thread.start()

    def stop_real_time_threat_detection(self):
        self.real_time_detection_active = False
        self.threat_detection_btn.setText("Start Real-Time Threat Detection")
        if self.threat_detection_thread:
            self.threat_detection_thread.stop()
            self.threat_detection_thread.wait()
            self.threat_detection_thread = None

    def notify_threat_detected(self, threat_info):
        self.threat_level = min(self.threat_level + 20, 100)
        self.update_threat_level_display()
        self.analysis_text.append(f"Real-Time Threat Detected: {threat_info}")
        self.add_incident(threat_info)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_analysis(self, analysis_result):
        if 'error' in analysis_result:
            self.analysis_text.append(f"Error: {analysis_result['error']}")
        else:
            insights = analysis_result.get('content', 'No insights generated by the AI.')
            self.analysis_text.append(insights)
            
            history_item = f"Analysis {len(self.history) + 1}"
            self.history.append((self.current_file, insights))
            self.history_list.addItem(history_item)

    def save_report(self):
        report_text = self.analysis_text.toPlainText()
        if report_text:
            file_dialog = QFileDialog()
            save_path, _ = file_dialog.getSaveFileName(self, "Save Report", "", "Text Files (*.txt);;PDF Files (*.pdf);;All Files (*)")
            if save_path:
                if save_path.endswith('.pdf'):
                    self.save_as_pdf(save_path, report_text)
                else:
                    with open(save_path, 'w') as file:
                        file.write(report_text)
                QMessageBox.information(self, "Report Saved", f"Report successfully saved to {save_path}")
        else:
            QMessageBox.warning(self, "No Report", "There is no analysis report to save.")

    def save_as_pdf(self, file_path, content):
        # Placeholder for PDF generation logic
        # You would typically use a library like reportlab here
        QMessageBox.information(self, "PDF Generation", "PDF generation feature coming soon!")

    def start_walkthrough(self):
        walkthrough_steps = [
            "Welcome to the Advanced SEF Interactive Demo!",
            "The dashboard shows current threat levels and incident trends.",
            "Use 'Predefined Scenarios' to analyze common security situations.",
            "Upload your own images or videos for custom analysis.",
            "The 'Analyze Content' button processes your selected media or scenario.",
            "View AI-generated insights in the 'Analysis' tab.",
            "The 'History' tab keeps a record of all your past analyses.",
            "Use 'Start Real-Time Threat Detection' to simulate live threat monitoring.",
            "The 'Map' tab shows geographic data of incidents.",
            "Report new incidents using the 'Incident Report' tab.",
            "Adjust application settings using the 'Settings' button.",
            "This concludes the walkthrough. Explore the demo to learn more!"
        ]

        for step in walkthrough_steps:
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Interactive Walkthrough")
            dialog.setText(step)
            dialog.setStandardButtons(QMessageBox.StandardButton.Next | QMessageBox.StandardButton.Cancel)
            if dialog.exec() == QMessageBox.StandardButton.Cancel:
                break

    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Settings")
        layout = QVBoxLayout(settings_dialog)

        # Dark Mode Toggle
        dark_mode_checkbox = QCheckBox("Dark Mode")
        dark_mode_checkbox.setChecked(self.palette().color(QPalette.ColorRole.Window).lightness() < 128)
        dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(dark_mode_checkbox)

        # Notification Settings
        notification_checkbox = QCheckBox("Enable Notifications")
        notification_checkbox.setChecked(True)
        layout.addWidget(notification_checkbox)

        # API Key Input
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("API Key:"))
        api_key_input = QLineEdit()
        api_key_input.setText(API_KEY)
        api_key_layout.addWidget(api_key_input)
        layout.addLayout(api_key_layout)

        # Close Button
        close_button = QPushButton("Close")
        close_button.clicked.connect(settings_dialog.accept)
        layout.addWidget(close_button)

        settings_dialog.exec()

    def toggle_dark_mode(self, state):
        if state == Qt.CheckState.Checked.value:
            self.setPalette(DarkPalette())
        else:
            self.setPalette(self.style().standardPalette())

    def update_threat_level_display(self):
        threat_levels = ["Low", "Medium", "High", "Critical"]
        level = threat_levels[min(self.threat_level // 25, 3)]
        self.threat_level_label.setText(f"Threat Level: {level}")
        self.threat_level_label.setStyleSheet(f"color: {'green' if level == 'Low' else 'orange' if level == 'Medium' else 'red'}; font-weight: bold;")

    def periodic_update(self):
        # Simulate changing threat levels
        self.threat_level = max(0, min(self.threat_level + random.randint(-10, 10), 100))
        self.update_threat_level_display()

        # Update threat level chart
        self.update_threat_level_chart()

        # Update incident trend chart
        self.update_incident_trend_chart()

        # Update map
        self.update_map()

    def update_threat_level_chart(self):
        chart = self.threat_chart.chart()
        if chart:
            series = chart.series()[0]
            series.clear()
            series.append("Low", max(0, 100 - self.threat_level))
            series.append("Medium", min(self.threat_level, 50))
            series.append("High", max(0, self.threat_level - 50))

    def update_incident_trend_chart(self):
        chart = self.incident_trend_chart.chart()
        if chart:
            series = chart.series()[0]
            series.clear()
            for i in range(7):
                date = QPointF(i, len([inc for inc in self.incidents if inc['date'] == (datetime.now() - timedelta(days=i)).date()]))
                series.append(date)

    def update_map(self):
        m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)
        
        # Add markers for incidents
        for incident in self.incidents:
            folium.Marker(
                location=incident['location'],
                popup=incident['description'],
                tooltip=incident['type']
            ).add_to(m)

        # Add heatmap layer
        heat_data = [[inc['location'][0], inc['location'][1]] for inc in self.incidents]
        HeatMap(heat_data).add_to(m)

        # Save map to HTML file
        m.save("incident_map.html")

        # Load the HTML file into the QWebEngineView
        self.map_view.setUrl(QUrl.fromLocalFile(os.path.abspath("incident_map.html")))

    def load_history_item(self, item):
        index = self.history_list.row(item)
        file_path, analysis = self.history[index]
        if file_path:
            self.display_file(file_path)
        self.analysis_text.setText(analysis)

    def submit_incident_report(self):
        incident_type = self.incident_type.currentText()
        location = self.incident_location.text()
        date = self.incident_date.selectedDate().toPyDate()
        description = self.incident_description.toPlainText()

        if incident_type == "Select Type" or not location or not description:
            QMessageBox.warning(self, "Incomplete Report", "Please fill in all fields.")
            return

        # In a real application, you would validate the location and convert it to coordinates
        # For this demo, we'll use random coordinates near New York City
        lat = 40.7128 + random.uniform(-0.1, 0.1)
        lon = -74.0060 + random.uniform(-0.1, 0.1)

        new_incident = {
            'type': incident_type,
            'location': [lat, lon],
            'date': date,
            'description': description
        }

        self.add_incident(new_incident)
        QMessageBox.information(self, "Report Submitted", "Incident report has been submitted successfully.")

    def add_incident(self, incident):
        self.incidents.append(incident)
        self.recent_incidents.insertItem(0, f"{incident['type']} - {incident['date']}")
        if self.recent_incidents.count() > 5:
            self.recent_incidents.takeItem(self.recent_incidents.count() - 1)
        self.update_map()

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
    threat_detected = pyqtSignal(dict)

    def __init__(self, scenarios):
        super().__init__()
        self.scenarios = scenarios
        self.is_running = True

    def run(self):
        while self.is_running:
            self.msleep(5000)  # Check every 5 seconds
            if random.random() < 0.3:  # 30% chance of detecting a threat
                threat = random.choice(list(self.scenarios.keys()))
                lat = 40.7128 + random.uniform(-0.1, 0.1)
                lon = -74.0060 + random.uniform(-0.1, 0.1)
                self.threat_detected.emit({
                    'type': threat,
                    'location': [lat, lon],
                    'date': datetime.now().date(),
                    'description': f"Potential {threat.lower()} detected."
                })

    def stop(self):
        self.is_running = False

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    demo = SEFDemoApp()
    demo.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
