"""
Modelo de predicción de insolvencia de Altman.

Implementa la variante Z'' de cuatro variables y su adaptación EM Score
para mercados emergentes, que es la pertinente para emisores dominicanos.

La formulación original de 1968 combinaba cinco variables y requería el
valor de mercado del patrimonio, lo que la restringía a empresas con
cotización bursátil. La variante Z'' sustituye ese término por el valor
contable y elimina la variable de rotación de ventas, cuya sensibilidad
sectorial dificultaba comparar empresas de actividades distintas.
"""

import numpy as np
import pandas as pd

from src.utils import division_segura

IDENTIFICADORES = ['empresa', 'anio']

# Coeficientes de la variante Z'' (Altman).
# No son parámetros ajustables: provienen del análisis discriminante
# sobre la muestra original y modificarlos invalidaría el modelo.
COEF_X1 = 6.56
COEF_X2 = 3.26
COEF_X3 = 6.72
COEF_X4 = 1.05

# Constante de ajuste del EM Score (Altman, Hartzell y Peck, 1995).
# Desplaza la escala para hacerla comparable con las calificaciones
# crediticias internacionales.
AJUSTE_EM = 3.25

# Umbrales de clasificación del Z''. Los del EM Score son los mismos
# desplazados por la constante de ajuste.
UMBRAL_SEGURA = 2.60
UMBRAL_PELIGRO = 1.10

ZONA_SEGURA = 'Segura'
ZONA_GRIS = 'Gris'
ZONA_PELIGRO = 'Peligro'
ZONA_NO_APLICA = 'No aplica'


# ── Las cuatro variables ─────────────────────────────────────────
# X1 y X4 corresponden a indicadores del catálogo, pero se calculan
# aquí de forma explícita para que el módulo sea autocontenido y la
# correspondencia con la formulación del modelo resulte verificable.
# X2 y X3 no figuran en el catálogo de razones.

def x1_capital_trabajo(df):
    """
    X1 = Capital de trabajo neto / Activo total.

    Mide la liquidez estructural: la proporción del activo financiada
    con recursos corrientes netos de obligaciones de corto plazo. Un
    valor negativo indica que la empresa financia activos de largo
    plazo con pasivos corrientes.
    """
    return division_segura(df['capital_trabajo_neto'], df['activo_total'])


def x2_utilidades_retenidas(df):
    """
    X2 = Utilidades retenidas / Activo total.

    Incorpora la trayectoria de la empresa: cuánta ganancia acumuló sin
    distribuir a lo largo de su existencia. Una entidad joven, o una que
    reparte la totalidad de sus resultados, presenta valores bajos con
    independencia de su desempeño corriente. Es la variable que
    introduce el factor de madurez en el modelo.
    """
    return division_segura(df['utilidades_retenidas'], df['activo_total'])


def x3_rentabilidad_operativa(df):
    """
    X3 = Utilidad operativa (EBIT) / Activo total.

    Mide la rentabilidad del activo antes del efecto del financiamiento
    y de la tributación. Por su coeficiente, 6.72, es la variable de
    mayor influencia sobre el puntaje: la incapacidad de generar
    resultado operativo es el predictor más fuerte de insolvencia.
    """
    return division_segura(df['utilidad_operativa'], df['activo_total'])


def x4_solvencia_patrimonial(df):
    """
    X4 = Patrimonio total / Pasivo total.

    Mide la proporción entre recursos propios y ajenos. La variante Z''
    emplea el valor contable del patrimonio, a diferencia del modelo
    original de 1968, que exigía su valor de mercado.
    """
    return division_segura(df['patrimonio_total'], df['pasivo_total'])


# ── Puntajes ─────────────────────────────────────────────────────

def z_doble_prima(df):
    """Puntaje Z'' de cuatro variables."""
    return (COEF_X1 * x1_capital_trabajo(df)
            + COEF_X2 * x2_utilidades_retenidas(df)
            + COEF_X3 * x3_rentabilidad_operativa(df)
            + COEF_X4 * x4_solvencia_patrimonial(df))


def em_score(df):
    """
    Puntaje EM Score para mercados emergentes: Z'' más la constante
    de ajuste.
    """
    return z_doble_prima(df) + AJUSTE_EM


# ── Clasificación ────────────────────────────────────────────────

