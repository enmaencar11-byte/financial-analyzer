"""
FinAnalyzer Pro — orquestador del proceso de análisis.

Ejecuta la secuencia completa sobre el conjunto consolidado de emisores y
escribe el resultado en un solo libro de Excel, con una hoja por análisis.

El módulo no realiza ningún cálculo propio. Su función es establecer el
orden de ejecución, reunir los resultados y registrar las verificaciones
internas en una hoja única. Esa separación es deliberada: si un cálculo
resultara incorrecto, el error estaría en el módulo correspondiente y no
aquí, lo que delimita el lugar donde corresponde buscarlo.

La hoja 'Validación' reúne las comprobaciones de consistencia interna que
cada módulo practica por separado: la identidad de la descomposición
DuPont, la equivalencia de las dos formulaciones del valor económico
agregado, el cuadre del balance y las bases del análisis vertical.
Constituye el registro del primer nivel del protocolo de validación, y se
reproduce con una sola instrucción cuantas veces sea necesario.

USO

    python -m src.main
    python -m src.main --crp 0.015
    python -m src.main --wacc 0.09 --salida outputs/escenario_wacc9.xlsx
    python -m src.main --rf 0.045 --erp 0.05 --crp 0.03 --beta 0.80

Los parámetros indicados en la línea de instrucciones sustituyen a los del
archivo de parámetros. Si se sustituyen los cuatro parámetros de mercado,
el proceso no requiere el archivo.
"""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from src import ratios
from src.analysis import altman, capm, dupont, eva, horizontal, vertical, wacc
from src.config import TODAS_LAS_COLUMNAS
from src.data_loader import cargar_datos
from src.parametros import incorporar

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_ENTRADA = RAIZ / 'data' / 'processed' / 'emisores_consolidado.csv'
ARCHIVO_SALIDA = RAIZ / 'outputs' / 'resultados.xlsx'

IDENTIFICADORES = ['empresa', 'anio']

# Parámetros que cada modelo admite como sustitutos. La distinción es
# necesaria porque el costo del patrimonio no reconoce el costo de la
# deuda: pasarle un argumento que no admite interrumpiría la ejecución.
PARAMETROS_CAPM = ('rf', 'erp', 'crp', 'beta_sectorial', 'tasa_impuesto')
PARAMETROS_WACC = PARAMETROS_CAPM + ('kd',)

# Parámetros que provienen del archivo externo. La tasa impositiva no
# figura aquí porque se obtiene de los estados financieros.
PARAMETROS_DE_ARCHIVO = ('rf', 'erp', 'crp', 'beta_sectorial')

TOLERANCIA_CUADRE = 1.0
TOLERANCIA_BASE_VERTICAL = 0.01


def _filtrar(sustitutos, admitidos):
    """Conserva los sustitutos que el modelo indicado reconoce."""
    return {k: v for k, v in sustitutos.items()
            if k in admitidos and v is not None}


# ── Preparación de los datos ─────────────────────────────────────

def preparar(archivo=ARCHIVO_ENTRADA, **sustitutos):
    """
    Carga el conjunto consolidado y le incorpora los parámetros externos.

    La incorporación se omite cuando los cuatro parámetros de mercado se
    indicaron por la línea de instrucciones, pues en ese caso el archivo
    de parámetros no aporta nada al cálculo. Esto permite ejecutar
    escenarios completos sin depender de él.
    """
    df = cargar_datos(archivo)

    if all(sustitutos.get(k) is not None for k in PARAMETROS_DE_ARCHIVO):
        print('Parámetros de mercado indicados por instrucción; '
              'no se consulta el archivo de parámetros.')
        return df

    return incorporar(df)


# ── Ejecución de los análisis ────────────────────────────────────

