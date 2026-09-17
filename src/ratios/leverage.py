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

def endeudamiento_financiero(df):
    """
    Deuda financiera total / Patrimonio.

    Indicador publicado por las agencias calificadoras. Se distingue del
    endeudamiento total en que considera únicamente la deuda con costo
    explícito, excluyendo el financiamiento espontáneo de proveedores.
    """
    return division_segura(df['deuda_financiera_total'], df['patrimonio_total'],
                           permitir_negativos=False)


def deuda_financiera_ebitda(df):
    """
    Deuda financiera total / EBITDA.

    Expresa el número de ejercicios de generación operativa que serían
    necesarios para cancelar la deuda financiera. Indicador publicado
    por las agencias calificadoras.
    """
    return division_segura(df['deuda_financiera_total'], df['ebitda'],
                           permitir_negativos=False)


def deuda_neta_ebitda(df):
    """
    (Deuda financiera total - Efectivo) / EBITDA.

    Variante del anterior que descuenta las disponibilidades líquidas,
    bajo el supuesto de que podrían aplicarse a la cancelación de la
    deuda. Indicador publicado por las agencias calificadoras.

    Puede resultar negativo cuando el efectivo supera a la deuda
    financiera. Ese valor es informativo y se conserva: indica posición
    de caja neta.
    """
    deuda_neta = df['deuda_financiera_total'] - df['efectivo_equivalentes']
    return division_segura(deuda_neta, df['ebitda'], permitir_negativos=False)


def apalancamiento_financiero(df):
    """
    Multiplicador del capital: Activo total / Patrimonio.

    Tercer factor de la descomposición DuPont. Indica cuántas unidades
    de activo sostiene cada unidad de patrimonio.
    """
    return division_segura(df['activo_total'], df['patrimonio_total'],
                           permitir_negativos=False)


def calidad_deuda(df):
    """
    Pasivo corriente / Pasivo total.

    Mide la proporción de las obligaciones exigibles en el corto plazo.
    A mayor valor, mayor presión sobre la liquidez.
    """
    return division_segura(df['pasivo_corriente_total'], df['pasivo_total'])