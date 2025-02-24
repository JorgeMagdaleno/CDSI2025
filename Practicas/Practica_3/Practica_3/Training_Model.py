import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import joblib


class MovementEvaluationSystem:
    def __init__(self, data_folder="datos", test_folder="test",
                 movements=["CrossoverArm", "Curl", "Pendulum"],
                 sensors=["accel", "gyro"]):
        self.data_folder = data_folder
        self.test_folder = test_folder
        self.movements = movements
        self.sensors = sensors
        self.classification_model = None
        self.centroids = {}

    def load_and_preprocess_data(self, folder):
        """Carga y preprocesa los datos (concatenando archivos CSV) de un movimiento."""
        data = []
        for file in os.listdir(folder):
            if file.endswith(".csv"):
                file_path = os.path.join(folder, file)
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                data.append(df)
        if data:
            return pd.concat(data, ignore_index=True)
        else:
            return pd.DataFrame()

    def extract_features(self, df):
        """
        Extrae características básicas (media, desviación, 'energía') para cada sensor.
        Se usan los ejes x, y, z para cada sensor definido.
        """
        features = []
        for sensor in self.sensors:
            sensor_data = df[df['sensor'] == sensor]
            if not sensor_data.empty:
                features.extend([
                    sensor_data['x'].mean(), sensor_data['y'].mean(), sensor_data['z'].mean(),
                    sensor_data['x'].std(), sensor_data['y'].std(), sensor_data['z'].std(),
                    np.sqrt((sensor_data['x'] ** 2 + sensor_data['y'] ** 2 + sensor_data['z'] ** 2)).mean(),
                ])
            else:
                # Rellenar con ceros si no hay datos para el sensor
                features.extend([0.0] * 7)
        return features

    def clean_data(self, X):
        """Limpia los datos reemplazando valores NaN e infinitos."""
        return np.nan_to_num(X, nan=0.0, posinf=1e10, neginf=-1e10)

    def compute_similarity(self, test_features, centroid, method="inverse_distance"):
        """
        Calcula la similitud entre el vector de características de prueba y el centroide
        usando la distancia euclidiana y transformándola a una medida de similitud.
        - "inverse_distance": similarity = 1/(1 + distancia)
        - "exp": similarity = exp(-distancia)
        """
        distance = np.linalg.norm(test_features - centroid)
        if method == "inverse_distance":
            similarity = 1 / (1 + distance)
        elif method == "exp":
            similarity = np.exp(-distance)
        else:
            similarity = 1 / (1 + distance)
        return similarity

    def train(self):
        """
        Entrena el modelo de clasificación y calcula el centroide (promedio de las
        características) para cada movimiento usando los datos de la carpeta 'datos'.
        """
        X_classification = []
        y_classification = []
        X_evaluation = {movement: [] for movement in self.movements}

        for movement in self.movements:
            movement_folder = os.path.join(self.data_folder, movement)
            movement_data = self.load_and_preprocess_data(movement_folder)
            if movement_data.empty:
                print(f"No se encontraron datos para {movement} en {self.data_folder}.")
                continue

            # Características globales para el modelo de clasificación
            features = self.extract_features(movement_data)
            X_classification.append(features)
            y_classification.append(movement)

            # Características de cada archivo individual para evaluar similitud
            for file in os.listdir(movement_folder):
                if file.endswith(".csv"):
                    file_path = os.path.join(movement_folder, file)
                    df = pd.read_csv(file_path)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                    features = self.extract_features(df)
                    X_evaluation[movement].append(features)

        X_classification = np.array(X_classification)
        y_classification = np.array(y_classification)
        X_classification = self.clean_data(X_classification)

        print("Entrenando el modelo de clasificación...")
        self.classification_model = make_pipeline(StandardScaler(),
                                                  RandomForestClassifier(n_estimators=100, random_state=42))
        self.classification_model.fit(X_classification, y_classification)

        # Calcular el centroide (promedio) para cada movimiento
        for movement in self.movements:
            if X_evaluation[movement]:
                X_eval = np.array(X_evaluation[movement])
                X_eval = self.clean_data(X_eval)
                self.centroids[movement] = np.mean(X_eval, axis=0)
            else:
                self.centroids[movement] = None
                print(f"No hay datos de evaluación para {movement}.")
        print("Entrenamiento completado.")

    def evaluate_individual_movements(self):
        """
        Evalúa cada archivo de prueba en las carpetas individuales (por movimiento)
        calculando la similitud entre sus características y el centroide correspondiente.
        """
        for movement in self.movements:
            movement_folder = os.path.join(self.test_folder, movement)
            if not os.path.exists(movement_folder):
                print(f"No se encontraron datos de prueba para {movement}.")
                continue

            print(f"\nEvaluando movimientos individuales para {movement}...")
            X_test = []
            file_names = []

            for file in os.listdir(movement_folder):
                if file.endswith(".csv"):
                    file_path = os.path.join(movement_folder, file)
                    df = pd.read_csv(file_path)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                    features = self.extract_features(df)
                    X_test.append(features)
                    file_names.append(file)

            if not X_test:
                print(f"No hay archivos CSV en {movement_folder}.")
                continue

            X_test = np.array(X_test)
            X_test = self.clean_data(X_test)

            centroid = self.centroids[movement]
            for i, test_features in enumerate(X_test):
                similarity = self.compute_similarity(test_features, centroid, method="inverse_distance")
                print(f"Calificación para {file_names[i]} en {movement}: {similarity:.2f}")

    def evaluate_mixed_movements(self):
        """
        Evalúa la clasificación de archivos CSV mezclados en la carpeta 'mixed'.
        Se asume que el nombre del archivo contiene la etiqueta del movimiento.
        """
        mixed_folder = os.path.join(self.test_folder, "mixed")
        if not os.path.exists(mixed_folder):
            print("No se encontraron datos de prueba mixtos.")
            return

        print("\nEvaluando clasificación de movimientos mixtos...")
        X_test = []
        y_test = []

        for file in os.listdir(mixed_folder):
            if file.endswith(".csv"):
                file_path = os.path.join(mixed_folder, file)
                df = pd.read_csv(file_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                features = self.extract_features(df)
                X_test.append(features)
                # Se extrae la etiqueta del nombre del archivo (por ejemplo, "Curl_01.csv")
                label = None
                for movement in self.movements:
                    if movement.lower() in file.lower():
                        label = movement
                        break
                if label is None:
                    label = "Desconocido"
                y_test.append(label)

        if not X_test:
            print("No hay archivos CSV en la carpeta 'mixed'.")
            return

        X_test = np.array(X_test)
        y_test = np.array(y_test)
        X_test = self.clean_data(X_test)

        y_pred = self.classification_model.predict(X_test)
        print("Precisión del modelo de clasificación en datos mixtos:", accuracy_score(y_test, y_pred))
        print("Reporte de clasificación:\n", classification_report(y_test, y_pred))

    def export_system(self, filename="movement_system.pkl"):
        """
        Exporta toda la instancia del sistema (modelos, centroides y funciones de preprocesado
        y calificación) para ser cargada en otro código.
        """
        joblib.dump(self, filename)
        print(f"Sistema exportado exitosamente en {filename}.")


if __name__ == "__main__":
    # Crear y entrenar el sistema
    system = MovementEvaluationSystem()
    system.train()

    # Exportar el sistema completo (modelos, preprocesado y sistema de calificación)
    system.export_system()  # Se guarda en "movement_system.pkl" por defecto

    # Evaluaciones:
    system.evaluate_individual_movements()
    system.evaluate_mixed_movements()
