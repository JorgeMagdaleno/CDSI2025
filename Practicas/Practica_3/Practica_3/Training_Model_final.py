import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import joblib  # Para guardar y cargar modelos

# Configuración
SENSORS = ["accel", "gyro"]  # Sensores a utilizar

# Función para cargar y preprocesar datos
def load_and_preprocess_data(file_path):
    """Carga y preprocesa los datos de un archivo CSV."""
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    return df

# Función para extraer características de los datos de sensores
def extract_features(df):
    """Extrae características básicas (media, desviación, 'energía') para cada sensor."""
    features = []
    for sensor in SENSORS:
        sensor_data = df[df['sensor'] == sensor]
        if not sensor_data.empty:
            features.extend([
                sensor_data['x'].mean(), sensor_data['y'].mean(), sensor_data['z'].mean(),
                sensor_data['x'].std(), sensor_data['y'].std(), sensor_data['z'].std(),
                np.sqrt((sensor_data['x']**2 + sensor_data['y']**2 + sensor_data['z']**2)).mean(),
            ])
        else:
            # Si no hay datos para el sensor, se rellenan 7 valores en cero
            features.extend([0.0] * 7)
    return features

# Función para limpiar los datos (reemplaza NaN e infinitos)
def clean_data(X):
    """Limpia los datos reemplazando NaN e infinitos."""
    return np.nan_to_num(X, nan=0.0, posinf=1e10, neginf=-1e10)

# Función para entrenar el modelo de clasificación y los modelos de evaluación por movimiento
def train_model(data_folder, movements):
    """
    Entrena el modelo de clasificación y un modelo de evaluación (regresión) por cada movimiento.
    Guarda los modelos en archivos.
    """
    X_classification = []  # Características globales de cada movimiento
    y_classification = []  # Etiqueta (nombre del movimiento)
    evaluation_models = {}  # Modelos de evaluación por movimiento

    # Cargar datos de cada movimiento
    for movement in movements:
        movement_folder = os.path.join(data_folder, movement)
        movement_data = pd.DataFrame()
        for file in os.listdir(movement_folder):
            if file.endswith(".csv"):
                file_path = os.path.join(movement_folder, file)
                df = load_and_preprocess_data(file_path)
                movement_data = pd.concat([movement_data, df], ignore_index=True)

        if movement_data.empty:
            print(f"No se encontraron datos para {movement} en {data_folder}.")
            continue

        # Extraer características a nivel global (para clasificación)
        features = extract_features(movement_data)
        X_classification.append(features)
        y_classification.append(movement)

        # Extraer características de cada archivo individual (para evaluación)
        X_eval = []
        y_eval = []
        for file in os.listdir(movement_folder):
            if file.endswith(".csv"):
                file_path = os.path.join(movement_folder, file)
                df = load_and_preprocess_data(file_path)
                features = extract_features(df)
                X_eval.append(features)
                y_eval.append(1.0)  # Suponemos que el movimiento esperado tiene una calificación de 1.0

        if not X_eval:
            print(f"No hay datos de evaluación para {movement}.")
            continue

        # Entrenar un modelo de evaluación (regresión) para este movimiento
        X_eval = np.array(X_eval)
        y_eval = np.array(y_eval)
        X_eval = clean_data(X_eval)

        evaluation_model = make_pipeline(StandardScaler(), RandomForestRegressor(n_estimators=100, random_state=42))
        evaluation_model.fit(X_eval, y_eval)
        evaluation_models[movement] = evaluation_model

    # Convertir a arrays de numpy y limpiar los datos
    X_classification = np.array(X_classification)
    y_classification = np.array(y_classification)
    X_classification = clean_data(X_classification)

    # Entrenar el modelo de clasificación
    print("Entrenando el modelo de clasificación...")
    classification_model = make_pipeline(StandardScaler(), RandomForestClassifier(n_estimators=100, random_state=42))
    classification_model.fit(X_classification, y_classification)

    # Guardar los modelos
    joblib.dump(classification_model, "classification_model.pkl")
    joblib.dump(evaluation_models, "evaluation_models.pkl")
    print("Modelos guardados en 'classification_model.pkl' y 'evaluation_models.pkl'.")

# Función para cargar los modelos
def load_model():
    """Carga el modelo de clasificación y los modelos de evaluación desde archivos."""
    classification_model = joblib.load("classification_model.pkl")
    evaluation_models = joblib.load("evaluation_models.pkl")
    return classification_model, evaluation_models

# Función para predecir y calificar un nuevo archivo CSV
def predict_and_score(file_path, classification_model, evaluation_models):
    """
    Prepara los datos de un archivo CSV, realiza la predicción y calcula la calificación.
    """
    # Cargar y preprocesar los datos
    df = load_and_preprocess_data(file_path)
    features = extract_features(df)
    features = clean_data(np.array([features]))

    # Realizar la predicción
    predicted_movement = classification_model.predict(features)[0]

    # Calcular la calificación usando el modelo de evaluación correspondiente
    evaluation_model = evaluation_models[predicted_movement]
    score = evaluation_model.predict(features)[0]

    return predicted_movement, score

# Ejemplo de uso
if __name__ == "__main__":
    # Entrenar el modelo y guardarlo
    DATA_FOLDER = "datos"  # Carpeta con los datos de entrenamiento
    MOVEMENTS = ["CrossoverArm", "Curl", "Pendulum"]  # Nombres de los movimientos
    train_model(DATA_FOLDER, MOVEMENTS)

    # Cargar el modelo y los modelos de evaluación
    classification_model, evaluation_models = load_model()

    # Predecir y calificar un nuevo archivo CSV
    TEST_FILE = "test/mixed/CrossoverArm/sensor_data_20250223_191559_to_20250223_191605.csv"  # Ruta al archivo de prueba
    predicted_movement, score = predict_and_score(TEST_FILE, classification_model, evaluation_models)
    print(f"Movimiento predicho: {predicted_movement}, Calificación: {score:.2f}")