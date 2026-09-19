"""
Catálogo de indicadores financieros de FinAnalyzer Pro.

Registra las 33 razones en un único lugar, con su categoría y su nombre
para presentación. El registro es explícito y no se construye inspeccionando
los módulos, porque esa técnica incluiría por error cualquier función
importada desde otro módulo y produciría un conteo incorrecto.
"""

import pandas as pd

from src.ratios import activity, leverage, liquidity, profitability

IDENTIFICADORES = ['empresa', 'anio']

# (categoría, módulo, función, nombre para presentación, decimales)
CATALOGO = [
    ('Liquidez', liquidity, 'razon_corriente', 'Razón corriente', 2),
    ('Liquidez', liquidity, 'prueba_acida', 'Prueba ácida', 2),
    ('Liquidez', liquidity, 'razon_efectivo', 'Razón de efectivo', 2),
    ('Liquidez', liquidity, 'capital_trabajo', 'Capital de trabajo neto', 0),
    ('Liquidez', liquidity, 'capital_trabajo_sobre_activos', 'Capital de trabajo / Activos', 3),
    ('Liquidez', liquidity, 'razon_deuda_corto_plazo', 'Deuda CP / Deuda total', 3),

    ('Rentabilidad', profitability, 'margen_bruto', 'Margen bruto', 3),
    ('Rentabilidad', profitability, 'margen_operativo', 'Margen operativo', 3),
    ('Rentabilidad', profitability, 'margen_ebitda', 'Margen EBITDA', 3),
    ('Rentabilidad', profitability, 'margen_neto', 'Margen neto', 3),
    ('Rentabilidad', profitability, 'margen_nopat', 'Margen NOPAT', 3),
    ('Rentabilidad', profitability, 'retorno_sobre_activos', 'ROA', 3),
    ('Rentabilidad', profitability, 'retorno_sobre_patrimonio', 'ROE', 3),
    ('Rentabilidad', profitability, 'roic', 'ROIC', 3),
    ('Rentabilidad', profitability, 'retorno_sobre_capital_empleado', 'ROCE', 3),

    ('Apalancamiento', leverage, 'endeudamiento_total', 'Endeudamiento total', 3),
    ('Apalancamiento', leverage, 'endeudamiento_financiero', 'Endeudamiento financiero', 3),
    ('Apalancamiento', leverage, 'deuda_sobre_patrimonio', 'Deuda / Patrimonio', 2),
    ('Apalancamiento', leverage, 'apalancamiento_financiero', 'Apalancamiento financiero', 2),
    ('Apalancamiento', leverage, 'cobertura_interes', 'Cobertura de intereses (EBIT)', 2),
    ('Apalancamiento', leverage, 'cobertura_interes_ebitda', 'Cobertura de intereses (EBITDA)', 2),
    ('Apalancamiento', leverage, 'deuda_financiera_ebitda', 'Deuda financiera / EBITDA', 2),
    ('Apalancamiento', leverage, 'deuda_neta_ebitda', 'Deuda neta / EBITDA', 2),
    ('Apalancamiento', leverage, 'calidad_deuda', 'Calidad de la deuda', 3),

    ('Actividad', activity, 'rotacion_activos', 'Rotación de activos', 2),
    ('Actividad', activity, 'rotacion_inventarios', 'Rotación de inventarios', 2),
    ('Actividad', activity, 'dias_inventario', 'Días de inventario', 1),
    ('Actividad', activity, 'rotacion_cuentas_x_cobrar', 'Rotación de cuentas por cobrar', 2),
    ('Actividad', activity, 'dias_cuentas_por_cobrar', 'Días de cobro (DSO)', 1),
    ('Actividad', activity, 'rotacion_cuentas_x_pagar', 'Rotación de cuentas por pagar', 2),
    ('Actividad', activity, 'dias_cuentas_por_pagar', 'Días de pago (DPO)', 1),
    ('Actividad', activity, 'ciclo_operativo', 'Ciclo operativo', 1),
    ('Actividad', activity, 'ciclo_conversion_efectivo', 'Ciclo de conversión de efectivo', 1),
]

CATEGORIAS = ['Liquidez', 'Rentabilidad', 'Apalancamiento', 'Actividad']


def calcular_todos(df, categoria=None):
    """
    Calcula los indicadores y devuelve una tabla ancha:
    una fila por emisor y ejercicio, una columna por indicador.

    Las columnas se construyen en un diccionario y se arman de una sola vez.
    Asignarlas al DataFrame una por una produciría la advertencia
    ChainedAssignmentError de pandas.
    """
    seleccion = [e for e in CATALOGO if categoria is None or e[0] == categoria]
    if not seleccion:
        raise ValueError(f"Categoría desconocida: {categoria}. "
                         f"Opciones: {', '.join(CATEGORIAS)}")

    columnas = {}
    for _, modulo, funcion, etiqueta, decimales in seleccion:
        columnas[etiqueta] = getattr(modulo, funcion)(df).round(decimales)

    return pd.concat([df[IDENTIFICADORES].reset_index(drop=True),
                      pd.DataFrame(columnas)], axis=1)


def calcular_largo(df):
    """
    Devuelve los indicadores en formato largo: una fila por cada
    combinación de emisor, ejercicio e indicador.

    Es la forma adecuada para construir tablas de reporte y para el
    cotejo contra los indicadores publicados por las calificadoras.
    """
    filas = []
    for categoria, modulo, funcion, etiqueta, decimales in CATALOGO:
        valores = getattr(modulo, funcion)(df).round(decimales)
        parcial = df[IDENTIFICADORES].reset_index(drop=True).copy()
        parcial['categoria'] = categoria
        parcial['indicador'] = etiqueta
        parcial['funcion'] = funcion
        parcial['valor'] = valores.reset_index(drop=True)
        filas.append(parcial)
    return pd.concat(filas, ignore_index=True)


def mostrar(df, categoria=None, ancho=78):
    """Imprime los indicadores en bloques legibles, por categoría."""
    categorias = [categoria] if categoria else CATEGORIAS
    largo = calcular_largo(df)

    for cat in categorias:
        sub = largo[largo['categoria'] == cat]
        tabla = sub.pivot_table(index='indicador', columns=['empresa', 'anio'],
                                values='valor', sort=False)
        print()
        print('=' * ancho)
        print(f'  {cat.upper()}')
        print('=' * ancho)
        print(tabla.to_string())


def resumen():
    """Cuenta los indicadores registrados, por categoría."""
    conteo = {cat: sum(1 for e in CATALOGO if e[0] == cat) for cat in CATEGORIAS}
    conteo['TOTAL'] = len(CATALOGO)
    return conteo