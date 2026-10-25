"""
Panel interactivo de análisis.

Presenta los resultados del sistema con los parámetros del modelo de
costo de capital gobernados por controles deslizantes, de modo que el
efecto de cada supuesto sobre el resultado pueda examinarse en el acto.

POR QUÉ UN PANEL Y NO SOLO UN REPORTE

Los parámetros del modelo de valoración de activos de capital son
estimaciones y no magnitudes observadas: el coeficiente de riesgo
sistemático procede de otro mercado y la prima de riesgo país de un
diferencial soberano que varía a diario. Un trabajo que presente un
único costo de capital afirma más de lo que puede sostener.

El panel responde esa limitación en lugar de declararla. Permite
mostrar, y no solo decir, que la conclusión sobre creación de valor se
invierte por debajo de determinado umbral, y cuál es ese umbral para
cada emisor.

UN SOLO CAMINO DE CÁLCULO

El panel no calcula nada por su cuenta. Invoca las mismas funciones que
el proceso por lotes y las mismas funciones de figura que el reporte, de
modo que la cifra que muestra es necesariamente la que el reporte
produce. Un panel con su propio código de cálculo acabaría divergiendo
del reporte, y entonces ninguna de las dos cifras sería defendible.

USO

    streamlit run src/visualization/dashboard.py

Se abre en el navegador, en esta misma computadora. No queda publicado
en internet ni accesible desde otro equipo.
"""

import sys
from pathlib import Path

# El panel se ejecuta con 'streamlit run', que no añade la raíz del
# proyecto a la ruta de importación como hace 'python -m'. Sin esta
# línea, 'from src...' no resuelve.
RAIZ = Path(__file__).resolve().parent.parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.analysis import altman as mod_altman
from src.analysis import capm as mod_capm
from src.analysis import dupont as mod_dupont
from src.analysis import eva as mod_eva
from src.analysis import wacc as mod_wacc
from src import ratios as mod_ratios
from src.analysis import horizontal as mod_horizontal
from src.analysis import vertical as mod_vertical
from src.config import TODAS_LAS_COLUMNAS
from src.data_loader import cargar_datos
from src.utils import UMBRAL_MONTO
from src.parametros import incorporar
from src.visualization import charts

ARCHIVO_ENTRADA = RAIZ / 'data' / 'processed' / 'emisores_consolidado.csv'

IDENTIFICADORES = ['empresa', 'anio']

# Intervalos de los controles. Se fijan con holgura sobre los valores
# plausibles del mercado dominicano: un control que no alcance los
# extremos defendibles impediría justamente el análisis que justifica
# la existencia del panel.
CONTROLES = {
    'rf': ('Tasa libre de riesgo', 0.0, 0.10, 0.0005,
           'Rendimiento del bono del Tesoro de los Estados Unidos.'),
    'erp': ('Prima de riesgo de mercado', 0.02, 0.10, 0.0005,
            'Exceso histórico del mercado accionario sobre la tasa libre '
            'de riesgo.'),
    'crp': ('Prima de riesgo país', 0.0, 0.08, 0.0005,
            'Diferencial soberano de la República Dominicana. Es el '
            'parámetro al que el resultado resulta más sensible, por ser '
            'el único que entra como término aditivo independiente del '
            'coeficiente de riesgo sistemático.'),
    'beta_sectorial': ('Beta desapalancado del sector', 0.30, 2.00, 0.01,
                       'Coeficiente de riesgo sistemático del sector, antes '
                       'de ajustar por la estructura de capital del emisor. '
                       'Un valor sustituto se aplica por igual a todos los '
                       'emisores, lo que es apropiado para el análisis de '
                       'sensibilidad pero no para un cálculo definitivo '
                       'cuando la muestra abarca sectores distintos.'),
    'kd': ('Costo de la deuda antes de impuestos', 0.02, 0.25, 0.001,
           'Sustituye al costo contable que se obtiene de los estados '
           'financieros.'),
}


# ── Carga ────────────────────────────────────────────────────────

