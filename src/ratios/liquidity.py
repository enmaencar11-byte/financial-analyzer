# FinAnalyzer Pro — liquidity.py
# ES: procesar los cálculos de las razones finacieras
# EN: Process the calculations of the financial ratios

import pandas as pd

def razon_corriente(df):                                                # Measures how many pesos the company has for every peso owed in the short term.

    return df['activo_corriente_total'] / df['pasivo_corriente_total']

def prueba_acida(df):                                                   #measures is the same tha currente ratio whithout inventories

    return (df['activo_corriente_total'] - df['inventarios']) / df['pasivo_corriente_total']