def clasificar(puntajes, ajustado=False):
    """
    Asigna a cada puntaje su zona de riesgo.

    Si el puntaje corresponde al EM Score, los umbrales se desplazan por
    la misma constante de ajuste, de modo que la clasificación resulta
    idéntica en ambas escalas.

    Un puntaje ausente se clasifica como no aplicable en lugar de
    asignarse a la zona de peligro, para no confundir la ausencia de
    información con un diagnóstico desfavorable.
    """
    desplazamiento = AJUSTE_EM if ajustado else 0.0
    segura = UMBRAL_SEGURA + desplazamiento
    peligro = UMBRAL_PELIGRO + desplazamiento

    puntajes = pd.Series(puntajes)
    zonas = pd.Series(ZONA_GRIS, index=puntajes.index, dtype=object)
    zonas[puntajes > segura] = ZONA_SEGURA
    zonas[puntajes < peligro] = ZONA_PELIGRO
    zonas[puntajes.isna()] = ZONA_NO_APLICA
    return zonas


def umbrales(ajustado=False):
    """Devuelve los umbrales vigentes, para su documentación en el reporte."""
    desplazamiento = AJUSTE_EM if ajustado else 0.0
    return {
        'escala': 'EM Score' if ajustado else "Z''",
        'zona_segura_desde': UMBRAL_SEGURA + desplazamiento,
        'zona_peligro_hasta': UMBRAL_PELIGRO + desplazamiento,
    }


# ── Tabla de resultados ──────────────────────────────────────────

def calcular(df, decimales=4):
    """
    Devuelve las cuatro variables, su aporte ponderado al puntaje, los
    dos puntajes y la zona de clasificación.

    Se incluyen las contribuciones ponderadas porque permiten identificar
    qué variable explica el puntaje de cada emisor, del mismo modo que la
    descomposición DuPont explica el rendimiento sobre el patrimonio.
    """
    resultado = df[IDENTIFICADORES].reset_index(drop=True).copy()

    variables = {
        'X1 Capital de trabajo / Activo': (x1_capital_trabajo, COEF_X1),
        'X2 Utilidades retenidas / Activo': (x2_utilidades_retenidas, COEF_X2),
        'X3 Utilidad operativa / Activo': (x3_rentabilidad_operativa, COEF_X3),
        'X4 Patrimonio / Pasivo': (x4_solvencia_patrimonial, COEF_X4),
    }

    for etiqueta, (funcion, coeficiente) in variables.items():
        valores = funcion(df).reset_index(drop=True)
        resultado[etiqueta] = valores.round(decimales)
        resultado[f'Aporte {etiqueta[:2]}'] = (coeficiente * valores).round(decimales)

    z = z_doble_prima(df).reset_index(drop=True)
    resultado["Z''"] = z.round(decimales)
    resultado['EM Score'] = (z + AJUSTE_EM).round(decimales)
    resultado['Zona'] = clasificar(z)

    return resultado


def resumen_zonas(df):
    """Cuenta las observaciones de cada zona, para el capítulo de resultados."""
    zonas = clasificar(z_doble_prima(df))
    conteo = zonas.value_counts().to_dict()
    for zona in (ZONA_SEGURA, ZONA_GRIS, ZONA_PELIGRO, ZONA_NO_APLICA):
        conteo.setdefault(zona, 0)
    conteo['total'] = len(zonas)
    return conteo


def mostrar(df, ancho=78):
    """
    Imprime el resultado con las variables en filas y los emisores y
    ejercicios en columnas.
    """
    tabla = calcular(df)
    columnas = [c for c in tabla.columns if c not in IDENTIFICADORES and c != 'Zona']

    largo = tabla.melt(id_vars=IDENTIFICADORES, value_vars=columnas,
                       var_name='concepto', value_name='valor')
    pivote = largo.pivot_table(index='concepto', columns=IDENTIFICADORES,
                               values='valor', sort=False)

    print()
    print('=' * ancho)
    print("  MODELO Z'' DE ALTMAN — EM SCORE PARA MERCADOS EMERGENTES")
    print('=' * ancho)
    print(pivote.to_string())
    print()
    print('Zona de clasificación:')
    print(tabla[IDENTIFICADORES + ["Z''", 'EM Score', 'Zona']].to_string(index=False))
    print()
    u = umbrales()
    print(f"Umbrales Z'': segura por encima de {u['zona_segura_desde']}, "
          f"peligro por debajo de {u['zona_peligro_hasta']}.")
    u = umbrales(ajustado=True)
    print(f"Umbrales EM Score: segura por encima de {u['zona_segura_desde']}, "
          f"peligro por debajo de {u['zona_peligro_hasta']}.")