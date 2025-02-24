import threading
import tkinter as tk
from tkinter import messagebox
import time
import os
import numpy as np
import pandas as pd
import joblib
from PIL import Image, ImageTk, ImageSequence

# Importamos las funciones de recolección de datos desde Collect_Data.py
import Collect_Data
from Training_Model import MovementEvaluationSystem


class MovimientoJuego:
    def __init__(self, root):
        self.root = root
        self.root.title("Juego de Movimientos")
        self.root.geometry("700x700")

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

        # Variable para almacenar el identificador del after() del gif animado
        self.gif_after_id = None

        # Frame para imagen y nombre del movimiento
        self.frame_movimiento = tk.Frame(root)
        self.frame_movimiento.pack(pady=20)

        # Etiqueta para la imagen del movimiento
        self.label_imagen = tk.Label(self.frame_movimiento)
        self.label_imagen.pack(side=tk.LEFT, padx=10)

        # Etiqueta para el nombre del movimiento
        self.label_movimiento = tk.Label(self.frame_movimiento, text="", font=("Arial", 24))
        self.label_movimiento.pack(side=tk.LEFT, padx=10)

        # Etiqueta para la cuenta regresiva
        self.label_cuenta_regresiva = tk.Label(root, text="", font=("Arial", 18))
        self.label_cuenta_regresiva.pack(pady=10)

        # Etiqueta para el mensaje de resultado
        self.label_resultado = tk.Label(root, text="", font=("Arial", 18))
        self.label_resultado.pack(pady=10)

        # Etiqueta para el GIF de resultado
        self.label_result_gif = tk.Label(root)
        self.label_result_gif.pack(pady=5)

        # Botones de control
        self.boton_intentar = tk.Button(root, text="Intentar de nuevo", command=self.intentar_de_nuevo, state=tk.DISABLED)
        self.boton_intentar.pack(pady=5)

        self.boton_siguiente = tk.Button(root, text="Siguiente movimiento", command=self.siguiente_movimiento, state=tk.DISABLED)
        self.boton_siguiente.pack(pady=5)

        self.iniciar_juego()

    def iniciar_juego(self):
        self.mostrar_movimiento_actual()
        self.iniciar_recoleccion_datos()
        self.iniciar_cuenta_regresiva()

    def mostrar_movimiento_actual(self):
        movimiento_actual = self.movimientos[self.indice_movimiento_actual]
        self.label_movimiento.config(text=f"Movimiento: {movimiento_actual}")

        # Cargar imagen correspondiente (PNG) desde la carpeta "Assets"
        image_path = os.path.join("Assets", f"{movimiento_actual}.png")
        if os.path.exists(image_path):
            imagen = Image.open(image_path)
            imagen = imagen.resize((150, 150), Image.ANTIALIAS)
            self.image_mov = ImageTk.PhotoImage(imagen)
            self.label_imagen.config(image=self.image_mov)
        else:
            self.label_imagen.config(image="")
            print(f"No se encontró la imagen para {movimiento_actual} en {image_path}.")

    def iniciar_recoleccion_datos(self):
        Collect_Data.output_folder = "temp_data"
        if not os.path.exists(Collect_Data.output_folder):
            os.makedirs(Collect_Data.output_folder)
        Collect_Data.start_recording("temp_data")

    def detener_recoleccion_datos(self):
        Collect_Data.stop_recording()
        files = [f for f in os.listdir(Collect_Data.output_folder) if f.endswith(".csv")]
        if not files:
            return None
        files = sorted(files, key=lambda x: os.path.getctime(os.path.join(Collect_Data.output_folder, x)), reverse=True)
        return os.path.join(Collect_Data.output_folder, files[0])

    def iniciar_cuenta_regresiva(self):
        self.cuenta_regresiva(5)

    def cuenta_regresiva(self, segundos):
        if segundos > 0:
            self.label_cuenta_regresiva.config(text=f"Tiempo restante: {segundos} segundos")
            self.root.after(1000, self.cuenta_regresiva, segundos - 1)
        else:
            self.label_cuenta_regresiva.config(text="¡Movimiento capturado!")
            self.calificar_movimiento()

    def calificar_movimiento(self):
        filename = self.detener_recoleccion_datos()
        if filename is None:
            messagebox.showerror("Error", "No se pudieron obtener datos de sensor.")
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

    def load_gif_frames(self, gif_path):
        frames = []
        try:
            im = Image.open(gif_path)
            for frame in ImageSequence.Iterator(im):
                frame = frame.resize((150, 150), Image.ANTIALIAS)
                frames.append(ImageTk.PhotoImage(frame.copy()))
        except Exception as e:
            print("Error al cargar GIF:", e)
        return frames

    def animate_gif(self, frames, delay=100, counter=0):
        if frames:
            frame = frames[counter]
            self.label_result_gif.config(image=frame)
            counter = (counter + 1) % len(frames)
            # Guardamos el id para poder cancelarlo luego
            self.gif_after_id = self.root.after(delay, self.animate_gif, frames, delay, counter)

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

        self.label_resultado.config(text=f"{mensaje} {calificacion:.4f}")

        mov_actual = self.movimientos[self.indice_movimiento_actual]
        self.attempts_data[mov_actual].append(calificacion)
        self.rating_counts[mensaje] += 1
        self.total_score += calificacion
        self.total_attempts += 1

        gif_path = os.path.join("Assets", gif_file)
        if os.path.exists(gif_path):
            frames = self.load_gif_frames(gif_path)
            self.animate_gif(frames, delay=100)
        else:
            self.label_result_gif.config(image="")
            print(f"No se encontró el GIF para {mensaje} en {gif_path}.")

        self.boton_intentar.config(state=tk.NORMAL)
        self.boton_siguiente.config(state=tk.NORMAL)

    def cancelar_gif(self):
        if self.gif_after_id is not None:
            self.root.after_cancel(self.gif_after_id)
            self.gif_after_id = None
        self.label_result_gif.config(image="")

    def intentar_de_nuevo(self):
        self.label_resultado.config(text="")
        self.cancelar_gif()
        self.boton_intentar.config(state=tk.DISABLED)
        self.boton_siguiente.config(state=tk.DISABLED)
        self.iniciar_recoleccion_datos()
        self.iniciar_cuenta_regresiva()

    def siguiente_movimiento(self):
        self.indice_movimiento_actual = (self.indice_movimiento_actual + 1) % len(self.movimientos)
        self.label_resultado.config(text="")
        self.cancelar_gif()
        self.boton_intentar.config(state=tk.DISABLED)
        self.boton_siguiente.config(state=tk.DISABLED)
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

        resumen_win = tk.Toplevel(self.root)
        resumen_win.title("Resumen General")
        tk.Label(resumen_win, text=resumen, font=("Arial", 14), justify=tk.LEFT).pack(padx=20, pady=20)
        tk.Button(resumen_win, text="Cerrar", command=resumen_win.destroy).pack(pady=10)


if __name__ == "__main__":
    data_thread = threading.Thread(target=Collect_Data.data_collection_thread)
    data_thread.daemon = True
    data_thread.start()
    root = tk.Tk()
    juego = MovimientoJuego(root)
    root.mainloop()