@st.cache_data(show_spinner='Cargando los estados financieros...')
def cargar(ruta):
    """
    Lee el conjunto consolidado y le incorpora los parámetros externos.

    El resultado queda en memoria entre ejecuciones del script, que
    Streamlit repite cada vez que el usuario mueve un control. Sin esa
    caché, cada movimiento de un deslizador releería los archivos.
    """
    return incorporar(cargar_datos(ruta))


def valores_de_archivo(df):
    """Promedio de cada parámetro registrado, como punto de partida."""
    base = {}
    for nombre, columna in mod_capm.PARAMETROS.items():
        if nombre in CONTROLES and columna in df.columns:
            base[nombre] = float(df[columna].mean())
    if 'kd' not in base:
        base['kd'] = float(mod_wacc.costo_deuda(df).mean())
    return base


# ── Selección de la muestra ──────────────────────────────────────

def seleccionar(df):
    """
    Restringe la muestra a los emisores y ejercicios elegidos.

    El orden canónico de los emisores se fija con la muestra COMPLETA y
    no con la seleccionada. De ese modo el color, el trazo y el marcador
    de cada emisor permanecen constantes al filtrar: quitar un emisor de
    la comparación no debe repintar a los que quedan, porque el lector
    sigue a la serie por su color y nada en los datos ha cambiado.

    Un emisor solo es una selección legítima: muchas de las figuras se
    leen mejor de uno en uno, y el análisis por emisor es el uso habitual
    cuando se redacta el apartado correspondiente a cada uno.

    La función no interrumpe la ejecución cuando la selección queda
    vacía. Devuelve el conjunto vacío y deja que quien la invoca decida:
    así los controles de parámetros alcanzan a dibujarse y el usuario
    conserva una barra lateral completa desde la que corregir. Detener el
    proceso aquí dejaba la página reducida al propio selector, lo que
    parecía una falla del programa en lugar de una selección vacía.
    """
    completos = list(dict.fromkeys(df['empresa']))
    charts.fijar_universo(completos)

    st.sidebar.title('Muestra')

    elegidos = st.sidebar.multiselect(
        'Emisores', options=completos, default=completos,
        help='Elija uno para el análisis individual, o varios para '
             'compararlos. El color de cada emisor no cambia al filtrar.')

    anios = sorted(df['anio'].unique())
    if len(anios) > 1:
        desde, hasta = st.sidebar.select_slider(
            'Ejercicios', options=anios, value=(anios[0], anios[-1]),
            help='Acota el período. El análisis horizontal y la '
                 'descomposición de la variación toman como base el '
                 'primer ejercicio del intervalo.')
    else:
        desde = hasta = anios[0]

    filtrado = df[df['empresa'].isin(elegidos)
                  & df['anio'].between(desde, hasta)].reset_index(drop=True)

    if filtrado.empty:
        st.sidebar.error('La selección no deja observaciones.')
    else:
        total = len(completos)
        if len(elegidos) < total or (desde, hasta) != (anios[0], anios[-1]):
            st.sidebar.info(f'{len(elegidos)} de {total} emisores · '
                            f'ejercicios {desde}–{hasta}')

    st.sidebar.divider()
    return filtrado


# ── Controles ────────────────────────────────────────────────────

