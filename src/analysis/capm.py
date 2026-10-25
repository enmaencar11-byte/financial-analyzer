"""
Modelo de valoración de activos de capital, adaptado a mercados emergentes.

Estima el costo del patrimonio, que es el rendimiento que los propietarios
exigirían por mantener su inversión en la empresa en lugar de destinarla a
una alternativa de riesgo equivalente. A diferencia del costo de la deuda,
este costo no aparece registrado en los estados financieros, pero existe
como costo de oportunidad y determina si la empresa crea o destruye valor.

La formulación de Sharpe y Lintner supone mercados con liquidez suficiente
para que los precios reflejen la información disponible. Esa condición no
se satisface en el mercado dominicano, por lo que el modelo incorpora dos
adaptaciones documentadas por Damodaran: la adición de una prima de riesgo
país y la estimación del coeficiente de riesgo sistemático a partir de
valores sectoriales de empresas comparables, reapalancados conforme a la
estructura de capital de cada emisor mediante la expresión de Hamada.

PARÁMETROS SUSTITUIBLES
Todas las funciones admiten valores que reemplazan a los del archivo de
parámetros. Cuando el argumento se omite, se emplea el valor registrado;
cuando se indica, ese valor rige para todas las observaciones.

Esta capacidad permite el análisis de sensibilidad: los parámetros del
modelo son estimaciones, no magnitudes observadas, y examinar cómo varía
el resultado dentro de un rango plausible forma parte de la interpretación
responsable de un costo de capital estimado por vía indirecta.

Un único camino de cálculo sirve tanto al proceso por lotes como al panel
interactivo, de modo que la cifra que el panel muestra es necesariamente
la misma que el reporte produce.
"""

import numpy as np
import pandas as pd

from src.utils import division_segura
from src.utils import division_segura, formatear_pivote

IDENTIFICADORES = ['empresa', 'anio']

# Correspondencia entre el nombre del argumento y la columna del archivo.
PARAMETROS = {
    'rf': 'tasa_libre_riesgo',
    'erp': 'prima_riesgo_mercado',
    'crp': 'prima_riesgo_pais',
    'beta_sectorial': 'beta_desapalancado',
    'tasa_impuesto': 'tasa_impuesto_efectiva',
}


def _serie(df, nombre, sustituto):
    """
    Devuelve un parámetro como serie alineada con el conjunto de datos.

    Sin sustituto, toma la columna correspondiente del archivo. Con
    sustituto, construye una serie constante, de modo que el valor
    indicado rige para todas las observaciones.

    La comprobación de la columna se realiza solo cuando hace falta: si
    todos los parámetros se sustituyen, el cálculo no requiere el archivo.
    """
    columna = PARAMETROS[nombre]
    if sustituto is None:
        if columna not in df.columns:
            raise ValueError(
                f"Falta el parámetro '{columna}' en los datos.\n"
                f'Incorpórelo con src.parametros.incorporar(df), o indique '
                f"un valor con el argumento {nombre}=.")
        return pd.Series(df[columna].to_numpy(), index=pd.RangeIndex(len(df)))
    return pd.Series(float(sustituto), index=pd.RangeIndex(len(df)))


# ── Componentes ──────────────────────────────────────────────────

def razon_deuda_patrimonio(df):
    """
    Razón D/E sobre deuda financiera, no sobre el pasivo total.

    La expresión de Hamada mide el efecto del apalancamiento financiero
    sobre el riesgo del patrimonio, por lo que considera únicamente las
    obligaciones que devengan interés. El financiamiento espontáneo de
    proveedores no forma parte de la estructura de capital en este sentido.
    """
    resultado = division_segura(df['deuda_financiera_total'],
                                df['patrimonio_total'],
                                permitir_negativos=False)
    return pd.Series(resultado.to_numpy(), index=pd.RangeIndex(len(df)))


def beta_reapalancado(df, beta_sectorial=None, tasa_impuesto=None):
    """
    Coeficiente de riesgo sistemático ajustado a la estructura de capital
    del emisor, conforme a la expresión de Hamada:

        Bl = Bu × [1 + (1 − t) × D/E]

    El término (1 − t) incorpora el escudo fiscal: como los intereses son
    deducibles, el endeudamiento incrementa el riesgo del patrimonio en
    una proporción menor a la que correspondería en ausencia de
    tributación.

    Un beta sectorial sustituto se aplica por igual a todos los emisores,
    lo que resulta apropiado para examinar la sensibilidad del resultado
    pero no para un cálculo definitivo cuando la muestra abarca sectores
    distintos.
    """
    bu = _serie(df, 'beta_sectorial', beta_sectorial)
    t = _serie(df, 'tasa_impuesto', tasa_impuesto)
    return bu * (1 + (1 - t) * razon_deuda_patrimonio(df))


