import csv
import qrcode
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, \
    QMessageBox, QInputDialog, QTabWidget, QMainWindow, QTextBrowser
from PyQt5.QtGui import QPixmap
from PyQt5.QtWebEngineWidgets import QWebEngineView
from folium import Map, Marker, Icon, PolyLine, Popup
from geopy.geocoders import Nominatim
import random
import sys


class RideApp(QWidget):
    def __init__(self, map_app):
        super().__init__()

        self.setWindowTitle("Cab Booking App")

        # Apply a style sheet for a cab booking app template
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
            }
            QLabel, QLineEdit, QPushButton, QComboBox {
                font-family: 'Arial', sans-serif;
                font-size: 14px;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 18px;
            }
            QLineEdit, QComboBox {
                background-color: #34495e;
                border: 1px solid #2c3e50;
                padding: 8px;
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                cursor: not-allowed;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLabel#qrLabel {
                margin-top: 20px;
                margin-bottom: 20px;
                color: #ecf0f1;
            }
        """)

        self.label = QLabel("Enter pickup location:")
        self.pickup_entry = QLineEdit()

        self.search_button = QPushButton("Search Drivers")
        self.search_button.clicked.connect(self.search_drivers)

        self.driver_listbox = QComboBox()

        self.confirm_button = QPushButton("Confirm Ride")
        self.confirm_button.clicked.connect(self.confirm_ride)

        self.qr_label = QLabel()
        self.qr_label.setObjectName("qrLabel")  # Set an object name for specific styling

        self.scanned_button = QPushButton("Scanned")
        self.scanned_button.clicked.connect(self.scan_confirmation)
        self.scanned_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.pickup_entry)
        layout.addWidget(self.search_button)
        layout.addWidget(self.driver_listbox)
        layout.addWidget(self.confirm_button)
        layout.addWidget(self.qr_label)
        layout.addWidget(self.scanned_button)

        self.setLayout(layout)

        # Reference to the BrowserWindow instance
        self.map_app = map_app

    def display_driver_details(self, driver_details):
        QMessageBox.information(
            self,
            "Driver Details",
            f"Name: {driver_details[0]}\n"
            f"Rating: {driver_details[1]}\n"
            f"Estimated Time of Arrival: {driver_details[2]} minutes\n"
            f"Fare: ${driver_details[3]}\n"
            f"Contact Number: {driver_details[4]}\n"
            f"Location: {driver_details[5]}"
        )

    def display_payment_details(self):
        payment_modes = ['Cash', 'Card', 'UPI']

        selected_mode, ok_pressed = QInputDialog.getItem(
            self,
            "Payment Mode",
            "Select Payment Mode:",
            payment_modes,
            0,
            False
        )

        if ok_pressed and selected_mode:
            QMessageBox.information(self, "Payment Mode", f"Selected Payment Mode: {selected_mode}")

    def search_drivers(self):
        pickup_location = self.pickup_entry.text()

        # Reading driver details from CSV file
        self.drivers = read_driver_details_from_csv('driver_details_with_location.csv')

        matching_drivers = [driver_details for driver_id, driver_details in self.drivers.items() if
                            driver_details[5].lower() == pickup_location.lower()]

        if matching_drivers:
            self.driver_listbox.clear()
            for i, driver_details in enumerate(matching_drivers, start=1):
                self.driver_listbox.addItem(
                    f"{i}. {driver_details[0]} (ETA: {driver_details[2]} mins, Fare: ${driver_details[3]})"
                )
        else:
            QMessageBox.information(self, "No Drivers", f"No available drivers for pickup location: {pickup_location}")

    def confirm_ride(self):
        index = self.driver_listbox.currentIndex()
        if index == -1:
            QMessageBox.information(self, "No Selection", "Please select a driver before confirming the ride.")
            return

        driver_details = list(self.drivers.values())[index]

        self.display_driver_details(driver_details)

        confirmation = QMessageBox.question(
            self, "Confirmation", "Do you want to confirm this ride?", QMessageBox.Yes | QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            qr_content = f"Ride Confirmation Driver: {driver_details[0]} ETA: {driver_details[2]} mins " \
                          f"Fare: ${driver_details[3]}"

            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(qr_content)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Save the image temporarily
            qr_img.save("temp_qr_code.png")

            # Display the QR code in QLabel
            pixmap = QPixmap("temp_qr_code.png")
            self.qr_label.setPixmap(pixmap)

            # Enable the "Scanned" button after 10 seconds
            self.scanned_button.setEnabled(True)

        else:
            QMessageBox.information(self, "Exit", "Ride not confirmed. Exiting...")

    def scan_confirmation(self):
        scan_result, ok_pressed = QInputDialog.getText(self, "Scanned", "Have you scanned the QR code? (yes/no)")

        if ok_pressed and scan_result and scan_result.lower() == 'yes':
            self.display_payment_details()
        else:
            QMessageBox.information(self, "Scan Cancelled", "Payment step cancelled.")


class ShopInfoWidget(QWidget):
    def __init__(self, shop_name, offer_details, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setWindowTitle(shop_name)
        self.setGeometry(100, 100, 400, 200)

        offer_button = QPushButton("View Offer Details")
        offer_button.clicked.connect(self.show_offer_details)

        layout.addWidget(offer_button)

        self.offer_details_label = QTextBrowser()
        self.offer_details_label.setPlainText(offer_details)
        layout.addWidget(self.offer_details_label)

        self.setLayout(layout)

    def show_offer_details(self):
        self.show()


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Specify pickup and destination coordinates
        pickup_location = get_coordinates("Porur, Chennai, India")
        destination_location = get_coordinates("Poonamallee, Chennai, India")

        if pickup_location is None or destination_location is None:
            sys.exit("Error: Unable to retrieve coordinates for pickup or destination.")

        # Create a Folium map centered around pickup location with a higher zoom level
        m = Map(location=pickup_location, zoom_start=17, control_scale=True)

        # Plot pickup and destination on the Folium map
        pickup_marker = Marker(location=pickup_location, popup='Pickup', icon=Icon(color='green'))
        dest_marker = Marker(location=destination_location, popup='Destination', icon=Icon(color='red'))
        m.add_child(pickup_marker)
        m.add_child(dest_marker)

        # Plot a PolyLine connecting pickup and destination
        polyline_coordinates = [pickup_location, destination_location]
        polyline = PolyLine(locations=polyline_coordinates, color='blue', weight=2.5)
        m.add_child(polyline)

        # Add random shops along the polyline
        for _ in range(3):
            random_coord = (
                pickup_location[0] + (destination_location[0] - pickup_location[0]) * random.uniform(0.2, 0.8),
                pickup_location[1] + (destination_location[1] - pickup_location[1]) * random.uniform(0.2, 0.8)
            )
            shop_name = random.choice(["KFC", "McDonald's", "Trends"])
            offer_details = f"Today's Offer at {shop_name}: {random.randint(10, 50)}% off on selected items"

            # Additional information for the popup
            additional_info = "Visit us for amazing deals!"

            # Include shop name, offer details, and additional information in the popup content
            popup_content = f"<b>{shop_name}</b><br>{offer_details}<br><i>{additional_info}</i>"

            shop_marker = Marker(location=random_coord, popup=popup_content, icon=Icon(color='orange'))
            shop_marker.add_child(
                Popup(
                    ShopInfoWidget(shop_name, offer_details),
                    max_width=300
                )
            )
            m.add_child(shop_marker)

        # Save the Folium map as an HTML string
        html_string = m._repr_html_()

        # Create a QWebEngineView to display the HTML string directly in the GUI
        self.browser = QWebEngineView()
        self.browser.setHtml(html_string)

        # Set up the central widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.showMaximized()


def get_coordinates(address):
    geolocator = Nominatim(user_agent="map_gui")

    try:
        location = geolocator.geocode(address)
        return location.latitude, location.longitude
    except AttributeError:
        print(f"Error: Could not find coordinates for address: {address}")
        return None


def read_driver_details_from_csv(filename):
    drivers = {}
    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            drivers[row['id']] = (
                row['name'],
                float(row['rating']),
                int(row['eta']),
                float(row['base_fare']),
                row['contact_number'],
                row['location'],
            )
    return drivers


if __name__ == "__main__":
    app = QApplication([])

    # Create an instance of BrowserWindow
    map_app = BrowserWindow()

    # Create an instance of RideApp with a reference to the BrowserWindow instance
    ride_app = RideApp(map_app)

    # Create a tab widget and add instances of RideApp and BrowserWindow as tabs
    tab_widget = QTabWidget()
    tab_widget.addTab(ride_app, "Ride App")
    tab_widget.addTab(map_app, "Map")

    # Show the tab widget
    tab_widget.show()

    app.exec_()
    sys.exit()