def barra_lateral(df):
    """
    Construye los controles y devuelve los parámetros sustituidos.

    Cada parámetro se sustituye por separado. Mantener los demás en su
    valor registrado es lo que permite atribuir un cambio del resultado
    al parámetro que efectivamente se movió, y no a una combinación de
    varios.
    """
    base = valores_de_archivo(df)
    sustitutos, activos = {}, []

    st.sidebar.title('Parámetros del modelo')
    st.sidebar.caption(
        'Cada parámetro parte del valor registrado en el archivo. '
        'Actívelo para sustituirlo y observar el efecto sobre el '
        'resultado.')

    for nombre, (etiqueta, minimo, maximo, paso, ayuda) in CONTROLES.items():
        inicial = base.get(nombre, (minimo + maximo) / 2)
        activo = st.sidebar.checkbox(etiqueta, value=False, key=f'ok_{nombre}',
                                     help=ayuda)
        valor = st.sidebar.slider(
            etiqueta, min_value=float(minimo), max_value=float(maximo),
            value=float(min(max(inicial, minimo), maximo)), step=float(paso),
            key=f'v_{nombre}', disabled=not activo,
            label_visibility='collapsed',
            format='%.4f' if paso < 0.01 else '%.2f')
        if activo:
            sustitutos[nombre] = valor
            activos.append(f'{etiqueta}: {valor:.4f}')

    st.sidebar.divider()
    st.sidebar.subheader('Costo de capital impuesto')
    st.sidebar.caption(
        'Reemplaza al costo promedio ponderado que el modelo calcula. '
        'Sirve para contrastar el resultado frente a un costo de capital '
        'objetivo, sin recorrer la cadena completa del modelo.')
    imponer = st.sidebar.checkbox('Imponer un WACC', value=False)
    wacc_valor = st.sidebar.slider(
        'WACC impuesto', 0.04, 0.20, 0.10, 0.0025,
        disabled=not imponer, label_visibility='collapsed',
        format='%.4f') if True else None
    if not imponer:
        wacc_valor = None
    else:
        activos.append(f'WACC impuesto: {wacc_valor:.4f}')

    st.sidebar.divider()
    if activos:
        st.sidebar.warning('Parámetros sustituidos:\n\n'
                           + '\n\n'.join(f'- {a}' for a in activos))
    else:
        st.sidebar.success('Todos los parámetros provienen del archivo.')

    return sustitutos, wacc_valor


# ── Encabezado ───────────────────────────────────────────────────

def _resumen(df, wacc_valor, sustitutos):
    """Cifras agregadas bajo un juego de parámetros determinado."""
    tabla = mod_eva.calcular(df, wacc_valor=wacc_valor, **sustitutos)
    return {
        'eva_total': float(tabla['EVA'].sum(skipna=True)),
        'crean': int((tabla['EVA'] > 0).sum()),
        'observaciones': len(tabla),
        'wacc_medio': float(tabla['WACC'].mean(skipna=True)),
        'tabla': tabla,
    }


def encabezado(df, sustitutos, wacc_valor):
    """
    Indicadores principales, con la variación respecto del caso base.

    La variación es el dato que da sentido al panel: sin ella, el usuario
    ve un número pero no sabe cuánto lo movió el control que acaba de
    desplazar.
    """
    actual = _resumen(df, wacc_valor, sustitutos)
    hay_cambio = bool(sustitutos) or wacc_valor is not None
    base = _resumen(df, None, {}) if hay_cambio else actual

    c1, c2, c3, c4 = st.columns(4)

    c1.metric('Emisores', df['empresa'].nunique(),
              help='Emisores incluidos en la selección actual.')

    c2.metric(
        'WACC promedio', f"{actual['wacc_medio']:.2%}",
        delta=(f"{actual['wacc_medio'] - base['wacc_medio']:+.2%}"
               if hay_cambio else None),
        delta_color='inverse',
        help='Promedio simple del costo promedio ponderado de capital '
             'sobre todas las observaciones.')

    c3.metric(
        'EVA agregado', f"{actual['eva_total']:,.0f}",
        delta=(f"{actual['eva_total'] - base['eva_total']:+,.0f}"
               if hay_cambio else None),
        help='Suma del valor económico agregado de todos los emisores y '
             'ejercicios.')

    c4.metric(
        'Observaciones que crean valor',
        f"{actual['crean']} de {actual['observaciones']}",
        delta=(f"{actual['crean'] - base['crean']:+d}"
               if hay_cambio else None),
        help='Observaciones con valor económico agregado positivo.')

    return actual['tabla']


# ── Pestañas ─────────────────────────────────────────────────────

def _figura(constructor):
    """
    Dibuja una figura de charts.py y la muestra, cerrándola después.

    Matplotlib conserva una referencia a cada figura creada. Sin el
    cierre explícito, cada movimiento de un control acumularía una figura
    más en memoria.
    """
    figura = constructor()
    # Sin use_container_width: el parametro quedo obsoleto y su sucesor,
    # width='stretch', es ya el valor por defecto. Omitirlo produce el
    # mismo resultado en las versiones actuales y no rompe en las
    # anteriores, donde width no existe.
    st.pyplot(figura)
    plt.close(figura)


