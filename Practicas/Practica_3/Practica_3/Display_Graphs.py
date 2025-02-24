import pandas as pd
import matplotlib.pyplot as plt
import os

def remove_duplicates_and_overlaps(df):
    """
    Elimina datos duplicados y solapamientos en el tiempo.
    """
    # Eliminar filas duplicadas (mismo timestamp y mismos valores)
    df = df.drop_duplicates()

    # Eliminar solapamientos en el tiempo (mantener la primera medición por timestamp)
    df = df.drop_duplicates(subset=['timestamp', 'sensor'], keep='first')

    return df

def plot_sensor_data(file_path):
    """Grafica los datos de todos los sensores en una sola pantalla."""
    # Leer el archivo CSV
    df = pd.read_csv(file_path)

    # Convertir el timestamp a un formato legible
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # Eliminar datos duplicados y solapamientos
    df = remove_duplicates_and_overlaps(df)

    # Ordenar los datos por tiempo
    df = df.sort_values(by='timestamp')

    # Obtener la lista de sensores únicos
    sensors = df['sensor'].unique()

    # Crear una figura con subgráficos para cada sensor
    fig, axes = plt.subplots(len(sensors), 1, figsize=(10, 6 * len(sensors)))
    fig.suptitle(f"Datos de Sensores - Archivo: {os.path.basename(file_path)}", fontsize=16)

    # Si solo hay un sensor, axes no es una lista, así que lo convertimos en una lista
    if len(sensors) == 1:
        axes = [axes]

    # Graficar los datos de cada sensor
    for i, sensor in enumerate(sensors):
        sensor_data = df[df['sensor'] == sensor]

        # Dividir los datos en segmentos continuos
        time_diff = sensor_data['timestamp'].diff() > pd.Timedelta(seconds=1)  # Umbral de 1 segundo
        segments = sensor_data.groupby(time_diff.cumsum())

        # Graficar cada segmento
        for _, segment in segments:
            axes[i].plot(segment['timestamp'], segment['x'], label='X')
            axes[i].plot(segment['timestamp'], segment['y'], label='Y')
            axes[i].plot(segment['timestamp'], segment['z'], label='Z')

        # Configurar el subgráfico
        axes[i].set_title(f"Sensor: {sensor}")
        axes[i].set_xlabel("Tiempo")
        axes[i].set_ylabel("Valor")
        axes[i].legend()
        axes[i].grid()

    # Ajustar el espacio entre subgráficos
    plt.tight_layout()
    plt.show()

def main():
    # Carpeta donde se encuentran los archivos CSV
    input_folder = "datos/Pendulum"  # Cambia esto al nombre de tu carpeta

    # Verificar si la carpeta existe
    if not os.path.exists(input_folder):
        print(f"La carpeta '{input_folder}' no existe.")
        return

    # Obtener la lista de archivos CSV en la carpeta
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]

    if not csv_files:
        print(f"No se encontraron archivos CSV en la carpeta '{input_folder}'.")
        return

    # Graficar los datos de cada archivo CSV
    for csv_file in csv_files:
        file_path = os.path.join(input_folder, csv_file)
        print(f"Graficando datos del archivo: {csv_file}")
        plot_sensor_data(file_path)

if __name__ == "__main__":
    main()