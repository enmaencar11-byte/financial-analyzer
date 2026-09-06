"""
Análisis horizontal (evolución en el tiempo).
Compara cada partida contra sí misma en ejercicios anteriores.

Todas las operaciones se agrupan por emisor. Sin esa separación, el
primer ejercicio de un emisor se compararía contra el último del emisor
anterior en el archivo, produciendo variaciones sin sentido económico
que no serían visibles a simple vista.
"""

import pandas as pd

from src.utils import division_segura

IDENTIFICADORES = ['empresa', 'anio']


def _partidas(df):
    """Todas las columnas numéricas, excluyendo los identificadores."""
    return [c for c in df.columns if c not in IDENTIFICADORES]


def variacion_interanual(df):
    """
    Variación porcentual de cada partida respecto al ejercicio anterior.

    El primer ejercicio de cada emisor queda en NaN porque no tiene
    período de comparación. Se conserva la fila en lugar de eliminarla,
    para que la salida mantenga la misma cantidad de filas que el resto
    de los análisis y las tablas puedan alinearse por empresa y año.
    """
    df = df.sort_values(IDENTIFICADORES).reset_index(drop=True)
    resultado = df[IDENTIFICADORES].copy()

    for partida in _partidas(df):
        anterior = df.groupby('empresa')[partida].shift(1)
        resultado[partida] = division_segura(df[partida] - anterior, anterior) * 100

    return resultado.round(2)


def numeros_indice(df, anio_base=None):
    """
    Expresa cada partida como índice respecto a un ejercicio base = 100.

    A diferencia de la variación interanual, permite leer el crecimiento
    acumulado del período completo en una sola cifra. Un valor de 128
    indica que la partida creció 28% desde el año base.

    Si no se indica anio_base, se toma el primer ejercicio disponible.
    """
    df = df.sort_values(IDENTIFICADORES).reset_index(drop=True)
    if anio_base is None:
        anio_base = df['anio'].min()

    if anio_base not in df['anio'].values:
        raise ValueError(f'El año base {anio_base} no existe en los datos.')

    resultado = df[IDENTIFICADORES].copy()
    base = df[df['anio'] == anio_base].set_index('empresa')

    for partida in _partidas(df):
        valores_base = df['empresa'].map(base[partida])
        resultado[partida] = division_segura(df[partida], valores_base) * 100

    return resultado.round(2)


def variacion_absoluta(df):
    """
    Diferencia en unidades monetarias respecto al ejercicio anterior.

    Complementa a la variación porcentual: una partida pequeña puede
    crecer 300% sin ser relevante, mientras que una grande que crece 4%
    puede explicar el movimiento principal del balance.
    """
    df = df.sort_values(IDENTIFICADORES).reset_index(drop=True)
    resultado = df[IDENTIFICADORES].copy()

    for partida in _partidas(df):
        anterior = df.groupby('empresa')[partida].shift(1)
        resultado[partida] = (df[partida] - anterior).round(2)

    return resultado