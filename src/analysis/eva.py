"""
Valor económico agregado.

Contrasta el resultado operativo después de impuestos con el costo del
capital empleado para generarlo:

    EVA = NOPAT − (Capital invertido × WACC)

La expresión admite una forma equivalente que hace explícita su relación
con los indicadores de rentabilidad:

    EVA = (ROIC − WACC) × Capital invertido

El aporte del indicador consiste en incorporar el costo de oportunidad del
patrimonio, que la contabilidad no registra. Una empresa puede presentar
utilidad contable positiva y destruir valor económico, si el rendimiento
del capital invertido no compensa el costo de los recursos empleados.

Como en los módulos anteriores, los parámetros admiten valores sustitutos
para el análisis de sensibilidad. Dado que el EVA depende del WACC, y el
WACC de los parámetros del modelo de costo de capital, el efecto de
modificar una prima de riesgo se propaga hasta el resultado final.
"""

import numpy as np
import pandas as pd

from src.analysis.wacc import capital_total, wacc as calcular_wacc
from src.utils import division_segura
from src.utils import division_segura, formatear_pivote

IDENTIFICADORES = ['empresa', 'anio']

# Tolerancia al comparar las dos formulaciones del indicador. No es cero
# porque la aritmética de punto flotante arrastra diferencias mínimas.
TOLERANCIA_RELATIVA = 1e-9


def capital_invertido(df):
    """
    Deuda financiera más patrimonio.

    Coincide con la base de ponderación del costo promedio ponderado de
    capital, lo que es condición para que el cargo por uso de capital se
    corresponda con el costo que lo produce.
    """
    return capital_total(df)


def nopat(df):
    """Resultado operativo después de impuestos, tomado de los datos."""
    return pd.Series(df['nopat'].to_numpy(), index=pd.RangeIndex(len(df)))


def roic(df):
    """
    Retorno sobre el capital invertido.

    Se calcula aquí sobre la misma base que el cargo por uso de capital,
    de modo que la diferencia entre este indicador y el WACC reproduzca
    exactamente el valor económico agregado por unidad de capital.
    """
    return division_segura(nopat(df), capital_invertido(df),
                           permitir_negativos=False)


def cargo_capital(df, wacc_valor=None, **sustitutos):
    """
    Costo monetario del capital empleado: Capital invertido × WACC.

    Admite un WACC indicado directamente, lo que permite examinar el
    resultado frente a un costo de capital objetivo sin recalcular la
    cadena completa del modelo.
    """
    w = _resolver_wacc(df, wacc_valor, **sustitutos)
    return capital_invertido(df) * w


def _resolver_wacc(df, wacc_valor=None, **sustitutos):
    """Devuelve el WACC indicado, o el calculado a partir del modelo."""
    if wacc_valor is not None:
        return pd.Series(float(wacc_valor), index=pd.RangeIndex(len(df)))
    return calcular_wacc(df, **sustitutos)


def eva(df, wacc_valor=None, **sustitutos):
    """Valor económico agregado: NOPAT menos el cargo por uso de capital."""
    return nopat(df) - cargo_capital(df, wacc_valor, **sustitutos)


def eva_por_diferencial(df, wacc_valor=None, **sustitutos):
    """
    Valor económico agregado por la forma del diferencial:

        (ROIC − WACC) × Capital invertido

    Matemáticamente equivalente a la formulación anterior. Se implementa
    por separado para que ambas puedan contrastarse, lo que constituye una
    verificación de consistencia interna del sistema.
    """
    w = _resolver_wacc(df, wacc_valor, **sustitutos)
    return (roic(df) - w) * capital_invertido(df)


def diferencial(df, wacc_valor=None, **sustitutos):
    """
    Diferencia entre el retorno y el costo del capital: ROIC − WACC.

    Expresa el valor creado por cada unidad de capital invertido. Un valor
    positivo indica creación de valor; uno negativo, destrucción, aun
    cuando el estado de resultados presente utilidad.
    """
    return roic(df) - _resolver_wacc(df, wacc_valor, **sustitutos)


# ── Verificación ─────────────────────────────────────────────────

