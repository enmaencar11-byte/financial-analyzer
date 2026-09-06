"""
Análisis vertical (estados de tamaño común).
Expresa cada partida como porcentaje de una base del mismo ejercicio,
lo que permite comparar emisores de distinto tamaño entre sí.
"""

import pandas as pd

from src.utils import division_segura

IDENTIFICADORES = ['empresa', 'anio']

BASE_BALANCE = 'activo_total'
BASE_RESULTADOS = 'ventas_netas'

PARTIDAS_BALANCE = [
    'efectivo_equivalentes', 'cuentas_por_cobrar', 'inventarios',
    'otros_activos_corrientes', 'activo_corriente_total',
    'propiedad_planta_equipo_neto', 'activos_intangibles',
    'otros_activos_no_corrientes', 'activo_no_corriente_total',
    'activo_total',
    'cuentas_por_pagar', 'deuda_financiera_corto_plazo',
    'otros_pasivos_corrientes', 'pasivo_corriente_total',
    'deuda_financiera_largo_plazo', 'otros_pasivos_no_corrientes',
    'pasivo_no_corriente_total', 'pasivo_total',
    'capital_social', 'utilidades_retenidas', 'otras_reservas',
    'patrimonio_total', 'deuda_financiera_total', 'capital_trabajo_neto',
]

PARTIDAS_RESULTADOS = [
    'ventas_netas', 'costo_ventas', 'utilidad_bruta',
    'gastos_ventas', 'gastos_administracion', 'depreciacion_amortizacion',
    'otros_gastos_operativos', 'total_gastos_operativos',
    'utilidad_operativa', 'ingresos_financieros', 'gastos_financieros',
    'otros_ingresos_netos', 'utilidad_antes_impuestos', 'impuesto_renta',
    'utilidad_neta', 'ebitda', 'nopat',
]


def _vertical(df, base, partidas):
    """Divide cada partida entre la base del mismo ejercicio."""
    if base not in df.columns:
        raise ValueError(f"Falta la columna base '{base}' en los datos.")

    resultado = df[IDENTIFICADORES].copy()
    for partida in partidas:
        if partida in df.columns:
            resultado[partida] = division_segura(df[partida], df[base]) * 100
    return resultado.round(2)


def vertical_balance(df):
    """
    Análisis vertical del balance, con el activo total como base.

    Cada partida se expresa como porcentaje del activo total del mismo
    ejercicio. Por construcción, 'activo_total' resulta siempre 100.
    """
    return _vertical(df, BASE_BALANCE, PARTIDAS_BALANCE)


def vertical_resultados(df):
    """
    Análisis vertical del estado de resultados, con las ventas como base.

    Cada partida se expresa como porcentaje de las ventas netas del mismo
    ejercicio. La lectura directa de márgenes es inmediata: la fila de
    'utilidad_bruta' es el margen bruto y la de 'utilidad_neta' el margen
    neto, sin cálculo adicional.
    """
    return _vertical(df, BASE_RESULTADOS, PARTIDAS_RESULTADOS)