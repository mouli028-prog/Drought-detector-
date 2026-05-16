import sys
import requests # auto - location (ai)
import datetime
import cv2 #opencv2 Camera (ai)
import numpy as np # accu (ai)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QMessageBox, QSplashScreen, QTextEdit
)
from PyQt5.QtGui import QPixmap, QFont, QColor, QPainter, QBrush
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRect

FETCH_URL = "https://api.open-meteo.com/v1/forecast"

#DBMS
CITIES = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "kolkata": (22.5726, 88.3639),
    "chennai": (13.0827, 80.2707),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
}


def drought_solutions(severity):
    tips = {
        "No Drought": [
            "✅ Maintain sustainable water usage.",
            "✅ Keep planting drought-tolerant crops.",
            "✅ Regularly monitor soil moisture."
        ],
        "Mild Drought": [
            "💧 Use drip irrigation to save water.",
            "🌿 Apply mulch to retain soil moisture.",
            "🚜 Avoid over-tilling the soil."
        ],
        "Moderate Drought": [
            "💦 Recycle and store rainwater.",
            "🌾 Grow drought-resistant crops.",
            "🧑‍🌾 Implement efficient irrigation."
        ],
        "Severe Drought": [
            "🚱 Ration water supply and avoid wastage.",
            "🏞️ Construct check dams for water storage.",
            "🌳 Promote afforestation.",
            "🤝 Seek government relief programs."
        ],
    }
    return "<br>".join(tips.get(severity, []))


def get_auto_location():
    try:
        res = requests.get("https://ipinfo.io/json", timeout=5)
        data = res.json()
        city = data.get("city", "Unknown").lower()
        loc = data.get("loc", "").split(",")
        if len(loc) == 2:
            lat, lon = float(loc[0]), float(loc[1])
        else:
            lat, lon = 20.5937, 78.9629
        return city, lat, lon
    except Exception:
        return None, None, None


def get_weather_data(city=None, auto=False, parent_widget=None):
    if auto:
        city_name, lat, lon = get_auto_location()
        if city_name is None:
            if parent_widget:
                QMessageBox.warning(parent_widget, "Location Error", "Unable to fetch location automatically.")
            return None
    else:
        city = city.lower()
        if city not in CITIES:
            if parent_widget:
                QMessageBox.critical(parent_widget, "Error", f"City '{city}' not found.")
            return None
        city_name = city
        lat, lon = CITIES[city]

    params = {"latitude": lat, "longitude": lon, "current_weather": True}
    try:
        response = requests.get(FETCH_URL, params=params, timeout=8)
        data = response.json()
        if "current_weather" not in data:
            raise Exception("Weather data not found.")
        return data["current_weather"], city_name.title(), lat, lon
    except Exception as e:
        if parent_widget:
            QMessageBox.critical(parent_widget, "Error", f"Failed to get weather data:\n{e}")
        return None


class DroughtApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌾 Drought Detection (UEM Project)")
        self.setGeometry(200, 100, 900, 850)
        self.setStyleSheet("background-color: #101820; color: white;")

        self.layout = QVBoxLayout(self)

        self.title = QLabel("🌾 Drought Detection System")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.title.setStyleSheet("color: #00e676;")
        self.layout.addWidget(self.title)

        banner = QLabel()
        try:
            pixmap = QPixmap("drought-removebg-preview.png").scaled(320, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            banner.setPixmap(pixmap)
            banner.setAlignment(Qt.AlignCenter)
        except:
            banner.setText("[Image Missing]")
            banner.setAlignment(Qt.AlignCenter)
            banner.setStyleSheet("color: #9e9e9e;")
        self.layout.addWidget(banner)

        form = QHBoxLayout()
        lbl_city = QLabel("Enter City (optional): ")
        lbl_city.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_city.setStyleSheet("color: #cfd8dc;")
        self.entry_city = QLineEdit()
        self.entry_city.setFixedWidth(250)
        self.entry_city.setStyleSheet("""
            background-color: #263238;
            border: none;
            color: white;
            padding: 6px;
            font-size: 13px;
        """)
        form.addWidget(lbl_city)
        form.addWidget(self.entry_city)
        self.layout.addLayout(form)

        self.add_button("Detect Current Drought (Manual)", self.detect_drought, "#0288d1")
        self.add_button("Auto Detect Drought (via Location)", lambda: self.detect_drought(auto=True), "#f57c00")
        self.add_button("Predict Future Drought (6 Months)", self.predict_future_drought, "#43a047")
        self.add_button("Analyze Soil via Camera", self.analyze_soil_camera, "#8e24aa")
        self.add_button("Upload Soil Image to Analyze", self.analyze_soil_upload, "#3949ab")

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setStyleSheet("""
            background-color: #1b1f23;
            color: #e0e0e0;
            border-radius: 10px;
            padding: 12px;
            font-size: 14px;
        """)
        self.layout.addWidget(self.result_box)

        self.footer = QLabel("Developed by Our Project Team")
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setStyleSheet("color: #757575; font-style: italic;")
        self.layout.addWidget(self.footer)

    def add_button(self, text, func, color):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #004d40;
            }}
        """)
        btn.clicked.connect(func)
        self.layout.addWidget(btn)

    def detect_drought(self, auto=False):
        city = self.entry_city.text().strip()
        if not city and not auto:
            QMessageBox.warning(self, "Input Missing", "Please enter a city name or use Auto Detect.")
            return

        result_data = get_weather_data(city, auto, parent_widget=self)
        if result_data is None:
            return

        data, city_name, _, _ = result_data
        temperature = data.get("temperature", 30)
        windspeed = data.get("windspeed", 5)
        rainfall = max(0, 10 - (windspeed / 2))
        soil_moisture = max(0, 100 - temperature - (windspeed / 1.5))

        if rainfall < 1 and temperature > 37 and soil_moisture < 20:
            result = "Severe Drought"; color = "#ff3b3b"
        elif rainfall < 5 and temperature > 33 and soil_moisture < 35:
            result = "Moderate Drought"; color = "#ff9933"
        elif rainfall < 10 and temperature > 30 and soil_moisture < 50:
            result = "Mild Drought"; color = "#e6b800"
        else:
            result = "No Drought"; color = "#00cc66"

        text = (
            f"🌆 City: {city_name}\n"
            f"🌡️ Temperature: {temperature} °C\n"
            f"🌬️ Windspeed: {windspeed} km/h\n"
            f"🌧️ Estimated Rainfall: {rainfall:.1f} mm\n"
            f"🌱 Soil Moisture (est.): {soil_moisture:.1f}%\n\n"
            f"🔥 Drought Status: {result}\n\n"
            f"💡 Suggested Solutions:\n{drought_solutions(result)}"
        )
        html = f'<div style="color:{color}; font-family:Segoe UI; font-size:14px; white-space:pre-wrap;">{text.replace(chr(10), "<br>")}</div>'
        self.result_box.setHtml(html)

    def predict_future_drought(self):
        city = self.entry_city.text().strip()
        if not city:
            QMessageBox.warning(self, "Input Missing", "Please enter a city name.")
            return
        city = city.lower()
        if city not in CITIES:
            QMessageBox.critical(self, "Error", f"City '{city}' not found.")
            return

        lat, lon = CITIES[city]
        params = {
            "latitude": lat,
            "longitude": lon,
            "forecast_days": 7,
            "daily": ["temperature_2m_max", "precipitation_sum"],
            "timezone": "auto"
        }

        try:
            response = requests.get(FETCH_URL, params=params, timeout=8)
            data = response.json()
            temps = data.get("daily", {}).get("temperature_2m_max", [30] * 7)
            rains = data.get("daily", {}).get("precipitation_sum", [1] * 7)
            avg_temp = sum(temps) / len(temps)
            avg_rain = sum(rains) / len(rains)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unable to fetch future data:\n{e}")
            return

        now = datetime.datetime.now()
        results = []
        for i in range(1, 6):
            month = (now + datetime.timedelta(days=30 * i)).strftime("%B")
            temp = avg_temp + (i * 0.8)
            rain = max(0, avg_rain - (i * 0.5))
            soil = max(0, 100 - temp - (rain * 3))

            if rain < 1 and temp > 37 and soil < 20:
                risk = "Severe Drought"
            elif rain < 5 and temp > 33 and soil < 35:
                risk = "Moderate Drought"
            elif rain < 10 and temp > 30 and soil < 50:
                risk = "Mild Drought"
            else:
                risk = "No Drought"
            results.append(f"{month}: {risk}\n{drought_solutions(risk)}\n")

        html = '<div style="color:#00bcd4; font-family:Segoe UI; font-size:14px;">'
        html += "<h3>🌦️ Future Drought Prediction:</h3>"
        for r in results:
            html += f"<p style='margin-bottom:8px'>{r.replace(chr(10), '<br>')}</p>"
        html += "</div>"
        self.result_box.setHtml(html)

    def analyze_soil_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Soil Image", "", "Images (*.jpg *.jpeg *.png *.bmp)")
        if not file_path:
            return

        image = cv2.imread(file_path)
        if image is None:
            QMessageBox.critical(self, "Error", "Unable to read image file.")
            return

        self.detect_soil_drought(image)

    def analyze_soil_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            QMessageBox.critical(self, "Camera Error", "Unable to access the webcam.")
            return
        QMessageBox.information(self, "Instructions", "Press SPACE to capture soil image, or ESC to cancel.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Soil Detection - Press Space to Capture", frame)
            key = cv2.waitKey(1)
            if key == 27:
                break
            elif key == 32:
                cv2.destroyAllWindows()
                cap.release()
                self.detect_soil_drought(frame)
                return
        cv2.destroyAllWindows()
        cap.release()

    def detect_soil_drought(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_brown = np.array([10, 60, 20])
        upper_brown = np.array([30, 255, 200])
        mask = cv2.inRange(hsv, lower_brown, upper_brown)
        dry_percent = (cv2.countNonZero(mask) / (image.size / 3)) * 100

        if dry_percent > 50:
            status = "⚠️ Dry Soil Detected (Possible Drought)"
            color = "#e60000"
        elif 20 < dry_percent <= 50:
            status = "🌤️ Mildly Dry Soil"
            color = "#ff8000"
        else:
            status = "💧 Moist Soil (No Drought)"
            color = "#00e676"

        text = f"📸 Soil Analysis:\n{status}\nDryness Level: {dry_percent:.1f}%"
        html = f'<div style="color:{color}; font-family:Segoe UI; font-size:14px; white-space:pre-wrap;">{text.replace(chr(10), "<br>")}</div>'
        self.result_box.setHtml(html)


class SplashScreen(QSplashScreen):
    finished_loading = pyqtSignal()

    def __init__(self, main_window=None):
        pixmap = QPixmap(650, 380)
        pixmap.fill(QColor("#101820"))
        super().__init__(pixmap)
        self.main_window = main_window
        self.progress = 0

        self.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.showMessage("<center><span style='font-size:20px; color:white;'>🌾 Drought Detection System<br><br>Loading... 0%</span></center>", Qt.AlignCenter)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(40)

    def update_progress(self):
        self.progress += 1
        if self.progress > 100:
            self.timer.stop()
            if self.main_window:
                self.finish(self.main_window)
                self.main_window.show()
            self.finished_loading.emit()
            return
        self.showMessage(f"<center><span style='font-size:20px; color:white;'>🌾 Drought Detection System<br><br>Loading... {self.progress}%</span></center>", Qt.AlignCenter)
        self.repaint()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        bar_width = int((self.width() - 80) * (self.progress / 100))
        rect = QRect(40, self.height() - 60, bar_width, 18)
        painter.fillRect(rect, QColor("#00e676"))

        outline = QRect(40, self.height() - 60, self.width() - 80, 18)
        painter.setPen(QColor("#ffffff"))
        painter.drawRect(outline)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = DroughtApp()
    splash = SplashScreen(main_window=main_window)
    splash.show()
    QTimer.singleShot(8000, lambda: (main_window.show() if not main_window.isVisible() else None))
    sys.exit(app.exec_())
