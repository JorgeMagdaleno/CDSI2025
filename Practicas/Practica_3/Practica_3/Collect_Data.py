import requests
import pandas as pd
import time
from datetime import datetime
import threading
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt

# URL del servidor de sensores
URL = "http://158.97.67.15:8080/sensors.json"

# DataFrame global para almacenar los datos
df = pd.DataFrame(columns=["timestamp", "sensor", "x", "y", "z", "w", "accuracy"])

# Variables de control
is_recording = False  # Indica si se está grabando
start_time = None  # Marca el inicio de la grabación

# Lock para sincronizar el acceso al DataFrame
df_lock = threading.Lock()

# Variable para almacenar el nombre de la carpeta
output_folder = ""

# Set para almacenar los timestamps ya procesados
processed_timestamps = set()


def fetch_sensor_data():
    """Obtiene los datos de sensores desde la URL."""
    try:
        response = requests.get(URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al obtener datos: {e}")
        return None


def process_data(data):
    """Parsea los datos del JSON y los almacena en el DataFrame global."""
    global df, processed_timestamps
    if data is None:
        return

    new_entries = []
    timestamp_now = datetime.now().timestamp()

    for sensor, details in data.items():
        if "data" in details:
            for entry in details["data"]:
                timestamp = entry[0] / 1000  # Convertir milisegundos a segundos
                if timestamp in processed_timestamps:
                    continue  # Skip already processed data
                processed_timestamps.add(timestamp)  # Mark this timestamp as processed

                values = entry[1]
                if sensor == "rot_vector":
                    # El vector de rotación tiene 5 valores: x, y, z, w, accuracy
                    new_entries.append({
                        "timestamp": timestamp,
                        "sensor": sensor,
                        "x": values[0],
                        "y": values[1],
                        "z": values[2],
                        "w": values[3],
                        "accuracy": values[4]
                    })
                else:
                    # Otros sensores tienen 3 valores: x, y, z
                    new_entries.append({
                        "timestamp": timestamp,
                        "sensor": sensor,
                        "x": values[0],
                        "y": values[1],
                        "z": values[2],
                        "w": None,
                        "accuracy": None
                    })

    new_df = pd.DataFrame(new_entries)
    with df_lock:  # Bloquear el acceso al DataFrame mientras se actualiza
        df = pd.concat([df, new_df], ignore_index=True)


def data_collection_thread():
    """Función para recolectar datos en un hilo separado."""
    global is_recording, start_time
    while True:
        if is_recording:
            sensor_data = fetch_sensor_data()
            process_data(sensor_data)
        time.sleep(1)  # Esperar 1 segundo antes de la próxima consulta


def start_recording(window, entry=""):
    """Inicia la recolección de datos."""
    global is_recording, start_time, df, processed_timestamps, output_folder
    if not is_recording:
        if entry != "":
            output_folder = entry
        else:
            output_folder = folder_entry.text()  # Obtener el nombre de la carpeta desde la interfaz
        if not output_folder:
            QMessageBox.warning(window, "Advertencia", "Por favor, ingrese un nombre para la carpeta.")
            return

        QMessageBox.information(window, "Inicio", "La recolección de datos empezará al presionar el botón.")

        is_recording = True
        start_time = datetime.now()
        df = pd.DataFrame(columns=["timestamp", "sensor", "x", "y", "z", "w", "accuracy"])  # Reiniciar el DataFrame
        processed_timestamps = set()  # Reiniciar el conjunto de timestamps procesados

    else:
        QMessageBox.warning(window, "Advertencia", "La recolección de datos ya está en curso.")


def stop_recording(window):
    """Detiene la recolección de datos y guarda los datos en un archivo."""
    global is_recording, start_time, df, output_folder
    if is_recording:
        is_recording = False
        end_time = datetime.now()

        # Crear la carpeta si no existe
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Guardar los datos en un archivo CSV dentro de la carpeta
        filename = f"{output_folder}/sensor_data_{start_time.strftime('%Y%m%d_%H%M%S')}_to_{end_time.strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        QMessageBox.information(window, "Fin", f"La recolección de datos ha finalizado. Los datos se han guardado en {filename}.")
    else:
        QMessageBox.warning(window, "Advertencia", "La recolección de datos no está en curso.")


class DataCollectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recolección de Datos de Sensores")
        self.setGeometry(100, 100, 400, 200)

        # Layout principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Campo de entrada para el nombre de la carpeta
        self.folder_label = QLabel("Nombre de la carpeta:", self)
        self.layout.addWidget(self.folder_label)

        global folder_entry
        folder_entry = QLineEdit(self)
        self.layout.addWidget(folder_entry)

        # Botón para iniciar la recolección
        self.start_button = QPushButton("Iniciar Recolección", self)
        self.start_button.clicked.connect(lambda: start_recording(self))
        self.layout.addWidget(self.start_button)

        # Botón para detener la recolección
        self.stop_button = QPushButton("Detener Recolección", self)
        self.stop_button.clicked.connect(lambda: stop_recording(self))
        self.layout.addWidget(self.stop_button)


if __name__ == "__main__":
    # Iniciar el hilo de recolección de datos
    data_thread = threading.Thread(target=data_collection_thread)
    data_thread.daemon = True  # El hilo se detendrá cuando el programa principal termine
    data_thread.start()

    # Iniciar la aplicación PyQt5
    app = QApplication([])
    window = DataCollectionApp()
    window.show()
    app.exec_()