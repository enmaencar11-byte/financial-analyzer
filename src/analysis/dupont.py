"""
Análisis DuPont: descomposición del rendimiento sobre el patrimonio.

El modelo no calcula información nueva. Toma el ROE y lo factoriza en los
elementos que lo determinan, de modo que pueda distinguirse si una empresa
es rentable por el margen de sus ventas, por la intensidad con que usa sus
activos, o por el grado de apalancamiento con que opera.

Dos emisores con idéntico ROE pueden haberlo alcanzado por vías opuestas.
La descomposición es lo que permite advertirlo.
"""

import numpy as np
import pandas as pd

from src.ratios.activity import rotacion_activos
from src.ratios.leverage import apalancamiento_financiero
from src.ratios.profitability import (
    margen_neto,
    margen_operativo,
    retorno_sobre_activos,
    retorno_sobre_patrimonio,
)
from src.utils import division_segura

IDENTIFICADORES = ['empresa', 'anio']

# Margen de tolerancia al comprobar que el producto de los factores
# reproduce el ROE. No es cero porque la aritmética de punto flotante
# arrastra diferencias del orden de 1e-16 en cada multiplicación.
TOLERANCIA = 1e-9


# ── Factores que no están en el catálogo de razones ──────────────
# Se definen aquí porque solo tienen sentido dentro de la
# descomposición y no constituyen indicadores de uso independiente.

def carga_fiscal(df):
    """
    Utilidad neta / Utilidad antes de impuestos.

    Proporción del resultado que sobrevive a la tributación. En una
    empresa con resultados positivos se sitúa entre cero y uno: un
    valor de 0.72 indica una tasa efectiva del 28%.
    """
    return division_segura(df['utilidad_neta'], df['utilidad_antes_impuestos'])


def carga_financiera(df):
    """
    Utilidad antes de impuestos / Utilidad operativa.

    Proporción del resultado operativo que sobrevive al servicio de la
    deuda. Un valor de 0.65 indica que los gastos financieros netos
    absorbieron el 35% del resultado de la operación.
    """
    return division_segura(df['utilidad_antes_impuestos'], df['utilidad_operativa'])


# ── Los tres niveles ─────────────────────────────────────────────

def dupont_nivel_1(df):
    """
    Primer nivel: el ROE sin descomponer.

    Se incluye por completitud del modelo y porque sirve de referencia
    para verificar los niveles siguientes.
    """
    resultado = df[IDENTIFICADORES].reset_index(drop=True).copy()
    resultado['ROE'] = retorno_sobre_patrimonio(df).reset_index(drop=True)
    return resultado


def dupont_nivel_2(df):
    """
    Segundo nivel: ROE = Margen neto × Rotación de activos × Apalancamiento.

    Separa tres causas: cuánto se gana por cada unidad vendida, cuántas
    unidades se venden por cada unidad de activo, y cuántas unidades de
    activo sostiene cada unidad de patrimonio.

    Se incluye también el ROA, que es el producto de los dos primeros
    factores, porque permite leer el efecto del apalancamiento como la
    diferencia entre ROA y ROE.
    """
    resultado = df[IDENTIFICADORES].reset_index(drop=True).copy()

    resultado['Margen neto'] = margen_neto(df).reset_index(drop=True)
    resultado['Rotación de activos'] = rotacion_activos(df).reset_index(drop=True)
    resultado['Apalancamiento'] = apalancamiento_financiero(df).reset_index(drop=True)

    resultado['ROA'] = retorno_sobre_activos(df).reset_index(drop=True)
    resultado['ROE calculado'] = (resultado['Margen neto']
                                  * resultado['Rotación de activos']
                                  * resultado['Apalancamiento'])
    resultado['ROE reportado'] = retorno_sobre_patrimonio(df).reset_index(drop=True)

    return resultado


