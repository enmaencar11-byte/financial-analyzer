# FinAnalyzer Pro — leverage.py
# ES: calcularemos los ratios que miden la
#     dependencia de la deuda para
#     financiar operaciones de la empresa
# EN: We calculeta the ratios that measures
#     the company's debt dependency

def endeudamiento_total(df):                                           # what percentage was financed with debt?
    return df['pasivo_total'] / df['activo_total']

def deuda_sobre_patrimonio(df):                                        # How many dollars do you owe for every dollar invested?
    return df['pasivo_total'] / df['patrimonio_total']

def cobertura_interes(df):
    return df['utilidad_operativa'] / df['gastos_financieros']         # How many times can you pay the interest with what you earn from the transactions?

