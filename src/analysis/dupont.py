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

    

# ── Contribución de cada factor a la variación del ROE ───────────

# Factores de cada nivel, en el orden en que aparecen en la identidad.
FACTORES_NIVEL_2 = ['Margen neto', 'Rotación de activos', 'Apalancamiento']
FACTORES_NIVEL_3 = ['Carga fiscal', 'Carga financiera', 'Margen operativo',
                    'Rotación de activos', 'Apalancamiento']


def _variacion(inicial, final):
    """
    Variación relativa entre dos valores de un mismo factor.

    Devuelve un valor nulo cuando el valor inicial es cero o ausente, y
    también cuando ambos valores tienen signos distintos: la variación
    relativa de una magnitud que pasa de negativa a positiva produce un
    número que no admite interpretación económica y que no debe figurar
    en una tabla de resultados.
    """
    if pd.isna(inicial) or pd.isna(final) or inicial == 0:
        return np.nan
    if (inicial > 0) != (final > 0):
        return np.nan
    return final / inicial - 1


def contribucion_factores(df, nivel=3, anio_inicial=None, anio_final=None):
    """
    Mide cuánto aportó cada factor a la variación del ROE entre dos
    ejercicios, por emisor.

    Se reportan dos medidas complementarias.

    La variación relativa de cada factor indica cuánto creció o se redujo
    respecto del ejercicio inicial. Como los factores se multiplican, el
    producto de sus variaciones reproduce la variación del ROE.

    El aporte logarítmico distribuye la variación total del ROE entre los
    factores, de modo que la suma de los aportes es cien por ciento. Se
    obtiene del hecho de que el logaritmo de un producto es la suma de los
    logaritmos de sus términos, por lo que la variación logarítmica del ROE
    equivale a la suma de las variaciones logarítmicas de cada factor. Esta
    descomposición es exacta y no deja residuo, a diferencia de la
    atribución por diferencias simples.

    El aporte logarítmico solo se calcula cuando todos los factores
    conservan signo positivo en ambos ejercicios y el ROE efectivamente
    varía. En caso contrario se devuelve un valor nulo, pues la variación
    relativa de una magnitud que cambia de signo carece de interpretación
    económica.
    """
    if nivel == 2:
        tabla = dupont_nivel_2(df)
        factores = FACTORES_NIVEL_2
    elif nivel == 3:
        tabla = dupont_nivel_3(df)
        factores = FACTORES_NIVEL_3
    else:
        raise ValueError('El nivel debe ser 2 o 3.')

    if anio_inicial is None:
        anio_inicial = int(tabla['anio'].min())
    if anio_final is None:
        anio_final = int(tabla['anio'].max())
    if anio_inicial == anio_final:
        raise ValueError('Los ejercicios inicial y final deben ser distintos.')

    filas = []
    for empresa in tabla['empresa'].unique():
        sub = tabla[tabla['empresa'] == empresa]
        ini = sub[sub['anio'] == anio_inicial]
        fin = sub[sub['anio'] == anio_final]
        if ini.empty or fin.empty:
            continue
        ini = ini.iloc[0]
        fin = fin.iloc[0]

        # La descomposición logarítmica exige que todos los factores y el
        # ROE sean positivos en ambos ejercicios.
        valores = [ini[f] for f in factores] + [fin[f] for f in factores]
        valores += [ini['ROE reportado'], fin['ROE reportado']]
        aplicable = all(pd.notna(v) and v > 0 for v in valores)

        if aplicable:
            variacion_roe_log = np.log(fin['ROE reportado'] / ini['ROE reportado'])
            aplicable = abs(variacion_roe_log) > 1e-12

        for f in factores:
            a, b = ini[f], fin[f]
            variacion = _variacion(a, b)
            aporte = (np.log(b / a) / variacion_roe_log * 100) if aplicable else np.nan
            filas.append({
                'empresa': empresa,
                'factor': f,
                f'valor {anio_inicial}': a,
                f'valor {anio_final}': b,
                'variación': variacion,
                'aporte %': aporte,
            })

        filas.append({
            'empresa': empresa,
            'factor': 'ROE',
            f'valor {anio_inicial}': ini['ROE reportado'],
            f'valor {anio_final}': fin['ROE reportado'],
            'variación': _variacion(ini['ROE reportado'], fin['ROE reportado']),
            'aporte %': 100.0 if aplicable else np.nan,
        })

    return pd.DataFrame(filas)


def mostrar_contribucion(df, nivel=3, anio_inicial=None, anio_final=None, ancho=78):
    """Imprime la tabla de contribuciones por emisor, con formato legible."""
    tabla = contribucion_factores(df, nivel, anio_inicial, anio_final)
    cols_valor = [c for c in tabla.columns if c.startswith('valor ')]

    for empresa in tabla['empresa'].unique():
        sub = tabla[tabla['empresa'] == empresa].copy()
        print()
        print('=' * ancho)
        print(f'  CONTRIBUCIÓN DE FACTORES — NIVEL {nivel} — {empresa}')
        print('=' * ancho)
        salida = sub[['factor'] + cols_valor + ['variación', 'aporte %']].copy()
        for c in cols_valor:
            salida[c] = salida[c].map(lambda v: f'{v:,.4f}' if pd.notna(v) else '—')
        salida['variación'] = salida['variación'].map(
            lambda v: f'{v:+.1%}' if pd.notna(v) else '—')
        salida['aporte %'] = salida['aporte %'].map(
            lambda v: f'{v:+.1f}' if pd.notna(v) else '—')
        print(salida.to_string(index=False))