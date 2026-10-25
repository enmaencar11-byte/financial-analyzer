"""
Carga de los parámetros externos que el modelo de costo de capital
requiere y que no provienen de los estados financieros.

Los parámetros se mantienen en dos archivos separados, cada uno con una
sola fuente de verdad.

Los parámetros de mercado son idénticos para todos los emisores de un
mismo ejercicio: la tasa libre de riesgo de un año no depende de la
empresa que se analice. Registrarlos una vez por año, y no una vez por
emisor, elimina la posibilidad de que una diferencia de transcripción
produzca costos de capital distintos para el mismo período.

Los parámetros sectoriales sí dependen del emisor, en tanto el
coeficiente de riesgo sistemático desapalancado corresponde al sector de
actividad. El sector asignado a cada emisor queda registrado de forma
explícita, pues constituye una decisión metodológica que debe poder
justificarse.
"""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_DATOS = RAIZ / 'data'

ARCHIVO_MERCADO = DIR_DATOS / 'parametros_mercado.csv'
ARCHIVO_SECTOR = DIR_DATOS / 'parametros_sector.csv'

COLUMNAS_MERCADO = ['anio', 'tasa_libre_riesgo',
                    'prima_riesgo_mercado', 'prima_riesgo_pais']
COLUMNAS_SECTOR = ['empresa', 'sector', 'beta_desapalancado']


def _leer(ruta, columnas, descripcion):
    """
    Lee un archivo de parámetros y comprueba que traiga sus columnas.

    La ruta se convierte a Path para admitir indistintamente una cadena
    de texto o un objeto de ruta.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(
            f'No se encontró el archivo de {descripcion}: {ruta}\n'
            f'Debe contener las columnas: {", ".join(columnas)}')

    tabla = pd.read_csv(ruta)
    faltantes = [c for c in columnas if c not in tabla.columns]
    if faltantes:
        raise ValueError(f'{ruta.name}: faltan las columnas {faltantes}')
    return tabla[columnas]


def cargar_mercado(ruta=ARCHIVO_MERCADO):
    """Parámetros de mercado, una fila por ejercicio."""
    return _leer(ruta, COLUMNAS_MERCADO, 'parámetros de mercado')


def cargar_sector(ruta=ARCHIVO_SECTOR):
    """Parámetros sectoriales, una fila por emisor."""
    return _leer(ruta, COLUMNAS_SECTOR, 'parámetros sectoriales')


def incorporar(df, ruta_mercado=ARCHIVO_MERCADO, ruta_sector=ARCHIVO_SECTOR):
    """
    Añade los parámetros externos al conjunto de datos financieros.

    La unión es por ejercicio para los parámetros de mercado y por emisor
    para los sectoriales. Si algún emisor o ejercicio quedara sin
    parámetro, el proceso se detiene: un costo de capital calculado sobre
    parámetros ausentes sería un resultado sin fundamento, y es preferible
    que el sistema falle de forma visible a que entregue una cifra que
    nadie podría justificar.
    """
    mercado = cargar_mercado(ruta_mercado)
    sector = cargar_sector(ruta_sector)

    resultado = df.merge(mercado, on='anio', how='left')
    resultado = resultado.merge(sector, on='empresa', how='left')

    sin_mercado = sorted(resultado.loc[resultado['tasa_libre_riesgo'].isna(),
                                       'anio'].unique().tolist())
    sin_sector = sorted(resultado.loc[resultado['beta_desapalancado'].isna(),
                                      'empresa'].unique().tolist())

    problemas = []
    if sin_mercado:
        problemas.append(f'  Ejercicios sin parámetros de mercado: {sin_mercado}')
    if sin_sector:
        problemas.append(f'  Emisores sin parámetro sectorial: {sin_sector}')
    if problemas:
        raise ValueError('Faltan parámetros externos:\n' + '\n'.join(problemas))

    return resultado


def plantilla_mercado(anios):
    """
    Devuelve una tabla vacía de parámetros de mercado, para los ejercicios
    indicados. Sirve para generar el archivo la primera vez.
    """
    return pd.DataFrame({
        'anio': list(anios),
        'tasa_libre_riesgo': [None] * len(anios),
        'prima_riesgo_mercado': [None] * len(anios),
        'prima_riesgo_pais': [None] * len(anios),
    })


def plantilla_sector(emisores):
    """Devuelve una tabla vacía de parámetros sectoriales."""
    return pd.DataFrame({
        'empresa': list(emisores),
        'sector': [None] * len(emisores),
        'beta_desapalancado': [None] * len(emisores),
    })