def _formato(tabla, porcentajes):
    """
    Formatea cada columna según su naturaleza.

    Las columnas indicadas se presentan como porcentaje. Las restantes se
    deciden por magnitud, del mismo modo que las tablas del reporte: por
    encima del umbral son montos y se presentan con separador de miles y
    sin decimales; por debajo son razones o coeficientes y conservan
    cuatro decimales.

    La distinción no es cosmética. Un coeficiente de riesgo sistemático
    de 0.78 presentado sin decimales aparece como 1, que es un valor
    distinto y además uno con significado propio en el modelo.
    """
    estilo = {}
    for columna in tabla.columns:
        if columna in IDENTIFICADORES:
            continue
        if columna in porcentajes:
            estilo[columna] = '{:.2%}'
        elif pd.api.types.is_numeric_dtype(tabla[columna]):
            mayor = tabla[columna].abs().max(skipna=True)
            estilo[columna] = ('{:,.0f}' if pd.notna(mayor)
                               and mayor >= UMBRAL_MONTO else '{:.4f}')
    return tabla.style.format(estilo, na_rep='n/a')


def pestana_indicadores(df):
    """
    El catálogo de razones financieras, por categoría.

    Las cuatro categorías se presentan por separado y no juntas. La
    categoría es la unidad con que el análisis financiero interpreta los
    indicadores: la liquidez responde si la empresa puede pagar lo que
    vence pronto y la rentabilidad si gana dinero, preguntas que se
    comentan en apartados distintos y que treinta y tres paneles en una
    sola vista no ayudarían a separar.
    """
    conteo = mod_ratios.resumen()

    st.subheader('Razones financieras')
    st.markdown(
        f'El sistema calcula **{conteo["TOTAL"]} indicadores** agrupados en '
        f'cuatro categorías. Ninguno responde por sí solo si la empresa va '
        f'bien: el margen neto no sabe si puede pagar la nómina del mes, y '
        f'la razón corriente no sabe si el negocio es rentable. Se leen en '
        f'conjunto.')

    columnas = st.columns(len(mod_ratios.CATEGORIAS))
    for columna, categoria in zip(columnas, mod_ratios.CATEGORIAS):
        columna.metric(categoria, conteo.get(categoria, 0))

    st.divider()

    categoria = st.radio(
        'Categoría', mod_ratios.CATEGORIAS, horizontal=True,
        help='Cada categoría responde una pregunta distinta sobre la '
             'misma empresa.')

    _figura(lambda: charts.indicadores(df, categoria, dir_salida=None))

    tabla = mod_ratios.calcular_todos(df, categoria=categoria)
    st.dataframe(_formato(tabla, []), hide_index=True)

    st.caption(
        'Un valor ausente indica que el indicador no aplica al emisor y '
        'ejercicio correspondientes, no que valga cero. Un ROE calculado '
        'sobre patrimonio negativo, por ejemplo, resultaría positivo por '
        'cancelación de signos y carecería de significado económico, de '
        'modo que se excluye.')


