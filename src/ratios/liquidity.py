# FinAnalyzer Pro — liquidity.py
# ES: procesar los cálculos de las razones financieras desde los estados financieros
# EN: Process the calculations of the financial ratios from financial statements


import pandas as pd

def razon_corriente(df):                                                # Measures how many pesos the company has for every peso owed in the short term.

    return df['activo_corriente_total'] / df['pasivo_corriente_total']

def prueba_acida(df):                                                   #measures is the same tha currente ratio whithout inventories

    return (df['activo_corriente_total'] - df['inventarios']) / df['pasivo_corriente_total']

def razon_efectivo(df):                                                 #measures the cash at moment

    return df['efectivo_equivalentes'] / df['pasivo_corriente_total']

def capital_trabajo(df):                                                 #measures the pillow; danger < 0 < save
    
    return df['activo_corriente_total'] - df['pasivo_corriente_total']