def costo_patrimonio(df, rf=None, erp=None, crp=None,
                     beta_sectorial=None, tasa_impuesto=None):
    """
    Costo del patrimonio conforme al modelo ajustado por riesgo país:

        Ke = Rf + Bl × ERP + CRP

    La prima de riesgo país se añade como término independiente, bajo el
    supuesto de que todos los emisores del mercado se encuentran expuestos
    a ella en igual medida. Damodaran documenta formulaciones alternativas
    que ponderan esa exposición por emisor; la adoptada aquí es la más
    difundida y la que no exige supuestos adicionales sobre el grado de
    exposición individual.
    """
    return (_serie(df, 'rf', rf)
            + beta_reapalancado(df, beta_sectorial, tasa_impuesto)
              * _serie(df, 'erp', erp)
            + _serie(df, 'crp', crp))


# ── Tabla de resultados ──────────────────────────────────────────

def calcular(df, decimales=4, **sustitutos):
    """
    Devuelve los insumos y los resultados intermedios del cálculo, de modo
    que cada componente del costo del patrimonio pueda verificarse por
    separado.

    Los parámetros sustituidos aparecen en la tabla con el valor empleado,
    no con el del archivo, para que el resultado mostrado se corresponda
    siempre con los insumos que lo produjeron.
    """
    resultado = pd.DataFrame({c: df[c].to_numpy() for c in IDENTIFICADORES},
                             index=pd.RangeIndex(len(df)))

    rf = _serie(df, 'rf', sustitutos.get('rf'))
    erp = _serie(df, 'erp', sustitutos.get('erp'))
    crp = _serie(df, 'crp', sustitutos.get('crp'))
    bu = _serie(df, 'beta_sectorial', sustitutos.get('beta_sectorial'))
    t = _serie(df, 'tasa_impuesto', sustitutos.get('tasa_impuesto'))

    de = razon_deuda_patrimonio(df)
    bl = beta_reapalancado(df, sustitutos.get('beta_sectorial'),
                           sustitutos.get('tasa_impuesto'))
    ke = costo_patrimonio(df, **sustitutos)

    resultado['Rf'] = rf.round(decimales)
    resultado['ERP'] = erp.round(decimales)
    resultado['CRP'] = crp.round(decimales)
    resultado['Beta desapalancado'] = bu.round(decimales)
    resultado['Tasa impuesto'] = t.round(decimales)
    resultado['D/E financiera'] = de.round(decimales)
    resultado['Beta reapalancado'] = bl.round(decimales)
    resultado['Prima por riesgo sistemático'] = (bl * erp).round(decimales)
    resultado['Ke'] = ke.round(decimales)

    return resultado


def mostrar(df, ancho=78, **sustitutos):
    """Imprime el cálculo con los componentes en filas."""
    tabla = calcular(df, **sustitutos)
    columnas = [c for c in tabla.columns if c not in IDENTIFICADORES]

    largo = tabla.melt(id_vars=IDENTIFICADORES, value_vars=columnas,
                       var_name='componente', value_name='valor')
    pivote = largo.pivot_table(index='componente', columns=IDENTIFICADORES,
                               values='valor', sort=False)

    print()
    print('=' * ancho)
    print('  COSTO DEL PATRIMONIO — CAPM CON PRIMA DE RIESGO PAÍS')
    print('=' * ancho)
    if sustitutos:
        indicados = ', '.join(f'{k}={v}' for k, v in sustitutos.items()
                              if v is not None)
        if indicados:
            print(f'  Parámetros sustituidos: {indicados}')
            print('-' * ancho)
    print(formatear_pivote(pivote).to_string())
    print()
    print('Ke = Rf + Beta reapalancado × ERP + CRP')
    print('Beta reapalancado = Beta desapalancado × [1 + (1 − t) × D/E]')


def sensibilidad(df, parametro, valores, agregacion='mean'):
    """
    Recalcula el costo del patrimonio para varios valores de un parámetro.

    Devuelve una tabla con el valor ensayado y el Ke resultante, agregado
    sobre el conjunto de observaciones. Es el insumo del análisis de
    sensibilidad y de los controles del panel interactivo.
    """
    if parametro not in PARAMETROS:
        raise ValueError(f'Parámetro desconocido: {parametro}. '
                         f'Opciones: {", ".join(PARAMETROS)}')

    filas = []
    for valor in valores:
        ke = costo_patrimonio(df, **{parametro: valor})
        filas.append({parametro: valor,
                      'Ke': getattr(ke, agregacion)(),
                      'Ke mínimo': ke.min(),
                      'Ke máximo': ke.max()})
    return pd.DataFrame(filas)