def pestana_estructura(df):
    """
    Análisis vertical y horizontal: la composición y su evolución.

    Son dos preguntas distintas sobre los mismos estados. El vertical
    expresa cada partida como porcentaje de un total del mismo ejercicio
    y describe la composición. El horizontal compara cada partida con la
    del ejercicio anterior o con la de un año base y describe el
    movimiento.

    Ninguno sirve solo. La composición sin evolución no distingue a un
    emisor que siempre tuvo esa estructura de uno que acaba de cambiarla;
    la evolución sin composición no distingue un crecimiento del
    trescientos por ciento en una partida insignificante de uno del
    cuatro por ciento en la que manda.
    """
    # El análisis se practica sobre las partidas de los estados: los
    # parámetros de mercado incorporados no son partidas contables.
    estados = df[TODAS_LAS_COLUMNAS]

    st.subheader('Composición y evolución')

    vertical_, horizontal_ = st.tabs(['Análisis vertical',
                                      'Análisis horizontal'])

    with vertical_:
        st.markdown(
            'Cada partida como porcentaje de un total del mismo ejercicio: '
            'el activo total en el balance, las ventas netas en el estado '
            'de resultados. La lectura de márgenes es inmediata, porque la '
            'fila de utilidad bruta **es** el margen bruto.')

        _figura(lambda: charts.vertical_activo(estados, dir_salida=None))
        _figura(lambda: charts.vertical_resultados(estados, dir_salida=None))

        cual = st.radio('Tabla', ['Balance general', 'Estado de resultados'],
                        horizontal=True, key='tabla_vertical')
        tabla = (mod_vertical.vertical_balance(estados)
                 if cual == 'Balance general'
                 else mod_vertical.vertical_resultados(estados))
        st.dataframe(_formato(tabla, []), hide_index=True)

    with horizontal_:
        st.markdown(
            'La variación de cada partida respecto del ejercicio anterior, '
            'y los números índice respecto de un año base igual a cien. '
            'Los índices permiten comparar en una misma escala partidas de '
            'magnitudes muy distintas.')

        _figura(lambda: charts.horizontal_indices(estados, dir_salida=None))

        cual = st.radio(
            'Tabla', ['Números índice', 'Variación interanual (%)',
                      'Variación absoluta'],
            horizontal=True, key='tabla_horizontal')
        if cual == 'Números índice':
            tabla = mod_horizontal.numeros_indice(estados)
        elif cual.startswith('Variación interanual'):
            tabla = mod_horizontal.variacion_interanual(estados)
        else:
            tabla = mod_horizontal.variacion_absoluta(estados)
        st.dataframe(_formato(tabla, []), hide_index=True)

        st.caption(
            'El primer ejercicio de cada emisor queda sin variación '
            'interanual porque no tiene período de comparación. La fila se '
            'conserva para que las tablas puedan alinearse entre sí.')


def pestana_valor(df, tabla_eva, sustitutos, wacc_valor):
    """Creación o destrucción de valor."""
    st.subheader('Creación y destrucción de valor')
    st.markdown(
        'El valor económico agregado contrasta el resultado operativo '
        'después de impuestos con el costo del capital empleado para '
        'generarlo. Una empresa puede presentar utilidad contable '
        'positiva y destruir valor económico, si el rendimiento del '
        'capital invertido no compensa el costo de los recursos.')

    _figura(lambda: charts.eva(df, dir_salida=None,
                               **({'wacc_valor': wacc_valor} if wacc_valor
                                  else {}), **sustitutos))
    _figura(lambda: charts.roic_wacc(df, dir_salida=None,
                                     **({'wacc_valor': wacc_valor}
                                        if wacc_valor else {}),
                                     **sustitutos))

    st.dataframe(_formato(tabla_eva, ['ROIC', 'WACC',
                                          'Diferencial ROIC − WACC']),
                 hide_index=True)


def pestana_sensibilidad(df):
    """Umbral de creación de valor."""
    st.subheader('Sensibilidad al costo de capital')
    st.markdown(
        'El umbral es la cifra que acota la conclusión. Por encima de ese '
        'costo de capital el emisor destruye valor; por debajo, lo crea. '
        'La distancia que lo separa del costo estimado indica cuán '
        'robusta es la conclusión frente al supuesto adoptado.')
    _figura(lambda: charts.sensibilidad_eva(df, dir_salida=None))

    st.caption(
        'La figura emplea los parámetros del archivo con independencia de '
        'los controles, pues su objeto es precisamente recorrer el '
        'intervalo completo de costos de capital posibles.')


