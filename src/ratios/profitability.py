# FinAnalyzer Pro — profitability.py
# ES: procesar los cálculos de los ratios financieras de margenes rentabidad desde los estados financieros
# EN: Process the calculations of the financial ratios de profitability from financial statements

import pandas as pd
from src.utils import division_segura



def margen_bruto(df):                                                  # What profitable is the product or service?
    return division_segura(df['utilidad_bruta'], df['ventas_netas'])                   

def margen_operativo(df):                                               # what eficient is the operation?
    return division_segura(df['utilidad_operativa'], df['ventas_netas'])

def margen_neto(df):                                                 # what is the profit?
    return division_segura(df['utilidad_neta'], df['ventas_netas'])

def retorno_sobre_activos(df):                                          #ROA
    return division_segura(df['utilidad_neta'], df['activo_total'])

def retorno_sobre_patrimonio(df):
    # Un patrimonio negativo (pérdidas acumuladas superiores al capital)
    # produce un ROE positivo por doble negación, lo que presentaría como
    # rentable a una empresa técnicamente insolvente. Se devuelve NaN,
    # siguiendo la práctica de los proveedores de datos financieros de
    # reportar el indicador como no significativo en ese escenario.
    return division_segura(df['utilidad_neta'], df['patrimonio_total'],
                           permitir_negativos=False)

def margen_ebitda(df):
    """
    EBITDA / Ventas netas.

    Indicador publicado por las agencias calificadoras y utilizado en el
    segundo nivel del protocolo de validación. Mide la rentabilidad
    operativa antes del efecto de la política de depreciación.
    """
    return division_segura(df['ebitda'], df['ventas_netas'])


def margen_nopat(df):
    """Resultado operativo después de impuestos / Ventas netas."""
    return division_segura(df['nopat'], df['ventas_netas'])


def roic(df):
    """
    Retorno sobre el capital invertido: NOPAT / Capital invertido.

    El capital invertido se define como deuda financiera total más
    patrimonio. A diferencia del ROA, excluye el financiamiento
    espontáneo de proveedores, que no tiene costo explícito. Es el
    indicador que debe contrastarse contra el WACC para determinar si
    la empresa crea o destruye valor económico.
    """
    capital_invertido = df['deuda_financiera_total'] + df['patrimonio_total']
    return division_segura(df['nopat'], capital_invertido,
                           permitir_negativos=False)


def retorno_sobre_capital_empleado(df):
    """
    ROCE: Utilidad operativa / (Activo total - Pasivo corriente).

    Mide el rendimiento del capital de largo plazo empleado en el
    negocio, antes del efecto del apalancamiento y de los impuestos.
    """
    capital_empleado = df['activo_total'] - df['pasivo_corriente_total']
    return division_segura(df['utilidad_operativa'], capital_empleado,
                           permitir_negativos=False)