"""
Costo promedio ponderado de capital.

Combina el costo del patrimonio, estimado por el modelo de valoración de
activos de capital, con el costo de la deuda, obtenido de los estados
financieros, ponderando ambos por su participación en la estructura de
financiamiento:

    WACC = [E/(D+E)] × Ke + [D/(D+E)] × Kd × (1 − t)

El resultado expresa el rendimiento mínimo que las inversiones de la
empresa deben generar para retribuir a quienes aportaron los recursos.

El endeudamiento incide sobre el resultado en dos direcciones opuestas.
Incrementa el coeficiente de riesgo sistemático reapalancado y con ello
el costo del patrimonio, en tanto el accionista percibe mayor riesgo.
Simultáneamente aumenta la ponderación de una fuente de menor costo y
fiscalmente deducible. El valor obtenido constituye el saldo de ambos
efectos.

Como en el módulo de costo del patrimonio, todos los parámetros admiten
valores sustitutos para el análisis de sensibilidad.
"""

import numpy as np
import pandas as pd

from src.analysis.capm import _serie, costo_patrimonio
from src.utils import division_segura
from src.utils import division_segura, formatear_pivote

IDENTIFICADORES = ['empresa', 'anio']


# ── Costo de la deuda ────────────────────────────────────────────

def costo_deuda(df):
    """
    Costo contable de la deuda: gastos financieros sobre deuda financiera
    total.

    NOTA METODOLÓGICA: el denominador es el saldo de cierre y no el saldo
    promedio del ejercicio. Cuando la deuda varía considerablemente
    durante el año, el cociente sobreestima o subestima el costo efectivo,
    porque relaciona un flujo de doce meses con un saldo puntual. La
    alternativa exigiría el saldo inicial, que no está disponible para el
    primer ejercicio de la serie. La decisión se declara como limitación.
    """
    resultado = division_segura(df['gastos_financieros'],
                                df['deuda_financiera_total'],
                                permitir_negativos=False)
    return pd.Series(resultado.to_numpy(), index=pd.RangeIndex(len(df)))


def costo_deuda_despues_impuestos(df, kd=None, tasa_impuesto=None):
    """
    Costo de la deuda neto del escudo fiscal: Kd × (1 − t).

    Los intereses son deducibles del impuesto sobre la renta, de modo que
    el costo efectivo de la deuda para la empresa resulta menor que la
    tasa pactada con el acreedor.
    """
    t = _serie(df, 'tasa_impuesto', tasa_impuesto)
    base = costo_deuda(df) if kd is None else pd.Series(
        float(kd), index=pd.RangeIndex(len(df)))
    return base * (1 - t)


# ── Estructura de financiamiento ─────────────────────────────────

def capital_total(df):
    """
    Deuda financiera más patrimonio.

    Define el capital sobre el que se pondera, y excluye el financiamiento
    espontáneo de proveedores, que no tiene costo explícito y por tanto no
    forma parte de la estructura de capital en este sentido.
    """
    total = df['deuda_financiera_total'] + df['patrimonio_total']
    return pd.Series(total.to_numpy(), index=pd.RangeIndex(len(df)))


def peso_patrimonio(df):
    """Participación del patrimonio en el capital total: E/(D+E)."""
    patrimonio = pd.Series(df['patrimonio_total'].to_numpy(),
                           index=pd.RangeIndex(len(df)))
    return division_segura(patrimonio, capital_total(df),
                           permitir_negativos=False)


def peso_deuda(df):
    """Participación de la deuda financiera en el capital total: D/(D+E)."""
    deuda = pd.Series(df['deuda_financiera_total'].to_numpy(),
                      index=pd.RangeIndex(len(df)))
    return division_segura(deuda, capital_total(df), permitir_negativos=False)


# ── Costo promedio ponderado ─────────────────────────────────────

def wacc(df, rf=None, erp=None, crp=None, beta_sectorial=None,
         tasa_impuesto=None, kd=None):
    """
    Costo promedio ponderado de capital.

    Los parámetros sustitutos se propagan al cálculo del costo del
    patrimonio, de modo que una modificación de la prima de riesgo país se
    refleja simultáneamente en el Ke y en el WACC resultante.
    """
    ke = costo_patrimonio(df, rf=rf, erp=erp, crp=crp,
                          beta_sectorial=beta_sectorial,
                          tasa_impuesto=tasa_impuesto)
    kd_neto = costo_deuda_despues_impuestos(df, kd=kd,
                                            tasa_impuesto=tasa_impuesto)
    return peso_patrimonio(df) * ke + peso_deuda(df) * kd_neto


# ── Tabla de resultados ──────────────────────────────────────────

def calcular(df, decimales=4, **sustitutos):
    """
    Devuelve los componentes del cálculo, de modo que cada uno pueda
    verificarse por separado.
    """
    resultado = pd.DataFrame({c: df[c].to_numpy() for c in IDENTIFICADORES},
                             index=pd.RangeIndex(len(df)))

    ke = costo_patrimonio(
        df, rf=sustitutos.get('rf'), erp=sustitutos.get('erp'),
        crp=sustitutos.get('crp'),
        beta_sectorial=sustitutos.get('beta_sectorial'),
        tasa_impuesto=sustitutos.get('tasa_impuesto'))
    kd_bruto = (costo_deuda(df) if sustitutos.get('kd') is None
                else pd.Series(float(sustitutos['kd']),
                               index=pd.RangeIndex(len(df))))
    kd_neto = costo_deuda_despues_impuestos(
        df, kd=sustitutos.get('kd'),
        tasa_impuesto=sustitutos.get('tasa_impuesto'))
    we = peso_patrimonio(df)
    wd = peso_deuda(df)

    resultado['Capital total'] = capital_total(df).round(0)
    resultado['Peso patrimonio'] = we.round(decimales)
    resultado['Peso deuda'] = wd.round(decimales)
    resultado['Ke'] = ke.round(decimales)
    resultado['Kd'] = kd_bruto.round(decimales)
    resultado['Kd después de impuestos'] = kd_neto.round(decimales)
    resultado['Aporte del patrimonio'] = (we * ke).round(decimales)
    resultado['Aporte de la deuda'] = (wd * kd_neto).round(decimales)
    resultado['WACC'] = (we * ke + wd * kd_neto).round(decimales)

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
    print('  COSTO PROMEDIO PONDERADO DE CAPITAL')
    print('=' * ancho)
    indicados = ', '.join(f'{k}={v}' for k, v in sustitutos.items()
                          if v is not None)
    if indicados:
        print(f'  Parámetros sustituidos: {indicados}')
        print('-' * ancho)
    print(formatear_pivote(pivote).to_string())
    print()
    print('WACC = [E/(D+E)] × Ke + [D/(D+E)] × Kd × (1 − t)')