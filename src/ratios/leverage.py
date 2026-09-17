# FinAnalyzer Pro — leverage.py
# ES: calcularemos los ratios que miden la
#     dependencia de la deuda para
#     financiar operaciones de la empresa
# EN: We calculeta the ratios that measures
#     the company's debt dependency

from src.utils import division_segura

def endeudamiento_total(df):                                           # what percentage was financed with debt?
    return division_segura(df['pasivo_total'], df['activo_total'])

def deuda_sobre_patrimonio(df):                                        # How many dollars do you owe for every dollar invested?
    return division_segura(df['pasivo_total'], df['patrimonio_total'],
                           permitir_negativos=False)

def cobertura_interes(df):
    return division_segura(df['utilidad_operativa'], df['gastos_financieros'])         # How many times can you pay the interest with what you earn from the transactions?

def cobertura_interes_ebitda(df):
    return division_segura(df['ebitda'], df['gastos_financieros'])