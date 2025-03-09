import sys
import threading
import time
import os
import numpy as np
import pandas as pd
import joblib
from PIL import Image, ImageSequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QMessageBox
)
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt, QTimer

# Importamos las funciones de recolección de datos desde Collect_Data.py
import Collect_Data
from Training_Model import MovementEvaluationSystem


class MovimientoJuego(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Juego de Movimientos")
        self.setGeometry(100, 100, 700, 700)

        # Cargar el sistema de evaluación exportado
        self.movement_system = joblib.load("movement_system.pkl")

        # Lista de movimientos (deben coincidir con los usados en el entrenamiento)
        self.movimientos = ["Curl", "CrossoverArm", "Pendulum"]
        self.indice_movimiento_actual = 0

        # Variables para estadísticas
        self.attempts_data = {mov: [] for mov in self.movimientos}  # calificaciones por movimiento
        self.rating_counts = {"Intente de nuevo": 0, "Bien": 0, "Maravilloso": 0, "Excelente": 0}
        self.total_score = 0.0
        self.total_attempts = 0
        self.start_time = time.time()

        # Configuración de la interfaz
        self.init_ui()

    def init_ui(self):
        # Layout principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Etiqueta para la imagen del movimiento
        self.label_imagen = QLabel(self)
        self.label_imagen.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_imagen)

        # Etiqueta para el nombre del movimiento
        self.label_movimiento = QLabel("", self)
        self.label_movimiento.setAlignment(Qt.AlignCenter)
        self.label_movimiento.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.label_movimiento)

        # Etiqueta para la cuenta regresiva
        self.label_cuenta_regresiva = QLabel("", self)
        self.label_cuenta_regresiva.setAlignment(Qt.AlignCenter)
        self.label_cuenta_regresiva.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.label_cuenta_regresiva)

        # Etiqueta para el mensaje de resultado
        self.label_resultado = QLabel("", self)
        self.label_resultado.setAlignment(Qt.AlignCenter)
        self.label_resultado.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.label_resultado)

        # Etiqueta para el GIF de resultado
        self.label_result_gif = QLabel(self)
        self.label_result_gif.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label_result_gif)

        # Botones de control
        self.boton_intentar = QPushButton("Intentar de nuevo", self)
        self.boton_intentar.clicked.connect(self.intentar_de_nuevo)
        self.boton_intentar.setEnabled(False)
        self.layout.addWidget(self.boton_intentar)

        self.boton_siguiente = QPushButton("Siguiente movimiento", self)
        self.boton_siguiente.clicked.connect(self.siguiente_movimiento)
        self.boton_siguiente.setEnabled(False)
        self.layout.addWidget(self.boton_siguiente)

        # Iniciar el juego
        self.iniciar_juego()

    def iniciar_juego(self):
        self.mostrar_movimiento_actual()
        self.iniciar_recoleccion_datos()
        self.iniciar_cuenta_regresiva()

    def mostrar_movimiento_actual(self):
        movimiento_actual = self.movimientos[self.indice_movimiento_actual]
        self.label_movimiento.setText(f"Movimiento: {movimiento_actual}")

        # Cargar imagen correspondiente (PNG) desde la carpeta "Assets"
        image_path = os.path.join("Assets", f"{movimiento_actual}.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.label_imagen.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
        else:
            self.label_imagen.clear()
            print(f"No se encontró la imagen para {movimiento_actual} en {image_path}.")

    def iniciar_recoleccion_datos(self):
        Collect_Data.output_folder = "temp_data"
        if not os.path.exists(Collect_Data.output_folder):
            os.makedirs(Collect_Data.output_folder)
        Collect_Data.start_recording(self, "temp_data")  # Pasar self como argumento

    def detener_recoleccion_datos(self):
        Collect_Data.stop_recording(self)  # Pasar self como argumento
        files = [f for f in os.listdir(Collect_Data.output_folder) if f.endswith(".csv")]
        if not files:
            return None
        files = sorted(files, key=lambda x: os.path.getctime(os.path.join(Collect_Data.output_folder, x)), reverse=True)
        return os.path.join(Collect_Data.output_folder, files[0])

    def iniciar_cuenta_regresiva(self):
        self.cuenta_regresiva(5)

    def cuenta_regresiva(self, segundos):
        if segundos > 0:
            self.label_cuenta_regresiva.setText(f"Tiempo restante: {segundos} segundos")
            QTimer.singleShot(1000, lambda: self.cuenta_regresiva(segundos - 1))
        else:
            self.label_cuenta_regresiva.setText("¡Movimiento capturado!")
            self.calificar_movimiento()

    def calificar_movimiento(self):
        filename = self.detener_recoleccion_datos()
        if filename is None:
            QMessageBox.critical(self, "Error", "No se pudieron obtener datos de sensor.")
            calificacion = 0
        else:
            df = pd.read_csv(filename)
            features = self.movement_system.extract_features(df)
            features = np.array(features)
            features = self.movement_system.clean_data(features)
            movimiento_actual = self.movimientos[self.indice_movimiento_actual]
            if (movimiento_actual in self.movement_system.centroids and
                    self.movement_system.centroids[movimiento_actual] is not None):
                centroid = self.movement_system.centroids[movimiento_actual]
                calificacion = self.movement_system.compute_similarity(features, centroid, method="inverse_distance")
            else:
                calificacion = 0

        self.mostrar_resultado(calificacion)

    def mostrar_resultado(self, calificacion):
        if calificacion < 0.15:
            mensaje = "Intente de nuevo"
            gif_file = "Intente.gif"
        elif calificacion < 0.20:
            mensaje = "Bien"
            gif_file = "Bien.gif"
        elif calificacion < 0.30:
            mensaje = "Maravilloso"
            gif_file = "Maravilloso.gif"
        else:
            mensaje = "Excelente"
            gif_file = "Excelente.gif"

        self.label_resultado.setText(f"{mensaje} {calificacion:.4f}")

        mov_actual = self.movimientos[self.indice_movimiento_actual]
        self.attempts_data[mov_actual].append(calificacion)
        self.rating_counts[mensaje] += 1
        self.total_score += calificacion
        self.total_attempts += 1

        gif_path = os.path.join("Assets", gif_file)
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            self.label_result_gif.setMovie(movie)
            movie.start()
        else:
            self.label_result_gif.clear()
            print(f"No se encontró el GIF para {mensaje} en {gif_path}.")

        self.boton_intentar.setEnabled(True)
        self.boton_siguiente.setEnabled(True)

    def intentar_de_nuevo(self):
        self.label_resultado.clear()
        self.label_result_gif.clear()
        self.boton_intentar.setEnabled(False)
        self.boton_siguiente.setEnabled(False)
        self.iniciar_recoleccion_datos()
        self.iniciar_cuenta_regresiva()

    def siguiente_movimiento(self):
        self.indice_movimiento_actual = (self.indice_movimiento_actual + 1) % len(self.movimientos)
        self.label_resultado.clear()
        self.label_result_gif.clear()
        self.boton_intentar.setEnabled(False)
        self.boton_siguiente.setEnabled(False)
        self.mostrar_movimiento_actual()
        self.iniciar_recoleccion_datos()
        self.iniciar_cuenta_regresiva()

        if self.indice_movimiento_actual == 0:
            self.mostrar_resumen()

    def mostrar_resumen(self):
        tiempo_total = time.time() - self.start_time
        resumen = "Resumen general:\n\n"
        resumen += "Intentos por movimiento:\n"
        for mov, calificaciones in self.attempts_data.items():
            if calificaciones:
                promedio = sum(calificaciones) / len(calificaciones)
            else:
                promedio = 0
            resumen += f"  {mov}: {len(calificaciones)} intento(s), promedio = {promedio:.4f}\n"
        resumen += f"\nPuntuación total: {self.total_score:.4f}\n"
        resumen += f"Intentos totales: {self.total_attempts}\n\n"
        resumen += "Cantidad por calificación:\n"
        for key, count in self.rating_counts.items():
            resumen += f"  {key}: {count}\n"
        resumen += f"\nTiempo total: {tiempo_total:.2f} segundos"

        QMessageBox.information(self, "Resumen General", resumen)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    juego = MovimientoJuego()
    data_thread = threading.Thread(target=Collect_Data.data_collection_thread)
    data_thread.daemon = True
    data_thread.start()

    juego.show()
    sys.exit(app.exec_())