def verificar_identidad(df, wacc_valor=None, tolerancia=TOLERANCIA_RELATIVA,
                        **sustitutos):
    """
    Comprueba que las dos formulaciones del indicador coincidan.

    La comparación es relativa a la magnitud del capital invertido, porque
    una diferencia absoluta de unas pocas unidades monetarias carece de
    significado sobre bases de miles de millones.

    Las filas en que ambas formulaciones resultan nulas se consideran
    coincidentes: la ausencia de valor es el resultado correcto en ambos
    lados cuando el capital invertido no es positivo.
    """
    directo = eva(df, wacc_valor, **sustitutos)
    diferencial_ = eva_por_diferencial(df, wacc_valor, **sustitutos)
    base = capital_invertido(df).abs()

    diferencia = (directo - diferencial_).abs()
    relativa = division_segura(diferencia, base)
    ambos_nulos = directo.isna() & diferencial_.isna()

    resultado = pd.DataFrame({c: df[c].to_numpy() for c in IDENTIFICADORES},
                             index=pd.RangeIndex(len(df)))
    resultado['EVA directo'] = directo
    resultado['EVA por diferencial'] = diferencial_
    resultado['Diferencia relativa'] = relativa
    resultado['Coincide'] = (relativa <= tolerancia) | ambos_nulos
    return resultado


# ── Tabla de resultados ──────────────────────────────────────────

def calcular(df, wacc_valor=None, decimales=4, **sustitutos):
    """Devuelve los componentes del cálculo y el resultado."""
    resultado = pd.DataFrame({c: df[c].to_numpy() for c in IDENTIFICADORES},
                             index=pd.RangeIndex(len(df)))

    w = _resolver_wacc(df, wacc_valor, **sustitutos)
    ci = capital_invertido(df)
    r = roic(df)

    resultado['Capital invertido'] = ci.round(0)
    resultado['NOPAT'] = nopat(df).round(0)
    resultado['ROIC'] = r.round(decimales)
    resultado['WACC'] = w.round(decimales)
    resultado['Diferencial ROIC − WACC'] = (r - w).round(decimales)
    resultado['Cargo por uso de capital'] = (ci * w).round(0)
    resultado['EVA'] = (nopat(df) - ci * w).round(0)
    resultado['Resultado'] = np.where(
        resultado['EVA'].isna(), 'No aplica',
        np.where(resultado['EVA'] > 0, 'Crea valor', 'Destruye valor'))

    return resultado


def mostrar(df, wacc_valor=None, ancho=78, **sustitutos):
    """Imprime el cálculo con los componentes en filas."""
    tabla = calcular(df, wacc_valor, **sustitutos)
    columnas = [c for c in tabla.columns
                if c not in IDENTIFICADORES and c != 'Resultado']

    largo = tabla.melt(id_vars=IDENTIFICADORES, value_vars=columnas,
                       var_name='componente', value_name='valor')
    pivote = largo.pivot_table(index='componente', columns=IDENTIFICADORES,
                               values='valor', sort=False)

    print()
    print('=' * ancho)
    print('  VALOR ECONÓMICO AGREGADO')
    print('=' * ancho)
    indicados = ', '.join(f'{k}={v}' for k, v in sustitutos.items()
                          if v is not None)
    if wacc_valor is not None:
        indicados = f'WACC={wacc_valor}' + (f', {indicados}' if indicados else '')
    if indicados:
        print(f'  Parámetros sustituidos: {indicados}')
        print('-' * ancho)
    print(formatear_pivote(pivote).to_string())
    print()
    print(tabla[IDENTIFICADORES + ['EVA', 'Resultado']].to_string(index=False))
    print()
    print('EVA = NOPAT − (Capital invertido × WACC) = (ROIC − WACC) × Capital invertido')


def sensibilidad(df, parametro, valores):
    """
    Recalcula el valor económico agregado para varios valores de un
    parámetro, agregando el resultado por emisor.

    Permite identificar el punto en que un emisor pasa de crear a destruir
    valor, que es la lectura más útil del análisis de sensibilidad: no
    tanto el valor puntual del indicador como la distancia al umbral.
    """
    filas = []
    for valor in valores:
        kwargs = ({'wacc_valor': valor} if parametro == 'wacc'
                  else {parametro: valor})
        serie = eva(df, **kwargs)
        temporal = pd.DataFrame({'empresa': df['empresa'].to_numpy(),
                                 'eva': serie.to_numpy()})
        for empresa, grupo in temporal.groupby('empresa', sort=False):
            filas.append({parametro: valor, 'empresa': empresa,
                          'EVA promedio': grupo['eva'].mean(),
                          'Ejercicios con EVA positivo': int((grupo['eva'] > 0).sum())})
    return pd.DataFrame(filas)