def dupont_nivel_3(df):
    """
    Tercer nivel: ROE = Carga fiscal × Carga financiera × Margen operativo
                        × Rotación de activos × Apalancamiento.

    Desagrega el margen neto en tres componentes, lo que permite atribuir
    una variación del ROE a su causa: el desempeño de la operación, el
    costo del financiamiento o la carga tributaria. Un deterioro originado
    en cada uno de los tres exige una respuesta distinta.
    """
    resultado = df[IDENTIFICADORES].reset_index(drop=True).copy()

    resultado['Carga fiscal'] = carga_fiscal(df).reset_index(drop=True)
    resultado['Carga financiera'] = carga_financiera(df).reset_index(drop=True)
    resultado['Margen operativo'] = margen_operativo(df).reset_index(drop=True)
    resultado['Rotación de activos'] = rotacion_activos(df).reset_index(drop=True)
    resultado['Apalancamiento'] = apalancamiento_financiero(df).reset_index(drop=True)

    resultado['ROE calculado'] = (resultado['Carga fiscal']
                                  * resultado['Carga financiera']
                                  * resultado['Margen operativo']
                                  * resultado['Rotación de activos']
                                  * resultado['Apalancamiento'])
    resultado['ROE reportado'] = retorno_sobre_patrimonio(df).reset_index(drop=True)

    return resultado


# ── Verificación de la identidad ─────────────────────────────────

def verificar_identidad(df, tolerancia=TOLERANCIA):
    """
    Comprueba que el producto de los factores reproduzca el ROE.

    La descomposición es una identidad algebraica: si el producto no
    coincide con el ROE, hay un error en alguno de los factores. La
    comprobación es por tanto una verificación de consistencia interna
    del sistema, no un contraste contra una fuente externa.

    Dos precisiones sobre la comparación. La primera es que se admite
    una tolerancia, porque la multiplicación en punto flotante arrastra
    diferencias del orden de 1e-16 que no constituyen error. La segunda
    es que NaN nunca es igual a nada, ni siquiera a sí mismo, de modo
    que una comparación directa marcaría como discrepantes las filas en
    que ambos valores son NaN. Tales filas se consideran coincidentes,
    pues la ausencia de valor es el resultado correcto en ambos lados.

    Devuelve un DataFrame con la diferencia de cada nivel y una columna
    booleana que indica si la identidad se satisface.
    """
    n2 = dupont_nivel_2(df)
    n3 = dupont_nivel_3(df)

    resultado = df[IDENTIFICADORES].reset_index(drop=True).copy()
    roe = n2['ROE reportado']

    for etiqueta, calculado in (('nivel 2', n2['ROE calculado']),
                                ('nivel 3', n3['ROE calculado'])):
        diferencia = (calculado - roe).abs()
        ambos_nulos = calculado.isna() & roe.isna()
        resultado[f'Diferencia {etiqueta}'] = diferencia
        resultado[f'Coincide {etiqueta}'] = (diferencia <= tolerancia) | ambos_nulos

    return resultado


def resumen_verificacion(df, tolerancia=TOLERANCIA):
    """
    Resume la verificación en un diccionario, apto para su registro en
    el capítulo de validación.
    """
    v = verificar_identidad(df, tolerancia)
    return {
        'observaciones': len(v),
        'nivel_2_coinciden': int(v['Coincide nivel 2'].sum()),
        'nivel_3_coinciden': int(v['Coincide nivel 3'].sum()),
        'diferencia_maxima_nivel_2': float(v['Diferencia nivel 2'].max(skipna=True)),
        'diferencia_maxima_nivel_3': float(v['Diferencia nivel 3'].max(skipna=True)),
        'tolerancia': tolerancia,
    }


# ── Presentación ─────────────────────────────────────────────────

def mostrar(df, nivel=2, ancho=78):
    """
    Imprime la descomposición con los factores en filas y los emisores
    y ejercicios en columnas, que es la disposición en que se lee una
    tabla financiera.
    """
    if nivel == 1:
        tabla_ancha = dupont_nivel_1(df)
    elif nivel == 2:
        tabla_ancha = dupont_nivel_2(df)
    elif nivel == 3:
        tabla_ancha = dupont_nivel_3(df)
    else:
        raise ValueError('El nivel debe ser 1, 2 o 3.')

    factores = [c for c in tabla_ancha.columns if c not in IDENTIFICADORES]
    largo = tabla_ancha.melt(id_vars=IDENTIFICADORES, value_vars=factores,
                             var_name='factor', value_name='valor')
    pivote = largo.pivot_table(index='factor', columns=IDENTIFICADORES,
                               values='valor', sort=False)

    print()
    print('=' * ancho)
    print(f'  ANÁLISIS DUPONT — NIVEL {nivel}')
    print('=' * ancho)
    print(pivote.round(4).to_string())