def pestana_costo(df, sustitutos):
    """Costo del capital."""
    st.subheader('Costo del capital')
    st.markdown(
        'El costo promedio ponderado combina el costo del patrimonio, '
        'estimado por el modelo de valoración de activos de capital, con '
        'el costo de la deuda, obtenido de los estados financieros. El '
        'endeudamiento incide en dos direcciones opuestas: incrementa el '
        'riesgo que percibe el accionista y, a la vez, aumenta la '
        'participación de una fuente más barata y fiscalmente deducible.')

    _figura(lambda: charts.composicion_wacc(df, dir_salida=None, **sustitutos))

    izquierda, derecha = st.columns(2)
    with izquierda:
        st.markdown('**Costo del patrimonio**')
        st.dataframe(
            _formato(mod_capm.calcular(
                df, **{k: v for k, v in sustitutos.items() if k != 'kd'}),
                ['Rf', 'ERP', 'CRP', 'Tasa impuesto', 'Ke',
                 'Prima por riesgo sistemático']),
            hide_index=True)
    with derecha:
        st.markdown('**Costo promedio ponderado**')
        st.dataframe(
            _formato(mod_wacc.calcular(df, **sustitutos),
                         ['Peso patrimonio', 'Peso deuda', 'Ke', 'Kd',
                          'Kd después de impuestos', 'WACC',
                          'Aporte del patrimonio', 'Aporte de la deuda']),
            hide_index=True)


def pestana_riesgo(df):
    """Riesgo de insolvencia."""
    st.subheader('Riesgo de insolvencia')
    st.markdown(
        "El puntaje Z'' de cuatro variables corresponde a empresas sin "
        'cotización bursátil, que es la condición de los emisores '
        'dominicanos del mercado de valores: colocan deuda y no acciones, '
        'de modo que no existe precio de mercado de su patrimonio.')

    _figura(lambda: charts.altman(df, dir_salida=None))

    tabla = mod_altman.calcular(df)
    st.dataframe(tabla, hide_index=True)

    conteo = mod_altman.resumen_zonas(df)
    c1, c2, c3 = st.columns(3)
    c1.metric('Zona segura', conteo.get('Segura', 0))
    c2.metric('Zona gris', conteo.get('Gris', 0))
    c3.metric('Zona de peligro', conteo.get('Peligro', 0))


def pestana_rendimiento(df):
    """Descomposición del rendimiento."""
    st.subheader('Descomposición del rendimiento')
    st.markdown(
        'El rendimiento sobre el patrimonio es el producto de sus '
        'factores, no su suma. La descomposición permite atribuir una '
        'variación a su causa: el desempeño de la operación, el costo del '
        'financiamiento o la carga tributaria, cada una de las cuales '
        'exige una respuesta distinta.')

    nivel = st.radio('Nivel de descomposición', [2, 3], index=1,
                     horizontal=True,
                     help='El nivel 2 descompone en tres factores; el '
                          'nivel 3 desagrega el margen neto en carga '
                          'fiscal, carga financiera y margen operativo.')
    _figura(lambda: charts.dupont_factores(df, dir_salida=None, nivel=nivel))

    emisor = st.selectbox('Emisor para la descomposición de la variación',
                          charts._emisores(df))
    try:
        _figura(lambda: charts.dupont_contribucion(df, emisor,
                                                   dir_salida=None,
                                                   nivel=nivel))
    except ValueError as error:
        st.info(str(error))

    st.dataframe(mod_dupont.dupont_nivel_3(df) if nivel == 3
                 else mod_dupont.dupont_nivel_2(df),
                 hide_index=True)


