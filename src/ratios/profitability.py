# FinAnalyzer Pro — profitability.py
# ES: procesar los cálculos de los ratios financieras de margenes rentabidad desde los estados financieros
# EN: Process the calculations of the financial ratios de profitability from financial statements

import pandas as pd



def margen_bruto(df):                                                  # What profitable is the product or service?
    return df['utilidad_bruta'] / df['ventas_netas']                    

def margen_operativo(df):                                               # what eficient is the operation?
    return df['utilidad_operativa'] / df['ventas_netas']

def margen_neto(df):                                                 # what is the profit?
    return df['utilidad_neta'] / df['ventas_netas']

def retorno_sobre_activos(df):                                          #ROA
    return df['utilidad_neta'] / df['activo_total']

def retorno_sobre_patrimonio(df):                                        # ROE
    return df['utilidad_neta'] / df['patrimonio_total']