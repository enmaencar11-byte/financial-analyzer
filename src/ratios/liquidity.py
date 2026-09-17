# FinAnalyzer Pro — liquidity.py
# ES: procesar los cálculos de las razones financieras desde los estados financieros
# EN: Process the calculations of the financial ratios from financial statements


import pandas as pd
from src.utils import division_segura

def razon_corriente(df):                                                # Measures how many pesos the company has for every peso owed in the short term.

     return division_segura(df['activo_corriente_total'], df['pasivo_corriente_total'])

def prueba_acida(df):                                                   #measures is the same tha currente ratio whithout inventories

    return division_segura(df['activo_corriente_total'] - df['inventarios'], df['pasivo_corriente_total'])

def razon_efectivo(df):                                                 #measures the cash at moment

    return division_segura(df['efectivo_equivalentes'], df['pasivo_corriente_total'])

def capital_trabajo(df):                                                 #measures the pillow; danger < 0 < save
    
    return df['activo_corriente_total'] - df['pasivo_corriente_total']

def capital_trabajo_sobre_activos(df):
    """
    Capital de trabajo neto / Activo total.

    Es la primera variable del modelo Z'' de Altman. Mide la proporción
    del activo que se encuentra financiada con recursos de corto plazo
    netos de obligaciones corrientes.
    """
    return division_segura(df['capital_trabajo_neto'], df['activo_total'])


def razon_deuda_corto_plazo(df):
    """
    Deuda financiera de corto plazo / Deuda financiera total.

    Mide la concentración del vencimiento de la deuda. Un valor alto
    indica exposición a riesgo de refinanciamiento en el corto plazo.
    """
    return division_segura(df['deuda_financiera_corto_plazo'],
                           df['deuda_financiera_total'])