def pestana_validacion(df, sustitutos, wacc_valor):
    """Consistencia interna."""
    st.subheader('Consistencia interna')
    st.markdown(
        'Las identidades algebraicas del sistema se comprueban en cada '
        'ejecución. Son verificaciones de consistencia interna: contrastan '
        'el sistema contra sí mismo y no contra una fuente externa, de '
        'modo que detectan incoherencia de cálculo y no error de origen '
        'en los datos.')

    resumen = mod_dupont.resumen_verificacion(df)
    identidad_eva = mod_eva.verificar_identidad(
        df, wacc_valor=wacc_valor, **sustitutos)

    filas = [
        {'Comprobación': 'Identidad DuPont nivel 2',
         'Observaciones': resumen['observaciones'],
         'Satisfacen': resumen['nivel_2_coinciden'],
         'Discrepancia máxima': resumen['diferencia_maxima_nivel_2']},
        {'Comprobación': 'Identidad DuPont nivel 3',
         'Observaciones': resumen['observaciones'],
         'Satisfacen': resumen['nivel_3_coinciden'],
         'Discrepancia máxima': resumen['diferencia_maxima_nivel_3']},
        {'Comprobación': 'Equivalencia de las formulaciones del EVA',
         'Observaciones': len(identidad_eva),
         'Satisfacen': int(identidad_eva['Coincide'].sum()),
         'Discrepancia máxima': float(
             identidad_eva['Diferencia relativa'].max())},
    ]
    tabla = pd.DataFrame(filas)
    tabla['Resultado'] = [
        'Satisface' if s == o else 'Revisar'
        for s, o in zip(tabla['Satisfacen'], tabla['Observaciones'])]

    st.dataframe(tabla.style.format({'Discrepancia máxima': '{:.2e}'}),
                 hide_index=True)

    if (tabla['Resultado'] == 'Satisface').all():
        st.success('Todas las comprobaciones de consistencia interna se '
                   'satisfacen.')
    else:
        st.error('Alguna comprobación no se satisface. Revise los datos de '
                 'entrada.')

    st.caption(
        'Las discrepancias del orden de 1e-17 no constituyen error: son el '
        'residuo de la aritmética de punto flotante, que no representa los '
        'números reales con precisión infinita.')


# ── Composición de la página ─────────────────────────────────────

def main():
    """Arma la página."""
    st.set_page_config(page_title='FinAnalyzer Pro',
                       page_icon='📊', layout='wide')

    st.title('FinAnalyzer Pro')
    st.caption('Análisis de estados financieros de emisores no financieros '
               'dominicanos, 2022–2025')

    if not ARCHIVO_ENTRADA.exists():
        st.error(f'No se encontró {ARCHIVO_ENTRADA}.\n\n'
                 f'Ejecute antes `python -m src.etl` para consolidar las '
                 f'plantillas.')
        st.stop()

    try:
        df = cargar(str(ARCHIVO_ENTRADA))
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    seleccion = seleccionar(df)

    # Los controles de parámetros se dibujan siempre, aun con la
    # selección vacía: una barra lateral incompleta se lee como una
    # falla. Cuando no hay observaciones se toman del conjunto completo,
    # que solo determina el valor inicial de cada control.
    sustitutos, wacc_valor = barra_lateral(
        seleccion if not seleccion.empty else df)

    if seleccion.empty:
        st.info('No hay ningún emisor seleccionado.\n\n'
                'Elija al menos uno en la barra lateral para ver el '
                'análisis. Los parámetros del modelo quedan como estaban.')
        st.stop()

    df = seleccion
    tabla_eva = encabezado(df, sustitutos, wacc_valor)
    st.divider()

    (estructura, indicadores, valor, sensibilidad, costo, riesgo,
     rendimiento, validacion) = st.tabs(
        ['Estructura', 'Indicadores', 'Valor', 'Sensibilidad',
         'Costo de capital', 'Riesgo', 'Rendimiento', 'Validación'])

    with estructura:
        pestana_estructura(df)
    with indicadores:
        pestana_indicadores(df)
    with valor:
        pestana_valor(df, tabla_eva, sustitutos, wacc_valor)
    with sensibilidad:
        pestana_sensibilidad(df)
    with costo:
        pestana_costo(df, sustitutos)
    with riesgo:
        pestana_riesgo(df)
    with rendimiento:
        pestana_rendimiento(df)
    with validacion:
        pestana_validacion(df, sustitutos, wacc_valor)


# Streamlit ejecuta el archivo indicado en la instrucción con __name__
# igual a '__main__', de modo que esta guarda permite abrir el panel de
# dos maneras: directamente sobre este archivo, o desde app.py, que
# importa main y lo invoca. Sin la guarda, la importación desde app.py
# armaría la página una segunda vez.
if __name__ == '__main__':
    main()