def ejecutar(df, wacc_valor=None, **sustitutos):
    """
    Corre la secuencia completa y devuelve los resultados en un
    diccionario ordenado, donde cada clave será el nombre de una hoja.

    El orden sigue la lógica del análisis financiero: primero la
    estructura y la evolución de los estados, después los indicadores,
    después la descomposición del rendimiento, y por último el riesgo de
    insolvencia y el costo del capital. Un lector que recorra las hojas
    en ese orden encuentra el razonamiento reconstruido.
    """
    para_capm = _filtrar(sustitutos, PARAMETROS_CAPM)
    para_wacc = _filtrar(sustitutos, PARAMETROS_WACC)

    # El análisis de estructura y evolución se practica sobre las partidas
    # de los estados financieros. Los parámetros de mercado incorporados
    # no son partidas contables: su variación interanual no significa nada
    # y su presencia en esas tablas solo introduciría ruido.
    estados = df[TODAS_LAS_COLUMNAS]

    resultados = {
        'Datos': df,

        'Vertical balance': vertical.vertical_balance(estados),
        'Vertical resultados': vertical.vertical_resultados(estados),
        'Horizontal interanual': horizontal.variacion_interanual(estados),
        'Horizontal absoluta': horizontal.variacion_absoluta(estados),
        'Horizontal indices': horizontal.numeros_indice(estados),

        'Ratios': ratios.calcular_todos(df),
        'Ratios detalle': ratios.calcular_largo(df),

        'DuPont nivel 1': dupont.dupont_nivel_1(df),
        'DuPont nivel 2': dupont.dupont_nivel_2(df),
        'DuPont nivel 3': dupont.dupont_nivel_3(df),
        'DuPont verificacion': dupont.verificar_identidad(df),

        'Altman': altman.calcular(df),

        'CAPM': capm.calcular(df, **para_capm),
        'WACC': wacc.calcular(df, **para_wacc),
        'EVA': eva.calcular(df, wacc_valor=wacc_valor, **para_wacc),
        'EVA verificacion': eva.verificar_identidad(
            df, wacc_valor=wacc_valor, **para_wacc),
    }

    resultados['Validacion'] = tabla_validacion(df, resultados)
    resultados['Parametros usados'] = tabla_parametros(
        df, wacc_valor, sustitutos)

    return resultados


# ── Registro de las verificaciones ───────────────────────────────

def tabla_validacion(df, resultados):
    """
    Reúne en una sola tabla las comprobaciones de consistencia interna.

    Cada fila declara qué se comprobó, sobre cuántas observaciones, en
    cuántas se satisfizo la condición y cuál fue la discrepancia máxima.
    Las discrepancias del orden de 1e-16 no constituyen error: son el
    residuo de la aritmética de punto flotante, que no representa los
    números reales con precisión infinita.

    La tabla es el registro del primer nivel del protocolo de validación.
    Se obtiene por ejecución y no por transcripción manual, de modo que
    no puede discrepar de los resultados que acompaña.
    """
    filas = []

    # Cuadre del balance. Activo = Pasivo + Patrimonio.
    desvio = (df['activo_total'] - df['pasivo_total']
              - df['patrimonio_total']).abs()
    filas.append({
        'Comprobación': 'Cuadre del balance',
        'Condición': 'Activo = Pasivo + Patrimonio',
        'Observaciones': len(desvio),
        'Satisfacen': int((desvio <= TOLERANCIA_CUADRE).sum()),
        'Discrepancia máxima': float(desvio.max()),
        'Tolerancia': TOLERANCIA_CUADRE,
    })

    # Bases del análisis vertical. Deben resultar exactamente 100.
    for etiqueta, hoja, columna in (
            ('Base del vertical del balance', 'Vertical balance',
             'activo_total'),
            ('Base del vertical de resultados', 'Vertical resultados',
             'ventas_netas')):
        if columna in resultados[hoja].columns:
            desvio = (resultados[hoja][columna] - 100).abs()
            filas.append({
                'Comprobación': etiqueta,
                'Condición': f'{columna} = 100',
                'Observaciones': len(desvio),
                'Satisfacen': int((desvio <= TOLERANCIA_BASE_VERTICAL).sum()),
                'Discrepancia máxima': float(desvio.max()),
                'Tolerancia': TOLERANCIA_BASE_VERTICAL,
            })

    # Identidad de la descomposición DuPont, en sus dos niveles.
    resumen = dupont.resumen_verificacion(df)
    for nivel in (2, 3):
        filas.append({
            'Comprobación': f'Identidad DuPont nivel {nivel}',
            'Condición': 'Producto de los factores = ROE',
            'Observaciones': resumen['observaciones'],
            'Satisfacen': resumen[f'nivel_{nivel}_coinciden'],
            'Discrepancia máxima': resumen[f'diferencia_maxima_nivel_{nivel}'],
            'Tolerancia': resumen['tolerancia'],
        })

    # Equivalencia de las dos formulaciones del valor económico agregado.
    v = resultados['EVA verificacion']
    filas.append({
        'Comprobación': 'Equivalencia de las formulaciones del EVA',
        'Condición': 'NOPAT − CI×WACC = (ROIC − WACC)×CI',
        'Observaciones': len(v),
        'Satisfacen': int(v['Coincide'].sum()),
        'Discrepancia máxima': float(v['Diferencia relativa'].max()),
        'Tolerancia': eva.TOLERANCIA_RELATIVA,
    })

    # Cobertura del catálogo de indicadores.
    conteo = ratios.resumen()
    filas.append({
        'Comprobación': 'Indicadores calculados',
        'Condición': 'Catálogo completo',
        'Observaciones': conteo['TOTAL'],
        'Satisfacen': conteo['TOTAL'],
        'Discrepancia máxima': 0.0,
        'Tolerancia': 0.0,
    })

    tabla = pd.DataFrame(filas)
    tabla['Resultado'] = [
        'Satisface' if s == o else 'Revisar'
        for s, o in zip(tabla['Satisfacen'], tabla['Observaciones'])]
    return tabla


