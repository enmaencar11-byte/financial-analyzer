# FinAnalyzer Pro — data_loader.py
# ES: Carga y valida el archivo CSV de estados financieros
# EN: Loads and validates the financial statements CSV file

import pandas as pd                                     #  import pandas — for to read CSV.
from config import TODAS_LAS_COLUMNAS                   # import the column list dinfine in config.py- for know what column the file has

def cargar_datos(ruta_csv):                             # Loads and validates the financial statements
    try:                                             
        df = pd.read_csv(ruta_csv)
    except FileNotFoundError:                           # se ejecuta en caso de que el archivo no se encuentre
        raise FileNotFoundError(
            f'Archivo no encontrando: {ruta_csv}\n'
            f'verifica que la ruta sea la correcta y vuelve a empezar.'
        )
    columnas_faltantes = [
        col for col in TODAS_LAS_COLUMNAS               #take a lits 
        if col not in df.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            f'Al archivo CVS le faltan las siguientes columnas:\n'
            f'{columnas_faltantes}\n'
            f'Verifica lo que pusiste en la plantilla de Excel.'
        )
    print(f'Archivo cargado correctamente:{len(df)} filas, {len(df.columns)} columnas')
    return df                                           #
