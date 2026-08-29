"""
Utilidades transversales de FinAnalyzer Pro.
Shared helper functions used across all analysis modules.
"""

import numpy as np
import pandas as pd


def division_segura(numerador, denominador, permitir_negativos=True):
    """
    Divide dos Series de pandas evitando la propagación de valores infinitos.

    En pandas, dividir entre cero no genera una excepción: devuelve inf o -inf
    y la ejecución continúa. Ese valor contamina cualquier promedio, gráfico o
    tabla que lo incluya. Esta función lo convierte en NaN, que se interpreta
    como "no aplica" y es excluido automáticamente por las funciones de pandas.

    Caso típico en la muestra: un emisor de servicios que reporta inventarios
    en cero haría que la rotación de inventarios devuelva inf.

    Parámetros
    ----------
    numerador : pd.Series
        Serie del numerador del ratio.
    denominador : pd.Series
        Serie del denominador del ratio.
    permitir_negativos : bool, opcional
        Si es False, los denominadores negativos también se convierten en NaN.
        Por defecto True (se calculan y se interpretan en el análisis).

    Retorna
    -------
    pd.Series
        Resultado de la división, con NaN donde el denominador es inválido.
    """
    numerador = pd.Series(numerador)
    denominador = pd.Series(denominador)

    # Los ceros del denominador se convierten en NaN ANTES de dividir.
    # pandas propaga el NaN automáticamente, sin necesidad de condicionales.
    denominador_limpio = denominador.replace(0, np.nan)

    # DECISIÓN METODOLÓGICA (documentar en el capítulo de metodología):
    # Los denominadores negativos se permiten por defecto. Un patrimonio
    # negativo (pérdidas acumuladas que superan el capital) produce un ROE
    # positivo por doble negación, matemáticamente correcto pero engañoso.
    # Se conserva el valor y se señala en la interpretación, en lugar de
    # ocultarlo.
    if not permitir_negativos:
        denominador_limpio = denominador_limpio.where(denominador_limpio > 0, np.nan)

    return numerador / denominador_limpio


def a_porcentaje(serie, decimales=2):
    """
    Convierte una serie de proporciones a porcentaje.

    Ejemplo: 0.1543 -> 15.43

    Parámetros
    ----------
    serie : pd.Series
        Serie expresada como proporción.
    decimales : int, opcional
        Cantidad de decimales a conservar. Por defecto 2.

    Retorna
    -------
    pd.Series
        Serie expresada en puntos porcentuales.
    """
    return (pd.Series(serie) * 100).round(decimales)