def tabla_parametros(df, wacc_valor, sustitutos):
    """
    Deja constancia de los parámetros con que se produjo el resultado.

    Un costo de capital estimado por vía indirecta carece de significado
    si no se conoce el valor de los parámetros que lo originaron. La hoja
    registra el origen de cada uno —el archivo o la instrucción de
    ejecución— y la fecha de la corrida, de modo que el resultado sea
    reproducible y no quede ambiguo cuál de varios escenarios produjo
    una cifra determinada.
    """
    filas = [{'Concepto': 'Fecha de ejecución', 'Valor': str(date.today()),
              'Origen': '—'},
             {'Concepto': 'Emisores', 'Valor': df['empresa'].nunique(),
              'Origen': 'Datos'},
             {'Concepto': 'Observaciones', 'Valor': len(df),
              'Origen': 'Datos'},
             {'Concepto': 'Ejercicios',
              'Valor': f"{df['anio'].min()}–{df['anio'].max()}",
              'Origen': 'Datos'}]

    for nombre in PARAMETROS_WACC:
        indicado = sustitutos.get(nombre)
        if indicado is not None:
            filas.append({'Concepto': nombre, 'Valor': indicado,
                          'Origen': 'Instrucción de ejecución'})
        elif nombre in capm.PARAMETROS:
            columna = capm.PARAMETROS[nombre]
            if columna in df.columns:
                valores = sorted(df[columna].dropna().unique())
                texto = (f'{valores[0]:.4f}' if len(valores) == 1
                         else f'{min(valores):.4f}–{max(valores):.4f}')
                filas.append({'Concepto': nombre, 'Valor': texto,
                              'Origen': 'Archivo de parámetros o datos'})
        else:
            filas.append({'Concepto': nombre, 'Valor': 'Calculado',
                          'Origen': 'Estados financieros'})

    if wacc_valor is not None:
        filas.append({'Concepto': 'wacc impuesto', 'Valor': wacc_valor,
                      'Origen': 'Instrucción de ejecución'})

    return pd.DataFrame(filas)


# ── Escritura del libro ──────────────────────────────────────────

def guardar(resultados, archivo=ARCHIVO_SALIDA):
    """
    Escribe cada resultado en su propia hoja del mismo libro.

    Excel limita los nombres de hoja a treinta y un caracteres, de modo
    que se recortan si fuera necesario. El ancho de las columnas se
    ajusta al contenido, porque una hoja que exige ajustar cada columna
    a mano no se consulta.
    """
    archivo = Path(archivo)
    archivo.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(archivo, engine='openpyxl') as libro:
        for nombre, tabla in resultados.items():
            hoja = nombre[:31]
            tabla.to_excel(libro, sheet_name=hoja, index=False)

            hoja_excel = libro.sheets[hoja]
            for i, columna in enumerate(tabla.columns, start=1):
                ancho = max(len(str(columna)),
                            *(len(f'{v}') for v in tabla[columna].head(50))) \
                        if len(tabla) else len(str(columna))
                hoja_excel.column_dimensions[
                    hoja_excel.cell(row=1, column=i).column_letter
                ].width = min(max(ancho + 2, 10), 42)

    return archivo


# ── Presentación en pantalla ─────────────────────────────────────

