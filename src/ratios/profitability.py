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