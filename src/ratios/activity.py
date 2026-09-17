#FinAnalyzer Pro activity.py
#ES: Que tan bien la empresa usa su recursos para generar ventas
#EN: How well does the company use its resources to generate sales?

import pandas as pd
from src.utils import division_segura

def rotacion_inventarios(df):                                         #How many times did you sell all your inventory?

   return division_segura(df['costo_ventas'], df['inventarios'])

def dias_inventario(df):
    
    return 365 * division_segura(df['inventarios'], df['costo_ventas'])          # How many days does it take to sell everything?

def rotacion_cuentas_x_cobrar(df):
    
    return division_segura(df['ventas_netas'], df['cuentas_por_cobrar'])           # How quickly does he collect what it is owed?

def rotacion_activos(df):
    
    return division_segura(df['ventas_netas'], df['activo_total'])         

DIAS_DEL_ANIO = 365


def dias_cuentas_por_cobrar(df):
    """
    Período promedio de cobro (DSO): 365 / Rotación de cuentas por cobrar.

    NOTA METODOLÓGICA: se calcula sobre el saldo de cierre y no sobre el
    saldo promedio del período. La alternativa exigiría el saldo inicial,
    que no está disponible para el primer ejercicio de la serie. Esta
    decisión es una causa conocida de discrepancia frente a los
    indicadores publicados por las agencias calificadoras.
    """
    return division_segura(df['cuentas_por_cobrar'] * DIAS_DEL_ANIO,
                           df['ventas_netas'])


def rotacion_cuentas_x_pagar(df):
    """Costo de ventas / Cuentas por pagar comerciales."""
    return division_segura(df['costo_ventas'], df['cuentas_por_pagar'])


def dias_cuentas_por_pagar(df):
    """
    Período promedio de pago (DPO): 365 / Rotación de cuentas por pagar.

    Se calcula sobre el saldo de cierre, conforme a la nota metodológica
    de dias_cuentas_por_cobrar.
    """
    return division_segura(df['cuentas_por_pagar'] * DIAS_DEL_ANIO,
                           df['costo_ventas'])


def ciclo_operativo(df):
    """
    Días de inventario más período promedio de cobro.

    Mide el tiempo transcurrido entre la adquisición del inventario y la
    cobranza efectiva de la venta.
    """
    return dias_inventario(df) + dias_cuentas_por_cobrar(df)


def ciclo_conversion_efectivo(df):
    """
    Ciclo operativo menos período promedio de pago.

    Mide los días que la empresa debe financiar con recursos propios o
    de terceros entre el desembolso a proveedores y la cobranza al
    cliente. Un valor negativo indica que la empresa se financia con el
    crédito de sus proveedores, situación característica de negocios de
    alta rotación y cobro al contado.
    """
    return ciclo_operativo(df) - dias_cuentas_por_pagar(df)         # How many pesos does it generate for every pesos of assets it owns?