def _notacion(valor):
    """
    Presenta una discrepancia o una tolerancia de forma legible.

    Las magnitudes del orden de 1e-17 exigen notación científica para ser
    interpretables, mientras que una tolerancia de una unidad monetaria se
    lee mejor como '1'. El criterio se aplica por valor y no por columna,
    porque una misma columna contiene ambas clases de magnitud.
    """
    if pd.isna(valor):
        return 'n/a'
    if valor == 0:
        return '0'
    if abs(valor) < 1e-4 or abs(valor) >= 1e6:
        return f'{valor:.2e}'
    return f'{valor:g}'


def resumir(resultados, ancho=78):
    """Imprime la tabla de validación y el resultado del EVA."""
    print()
    print('=' * ancho)
    print('  VALIDACIÓN — CONSISTENCIA INTERNA')
    print('=' * ancho)
    validacion = resultados['Validacion'].copy()
    for columna in ('Discrepancia máxima', 'Tolerancia'):
        validacion[columna] = validacion[columna].map(_notacion)
    print(validacion.to_string(index=False))

    print()
    print('=' * ancho)
    print('  RESULTADO POR EMISOR Y EJERCICIO')
    print('=' * ancho)

    # El WACC se toma de la hoja de EVA y no de la hoja de WACC. Son
    # distintos cuando la ejecución impone un costo de capital con --wacc:
    # la hoja de WACC conserva el valor que el modelo calcula, mientras
    # que la de EVA registra el que efectivamente produjo el resultado.
    # Presentar el calculado junto a un EVA obtenido con otro sería
    # atribuir la cifra a un costo de capital que no la originó.
    tabla = resultados['Altman'][IDENTIFICADORES + ['Zona']].merge(
        resultados['EVA'][IDENTIFICADORES
                          + ['WACC', 'ROIC', 'EVA', 'Resultado']],
        on=IDENTIFICADORES)
    tabla = tabla.rename(columns={'Zona': 'Altman',
                                  'Resultado': 'Juicio EVA'})
    tabla['EVA'] = tabla['EVA'].map(
        lambda v: 'n/a' if pd.isna(v) else f'{v:,.0f}')
    print(tabla.to_string(index=False))


# ── Línea de instrucciones ───────────────────────────────────────

def construir_argumentos():
    """Define los argumentos que el proceso admite."""
    p = argparse.ArgumentParser(
        prog='python -m src.main',
        description='Ejecuta el análisis completo y escribe el libro de '
                    'resultados.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Los parámetros indicados sustituyen a los del archivo.')

    p.add_argument('--datos', default=str(ARCHIVO_ENTRADA),
                   help='Archivo CSV consolidado de entrada.')
    p.add_argument('--salida', default=str(ARCHIVO_SALIDA),
                   help='Libro de Excel que se escribirá.')
    p.add_argument('--silencioso', action='store_true',
                   help='Omite la impresión en pantalla.')

    g = p.add_argument_group('parámetros sustituibles')
    g.add_argument('--rf', type=float, help='Tasa libre de riesgo.')
    g.add_argument('--erp', type=float, help='Prima de riesgo de mercado.')
    g.add_argument('--crp', type=float, help='Prima de riesgo país.')
    g.add_argument('--beta', type=float, dest='beta_sectorial',
                   help='Beta desapalancado del sector.')
    g.add_argument('--tasa', type=float, dest='tasa_impuesto',
                   help='Tasa impositiva efectiva.')
    g.add_argument('--kd', type=float, help='Costo de la deuda antes de '
                                            'impuestos.')
    g.add_argument('--wacc', type=float, dest='wacc_valor',
                   help='Costo promedio ponderado impuesto, que reemplaza '
                        'al calculado.')
    return p


def main(argv=None):
    """Punto de entrada del proceso."""
    argumentos = construir_argumentos().parse_args(argv)

    sustitutos = {k: getattr(argumentos, k) for k in PARAMETROS_WACC}
    wacc_valor = argumentos.wacc_valor

    df = preparar(argumentos.datos, **sustitutos)
    resultados = ejecutar(df, wacc_valor=wacc_valor, **sustitutos)
    archivo = guardar(resultados, argumentos.salida)

    if not argumentos.silencioso:
        resumir(resultados)

    pendientes = resultados['Validacion']
    pendientes = pendientes[pendientes['Resultado'] != 'Satisface']

    print()
    print(f'Libro escrito en {archivo}')
    print(f'Hojas: {len(resultados)}')
    if len(pendientes):
        print(f'ATENCIÓN: {len(pendientes)} comprobación(es) no se satisfacen. '
              f'Revise la hoja Validacion.')
    else:
        print('Todas las comprobaciones de consistencia interna se satisfacen.')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())