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

from src.idioma import t
from src import idioma
import contextlib
import io
import shutil

from src import etl as mod_etl
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

IDENTIFICADORES = ['empresa', 'anio', 'issuer', 'year']

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
def cargar(ruta, marca_de_tiempo):
    """
    Lee el conjunto consolidado y le incorpora los parámetros externos.

    El resultado queda en memoria entre ejecuciones del script, que
    Streamlit repite cada vez que el usuario mueve un control. Sin esa
    caché, cada movimiento de un deslizador releería los archivos.

    El argumento marca_de_tiempo no se emplea dentro de la función:
    forma parte de la clave de la caché. Sin él, la caché responde a la
    ruta y no al contenido, de modo que volver a consolidar las
    plantillas con el panel abierto dejaba en pantalla los datos
    anteriores sin aviso alguno. Transcribir los emisores por partes es
    el uso habitual, y esa combinación —datos nuevos en disco, datos
    viejos en pantalla— no se advierte hasta que una cifra no concuerda
    con el documento.
    """
    return incorporar(cargar_datos(ruta))


def marca_de(archivo):
    """Momento de la última modificación de un archivo, o cero si falta."""
    try:
        return Path(archivo).stat().st_mtime
    except OSError:
        return 0.0


def valores_de_archivo(df):
    """Promedio de cada parámetro registrado, como punto de partida."""
    base = {}
    for nombre, columna in mod_capm.PARAMETROS.items():
        if nombre in CONTROLES and columna in df.columns:
            base[nombre] = float(df[columna].mean())
    if 'kd' not in base:
        base['kd'] = float(mod_wacc.costo_deuda(df).mean())
    return base


def periodo(df):
    """
    Describe el período que los datos cubren, como '2022–2025' o '2024'.

    El período se deduce de los datos y no se escribe a mano. Una leyenda
    fija afirmaría un intervalo que el archivo puede no contener: una
    plantilla a medio llenar produciría un panel que declara cuatro
    ejercicios y muestra uno, y la discrepancia pasaría inadvertida
    precisamente en la herramienta cuyo argumento es que sus cifras se
    comprueban.
    """
    anios = sorted(df['anio'].dropna().unique())
    if not anios:
        return ''
    if len(anios) == 1:
        return str(int(anios[0]))
    return f'{int(anios[0])}–{int(anios[-1])}'


# ── Carga de plantillas y parámetros ─────────────────────────────

DIR_PLANTILLAS = RAIZ / 'data' / 'raw'
ARCHIVO_MERCADO = RAIZ / 'data' / 'parametros_mercado.csv'
ARCHIVO_SECTOR = RAIZ / 'data' / 'parametros_sector.csv'


def _emisores_del_consolidado():
    """
    Emisores y ejercicios presentes en el consolidado, sin incorporar los
    parámetros externos.

    Se lee el archivo en crudo y no mediante la carga habitual porque
    esta función se emplea, entre otros casos, cuando la incorporación de
    parámetros ha fallado: necesita decir qué emisores carecen de ellos,
    y para eso no puede depender de que la incorporación funcione.
    """
    if not ARCHIVO_ENTRADA.exists():
        return pd.DataFrame(columns=['empresa', 'anio'])
    try:
        crudo = pd.read_csv(ARCHIVO_ENTRADA)
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame(columns=['empresa', 'anio'])
    return crudo[['empresa', 'anio']]


def _consolidar_y_reportar():
    """
    Ejecuta la consolidación y devuelve (exito, mensaje).

    El proceso de consolidación escribe su avance por la salida estándar,
    que en una terminal es el sitio adecuado y en una página web no se ve.
    Se captura para mostrarla donde el usuario está mirando.
    """
    salida = io.StringIO()
    try:
        with contextlib.redirect_stdout(salida):
            mod_etl.consolidar()
    except (ValueError, FileNotFoundError, KeyError) as error:
        return False, str(error)
    except Exception as error:                              # noqa: BLE001
        return False, f'{type(error).__name__}: {error}'
    return True, salida.getvalue().strip()


def _plantillas_presentes():
    """Archivos de plantilla que la carpeta de entrada contiene."""
    if not DIR_PLANTILLAS.exists():
        return []
    return sorted(p for p in DIR_PLANTILLAS.glob('*.xlsx')
                  if not p.name.startswith('~$'))


def _guardar_subidas(archivos):
    """
    Copia los archivos subidos a la carpeta de plantillas.

    Se conservan en disco y no solo en memoria porque el proceso por
    lotes, las figuras y el reporte leen de esa carpeta: una plantilla
    que existiera únicamente dentro del panel haría que la instrucción
    `python -m src.main` produjera un resultado distinto del que el panel
    muestra, y entonces ninguna de las dos cifras sería defendible.
    """
    DIR_PLANTILLAS.mkdir(parents=True, exist_ok=True)
    guardados = []
    for archivo in archivos:
        destino = DIR_PLANTILLAS / archivo.name
        with open(destino, 'wb') as salida:
            shutil.copyfileobj(archivo, salida)
        guardados.append(destino.name)
    return guardados


def pestana_datos():
    """
    Carga de plantillas y de los parámetros que el modelo requiere.

    Reúne en un solo lugar las tres cosas que el sistema necesita antes
    de calcular: las plantillas de los emisores, los parámetros de
    mercado por ejercicio y los sectoriales por emisor. Antes exigían
    manipular carpetas y archivos CSV a mano, que es donde se producen
    los errores difíciles de diagnosticar: un nombre de emisor con una
    coma sin comillas, un ejercicio transcrito a medias, un archivo que
    nunca pasó por Excel y cuyas fórmulas se leen vacías.
    """
    st.subheader(t('Datos'))

    # ── Plantillas ───────────────────────────────────────────────
    st.markdown(f"**{t('Plantillas de los emisores')}**")
    st.markdown(
        t('Arrastre aquí las plantillas de Excel, una por emisor. El '
          'sistema las guarda, las consolida y comprueba el cuadre del '
          'balance y la distribución del resultado antes de aceptarlas.'))

    subidas = st.file_uploader(
        t('Plantillas'), type=['xlsx'], accept_multiple_files=True,
        key='subidas', label_visibility='collapsed',
        help=t('El archivo debe haberse abierto y guardado en Excel al '
               'menos una vez después de llenarlo: las celdas con fórmula '
               'se leen vacías en caso contrario.'))

    if subidas:
        guardados = _guardar_subidas(subidas)
        exito, mensaje = _consolidar_y_reportar()
        if exito:
            st.success(t('{n} plantilla(s) incorporada(s).').format(
                n=len(guardados)))
            if mensaje:
                st.code(mensaje, language=None)
            st.cache_data.clear()
        else:
            st.error(mensaje)
            st.warning(
                t('La plantilla quedó guardada pero no se incorporó. '
                  'Corrija el archivo y vuelva a subirlo, o elimínelo de '
                  'la lista.'))

    presentes = _plantillas_presentes()
    if presentes:
        st.markdown(f"**{t('Plantillas cargadas')}**")
        for ruta in presentes:
            columna_nombre, columna_boton = st.columns([5, 1])
            columna_nombre.write(f'`{ruta.name}`')
            if columna_boton.button(t('Eliminar'), key=f'borrar_{ruta.name}'):
                ruta.unlink(missing_ok=True)
                exito, mensaje = _consolidar_y_reportar()
                st.cache_data.clear()
                if not exito:
                    st.warning(mensaje)
                st.rerun()
    else:
        st.info(t('Todavía no hay ninguna plantilla cargada.'))

    st.divider()

    # ── Parámetros ───────────────────────────────────────────────
    datos = _emisores_del_consolidado()
    if datos.empty:
        return

    st.markdown(f"**{t('Parámetros del modelo de costo de capital')}**")
    st.markdown(
        t('El sistema no calcula un costo de capital sobre parámetros '
          'ausentes: se detiene e indica cuál falta. Complételos aquí.'))

    izquierda, derecha = st.columns(2)

    with izquierda:
        st.markdown(f"**{t('Por ejercicio')}**")
        anios = sorted(datos['anio'].unique())
        if ARCHIVO_MERCADO.exists():
            mercado = pd.read_csv(ARCHIVO_MERCADO)
        else:
            mercado = pd.DataFrame(columns=['anio', 'tasa_libre_riesgo',
                                            'prima_riesgo_mercado',
                                            'prima_riesgo_pais'])
        mercado = (pd.DataFrame({'anio': anios})
                   .merge(mercado, on='anio', how='left'))
        editado_mercado = st.data_editor(
            mercado, hide_index=True, num_rows='fixed', key='ed_mercado',
            column_config={
                'anio': st.column_config.NumberColumn(t('Ejercicio'),
                                                      disabled=True,
                                                      format='%d'),
                'tasa_libre_riesgo': st.column_config.NumberColumn(
                    t('Tasa libre de riesgo'), format='%.4f'),
                'prima_riesgo_mercado': st.column_config.NumberColumn(
                    t('Prima de riesgo de mercado'), format='%.4f'),
                'prima_riesgo_pais': st.column_config.NumberColumn(
                    t('Prima de riesgo país'), format='%.4f')})
        if st.button(t('Guardar parámetros de mercado')):
            editado_mercado.to_csv(ARCHIVO_MERCADO, index=False)
            st.cache_data.clear()
            st.success(t('Guardado.'))
            st.rerun()

    with derecha:
        st.markdown(f"**{t('Por emisor')}**")
        emisores = sorted(datos['empresa'].unique())
        if ARCHIVO_SECTOR.exists():
            sector = pd.read_csv(ARCHIVO_SECTOR)
        else:
            sector = pd.DataFrame(columns=['empresa', 'sector',
                                           'beta_desapalancado'])
        # Los nombres provienen de los datos y no se escriben a mano: la
        # coincidencia debe ser exacta, y un nombre con coma transcrito
        # sin comillas en el archivo era la causa más frecuente de que un
        # parámetro pareciera ausente estando presente.
        sector = (pd.DataFrame({'empresa': emisores})
                  .merge(sector, on='empresa', how='left'))
        editado_sector = st.data_editor(
            sector, hide_index=True, num_rows='fixed', key='ed_sector',
            column_config={
                'empresa': st.column_config.TextColumn(t('Emisor'),
                                                       disabled=True),
                'sector': st.column_config.TextColumn(t('Sector')),
                'beta_desapalancado': st.column_config.NumberColumn(
                    t('Beta desapalancado'), format='%.4f')})
        if st.button(t('Guardar parámetros sectoriales')):
            editado_sector.to_csv(ARCHIVO_SECTOR, index=False)
            st.cache_data.clear()
            st.success(t('Guardado.'))
            st.rerun()

    st.caption(
        t('Los parámetros son estimaciones y constituyen decisiones '
          'metodológicas: registre la fuente y su fecha, porque un costo '
          'de capital sin ellas no es verificable.'))


# ── Idioma ───────────────────────────────────────────────────────

def selector_idioma():
    """
    Fija el idioma antes de que se dibuje nada de la página.

    El orden importa. Streamlit ejecuta el script de arriba abajo, de
    modo que todo rótulo escrito antes de leer este control conservaría
    el idioma de la pasada anterior: el título y el subtítulo quedarían
    en español dentro de una página en inglés hasta la interacción
    siguiente.
    """
    codigos = list(idioma.IDIOMAS)
    elegido = st.sidebar.radio(
        'Idioma / Language', codigos,
        index=codigos.index(idioma.actual()),
        format_func=lambda c: idioma.IDIOMAS[c],
        horizontal=True, key='idioma')
    idioma.fijar(elegido)
    st.sidebar.divider()
    return elegido


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

    st.sidebar.title(t('Muestra'))

    elegidos = st.sidebar.multiselect(
        t('Emisores'), options=completos, default=completos,
        help=t('Elija uno para el análisis individual, o varios para '
             'compararlos. El color de cada emisor no cambia al filtrar.'))

    anios = sorted(df['anio'].unique())
    if len(anios) > 1:
        desde, hasta = st.sidebar.select_slider(
            t('Ejercicios'), options=anios, value=(anios[0], anios[-1]),
            help=t('Acota el período. El análisis horizontal y la '
                 'descomposición de la variación toman como base el '
                 'primer ejercicio del intervalo.'))
    else:
        desde = hasta = anios[0]

    filtrado = df[df['empresa'].isin(elegidos)
                  & df['anio'].between(desde, hasta)].reset_index(drop=True)

    if filtrado.empty:
        st.sidebar.error(t('La selección no deja observaciones.'))
    else:
        total = len(completos)
        if len(elegidos) < total or (desde, hasta) != (anios[0], anios[-1]):
            st.sidebar.info(
                t('{n} de {total} emisores · ejercicios {a}–{b}').format(
                    n=len(elegidos), total=total, a=desde, b=hasta))

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

    st.sidebar.title(t('Parámetros del modelo'))
    st.sidebar.caption(
        t('Cada parámetro parte del valor registrado en el archivo. '
        'Actívelo para sustituirlo y observar el efecto sobre el '
        'resultado.'))

    for nombre, (etiqueta, minimo, maximo, paso, ayuda) in CONTROLES.items():
        inicial = base.get(nombre, (minimo + maximo) / 2)
        activo = st.sidebar.checkbox(t(etiqueta), value=False,
                                     key=f'ok_{nombre}', help=t(ayuda))
        valor = st.sidebar.slider(
            t(etiqueta), min_value=float(minimo), max_value=float(maximo),
            value=float(min(max(inicial, minimo), maximo)), step=float(paso),
            key=f'v_{nombre}', disabled=not activo,
            label_visibility='collapsed',
            format='%.4f' if paso < 0.01 else '%.2f')
        if activo:
            sustitutos[nombre] = valor
            activos.append(f'{t(etiqueta)}: {valor:.4f}')

    st.sidebar.divider()
    st.sidebar.subheader(t('Costo de capital impuesto'))
    st.sidebar.caption(
        t('Reemplaza al costo promedio ponderado que el modelo calcula. '
        'Sirve para contrastar el resultado frente a un costo de capital '
        'objetivo, sin recorrer la cadena completa del modelo.'))
    imponer = st.sidebar.checkbox(t('Imponer un WACC'), value=False)
    wacc_valor = st.sidebar.slider(
        t('WACC impuesto'), 0.04, 0.20, 0.10, 0.0025,
        disabled=not imponer, label_visibility='collapsed',
        format='%.4f') if True else None
    if not imponer:
        wacc_valor = None
    else:
        activos.append(f"{t('WACC impuesto')}: {wacc_valor:.4f}")

    st.sidebar.divider()
    if activos:
        st.sidebar.warning(t('Parámetros sustituidos:') + '\n\n'
                           + '\n\n'.join(f'- {a}' for a in activos))
    else:
        st.sidebar.success(t('Todos los parámetros provienen del archivo.'))

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

    c1.metric(t('Emisores'), df['empresa'].nunique(),
              help=t('Emisores incluidos en la selección actual.'))

    c2.metric(
        t('WACC promedio'), f"{actual['wacc_medio']:.2%}",
        delta=(f"{actual['wacc_medio'] - base['wacc_medio']:+.2%}"
               if hay_cambio else None),
        delta_color='inverse',
        help=t('Promedio simple del costo promedio ponderado de capital '
             'sobre todas las observaciones.'))

    c3.metric(
        t('EVA agregado'), f"{actual['eva_total']:,.0f}",
        delta=(f"{actual['eva_total'] - base['eva_total']:+,.0f}"
               if hay_cambio else None),
        help=t('Suma del valor económico agregado de todos los emisores y '
             'ejercicios.'))

    c4.metric(
        t('Observaciones que crean valor'),
        t('{n} de {total}').format(n=actual['crean'],
                                   total=actual['observaciones']),
        delta=(f"{actual['crean'] - base['crean']:+d}"
               if hay_cambio else None),
        help=t('Observaciones con valor económico agregado positivo.'))

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


def _tabla(tabla, porcentajes=()):
    """
    Presenta una tabla con sus encabezados y sus valores de texto
    traducidos al idioma vigente.

    Los nombres de emisor no se traducen: son nombres propios. Sí se
    traducen las columnas y los valores de clasificación —las zonas de
    Altman, el veredicto del EVA—, que son términos del modelo y no
    datos del emisor.
    """
    tabla = idioma.traducir_columnas(tabla)
    for columna in tabla.columns:
        if tabla[columna].dtype == object and columna not in ('issuer', 'empresa'):
            tabla[columna] = idioma.traducir_valores(tabla[columna])
    return _formato(tabla, [t(c) for c in porcentajes])


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

    st.subheader(t('Razones financieras'))
    st.markdown(
        t('El sistema calcula **{n} indicadores** agrupados en cuatro '
          'categorías. Ninguno responde por sí solo si la empresa va bien: '
          'el margen neto no sabe si puede pagar la nómina del mes, y la '
          'razón corriente no sabe si el negocio es rentable. Se leen en '
          'conjunto.').format(n=conteo['TOTAL']))

    columnas = st.columns(len(mod_ratios.CATEGORIAS))
    for columna, categoria in zip(columnas, mod_ratios.CATEGORIAS):
        columna.metric(t(categoria), conteo.get(categoria, 0))

    st.divider()

    # format_func traduce lo que se muestra sin alterar el valor que la
    # función devuelve: el código sigue recibiendo el nombre en español,
    # que es la clave con que el catálogo identifica cada categoría.
    categoria = st.radio(
        t('Categoría'), mod_ratios.CATEGORIAS, horizontal=True, format_func=t,
        help=t('Cada categoría responde una pregunta distinta sobre la '
             'misma empresa.'))

    _figura(lambda: charts.indicadores(df, categoria, dir_salida=None))

    tabla = mod_ratios.calcular_todos(df, categoria=categoria)
    st.dataframe(_tabla(tabla, []), hide_index=True)

    st.caption(
        t('Un valor ausente indica que el indicador no aplica al emisor y '
        'ejercicio correspondientes, no que valga cero. Un ROE calculado '
        'sobre patrimonio negativo, por ejemplo, resultaría positivo por '
        'cancelación de signos y carecería de significado económico, de '
        'modo que se excluye.'))


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

    st.subheader(t('Composición y evolución'))

    vertical_, horizontal_ = st.tabs([t('Análisis vertical'),
                                      t('Análisis horizontal')])

    with vertical_:
        st.markdown(
            t('Cada partida como porcentaje de un total del mismo ejercicio: '
            'el activo total en el balance, las ventas netas en el estado '
            'de resultados. La lectura de márgenes es inmediata, porque la '
            'fila de utilidad bruta **es** el margen bruto.'))

        _figura(lambda: charts.vertical_activo(estados, dir_salida=None))
        _figura(lambda: charts.vertical_resultados(estados, dir_salida=None))

        cual = st.radio(t('Tabla'), ['Balance general', 'Estado de resultados'],
                        horizontal=True, format_func=t, key='tabla_vertical')
        tabla = (mod_vertical.vertical_balance(estados)
                 if cual == 'Balance general'
                 else mod_vertical.vertical_resultados(estados))
        st.dataframe(_tabla(tabla, []), hide_index=True)

    with horizontal_:
        st.markdown(
            t('La variación de cada partida respecto del ejercicio anterior, '
            'y los números índice respecto de un año base igual a cien. '
            'Los índices permiten comparar en una misma escala partidas de '
            'magnitudes muy distintas.'))

        _figura(lambda: charts.horizontal_indices(estados, dir_salida=None))

        cual = st.radio(
            t('Tabla'), ['Números índice', 'Variación interanual (%)',
                         'Variación absoluta'],
            horizontal=True, format_func=t, key='tabla_horizontal')
        if cual == 'Números índice':
            tabla = mod_horizontal.numeros_indice(estados)
        elif cual.startswith('Variación interanual'):
            tabla = mod_horizontal.variacion_interanual(estados)
        else:
            tabla = mod_horizontal.variacion_absoluta(estados)
        st.dataframe(_tabla(tabla, []), hide_index=True)

        st.caption(
            t('El primer ejercicio de cada emisor queda sin variación '
            'interanual porque no tiene período de comparación. La fila se '
            'conserva para que las tablas puedan alinearse entre sí.'))


def pestana_valor(df, tabla_eva, sustitutos, wacc_valor):
    """Creación o destrucción de valor."""
    st.subheader(t('Creación y destrucción de valor'))
    st.markdown(
        t('El valor económico agregado contrasta el resultado operativo '
        'después de impuestos con el costo del capital empleado para '
        'generarlo. Una empresa puede presentar utilidad contable '
        'positiva y destruir valor económico, si el rendimiento del '
        'capital invertido no compensa el costo de los recursos.'))

    _figura(lambda: charts.eva(df, dir_salida=None,
                               **({'wacc_valor': wacc_valor} if wacc_valor
                                  else {}), **sustitutos))
    _figura(lambda: charts.roic_wacc(df, dir_salida=None,
                                     **({'wacc_valor': wacc_valor}
                                        if wacc_valor else {}),
                                     **sustitutos))

    st.dataframe(_tabla(tabla_eva, ['ROIC', 'WACC',
                                          'Diferencial ROIC − WACC']),
                 hide_index=True)


def pestana_sensibilidad(df):
    """Umbral de creación de valor."""
    st.subheader(t('Sensibilidad al costo de capital'))
    st.markdown(
        t('El umbral es la cifra que acota la conclusión. Por encima de ese '
        'costo de capital el emisor destruye valor; por debajo, lo crea. '
        'La distancia que lo separa del costo estimado indica cuán '
        'robusta es la conclusión frente al supuesto adoptado.'))
    _figura(lambda: charts.sensibilidad_eva(df, dir_salida=None))

    st.caption(
        t('La figura emplea los parámetros del archivo con independencia de '
        'los controles, pues su objeto es precisamente recorrer el '
        'intervalo completo de costos de capital posibles.'))


def pestana_costo(df, sustitutos):
    """Costo del capital."""
    st.subheader(t('Costo del capital'))
    st.markdown(
        t('El costo promedio ponderado combina el costo del patrimonio, '
        'estimado por el modelo de valoración de activos de capital, con '
        'el costo de la deuda, obtenido de los estados financieros. El '
        'endeudamiento incide en dos direcciones opuestas: incrementa el '
        'riesgo que percibe el accionista y, a la vez, aumenta la '
        'participación de una fuente más barata y fiscalmente deducible.'))

    _figura(lambda: charts.composicion_wacc(df, dir_salida=None, **sustitutos))

    izquierda, derecha = st.columns(2)
    with izquierda:
        st.markdown(t('**Costo del patrimonio**'))
        st.dataframe(
            _tabla(mod_capm.calcular(
                df, **{k: v for k, v in sustitutos.items() if k != 'kd'}),
                ['Rf', 'ERP', 'CRP', 'Tasa impuesto', 'Ke',
                 'Prima por riesgo sistemático']),
            hide_index=True)
    with derecha:
        st.markdown(t('**Costo promedio ponderado**'))
        st.dataframe(
            _tabla(mod_wacc.calcular(df, **sustitutos),
                         ['Peso patrimonio', 'Peso deuda', 'Ke', 'Kd',
                          'Kd después de impuestos', 'WACC',
                          'Aporte del patrimonio', 'Aporte de la deuda']),
            hide_index=True)


def pestana_riesgo(df):
    """Riesgo de insolvencia."""
    st.subheader(t('Riesgo de insolvencia'))
    st.markdown(
        t("El puntaje Z'' de cuatro variables corresponde a empresas sin "
        'cotización bursátil, que es la condición de los emisores '
        'dominicanos del mercado de valores: colocan deuda y no acciones, '
        'de modo que no existe precio de mercado de su patrimonio.'))

    _figura(lambda: charts.altman(df, dir_salida=None))

    tabla = mod_altman.calcular(df)
    st.dataframe(_tabla(tabla), hide_index=True)

    conteo = mod_altman.resumen_zonas(df)
    c1, c2, c3 = st.columns(3)
    c1.metric(t('Zona segura'), conteo.get('Segura', 0))
    c2.metric(t('Zona gris'), conteo.get('Gris', 0))
    c3.metric(t('Zona de peligro'), conteo.get('Peligro', 0))


def pestana_rendimiento(df):
    """Descomposición del rendimiento."""
    st.subheader(t('Descomposición del rendimiento'))
    st.markdown(
        t('El rendimiento sobre el patrimonio es el producto de sus '
        'factores, no su suma. La descomposición permite atribuir una '
        'variación a su causa: el desempeño de la operación, el costo del '
        'financiamiento o la carga tributaria, cada una de las cuales '
        'exige una respuesta distinta.'))

    nivel = st.radio(t('Nivel de descomposición'), [2, 3], index=1,
                     horizontal=True,
                     help=t('El nivel 2 descompone en tres factores; el '
                          'nivel 3 desagrega el margen neto en carga '
                          'fiscal, carga financiera y margen operativo.'))
    _figura(lambda: charts.dupont_factores(df, dir_salida=None, nivel=nivel))

    emisor = st.selectbox(t('Emisor para la descomposición de la variación'),
                          charts._emisores(df))
    try:
        _figura(lambda: charts.dupont_contribucion(df, emisor,
                                                   dir_salida=None,
                                                   nivel=nivel))
    except ValueError as error:
        st.info(str(error))

    st.dataframe(_tabla(mod_dupont.dupont_nivel_3(df) if nivel == 3
                        else mod_dupont.dupont_nivel_2(df)),
                 hide_index=True)


def pestana_validacion(df, sustitutos, wacc_valor):
    """Consistencia interna."""
    st.subheader(t('Consistencia interna'))
    st.markdown(
        t('Las identidades algebraicas del sistema se comprueban en cada '
        'ejecución. Son verificaciones de consistencia interna: contrastan '
        'el sistema contra sí mismo y no contra una fuente externa, de '
        'modo que detectan incoherencia de cálculo y no error de origen '
        'en los datos.'))

    resumen = mod_dupont.resumen_verificacion(df)
    identidad_eva = mod_eva.verificar_identidad(
        df, wacc_valor=wacc_valor, **sustitutos)

    filas = [
        {'Comprobación': t('Identidad DuPont nivel 2'),
         'Observaciones': resumen['observaciones'],
         'Satisfacen': resumen['nivel_2_coinciden'],
         'Discrepancia máxima': resumen['diferencia_maxima_nivel_2']},
        {'Comprobación': t('Identidad DuPont nivel 3'),
         'Observaciones': resumen['observaciones'],
         'Satisfacen': resumen['nivel_3_coinciden'],
         'Discrepancia máxima': resumen['diferencia_maxima_nivel_3']},
        {'Comprobación': t('Equivalencia de las formulaciones del EVA'),
         'Observaciones': len(identidad_eva),
         'Satisfacen': int(identidad_eva['Coincide'].sum()),
         'Discrepancia máxima': float(
             identidad_eva['Diferencia relativa'].max())},
    ]
    tabla = pd.DataFrame(filas)
    # El veredicto se decide comparando números y no el texto que se
    # muestra: ese texto se traduce, y contrastarlo contra una redacción
    # fija daría por fallida toda comprobación en otro idioma.
    satisfacen = tabla['Satisfacen'] == tabla['Observaciones']
    tabla['Resultado'] = [t('Satisface') if ok else t('Revisar')
                          for ok in satisfacen]

    st.dataframe(_tabla(tabla).format({t('Discrepancia máxima'): '{:.2e}'}),
                 hide_index=True)

    if satisfacen.all():
        st.success(t('Todas las comprobaciones de consistencia interna se '
                   'satisfacen.'))
    else:
        st.error(t('Alguna comprobación no se satisface. Revise los datos de '
                 'entrada.'))

    st.caption(
        t('Las discrepancias del orden de 1e-17 no constituyen error: son el '
        'residuo de la aritmética de punto flotante, que no representa los '
        'números reales con precisión infinita.'))


# ── Composición de la página ─────────────────────────────────────

def main():
    """Arma la página."""
    st.set_page_config(page_title='FinAnalyzer Pro',
                       page_icon='📊', layout='wide')

    selector_idioma()

    st.title(t('FinAnalyzer Pro'))

    # Sin datos no hay panel, pero sí hay algo que hacer: cargarlos. La
    # pestaña de datos se presenta sola, de modo que el sistema sea
    # utilizable desde una instalación limpia sin recurrir a la terminal.
    if not ARCHIVO_ENTRADA.exists():
        st.info(t('Todavía no hay datos cargados. Suba al menos una '
                  'plantilla para comenzar.'))
        pestana_datos()
        st.stop()

    try:
        # Se pasan también las marcas de los archivos de parámetros:
        # el conjunto resultante depende de los tres.
        df = cargar(str(ARCHIVO_ENTRADA),
                    (marca_de(ARCHIVO_ENTRADA),
                     marca_de(ARCHIVO_MERCADO),
                     marca_de(ARCHIVO_SECTOR)))
    except (FileNotFoundError, ValueError) as error:
        # Un parámetro ausente se corrige desde la misma pestaña que lo
        # declara: interrumpir sin ofrecer dónde arreglarlo obligaba a
        # editar archivos CSV a mano, que es donde se originaba el error.
        st.error(str(error))
        pestana_datos()
        st.stop()

    # El subtítulo se escribe una vez cargados los datos, porque declara
    # el período que efectivamente contienen.
    st.caption(
        t('Análisis de estados financieros de emisores no financieros '
          'dominicanos, {periodo}').format(periodo=periodo(df)))

    seleccion = seleccionar(df)

    # Los controles de parámetros se dibujan siempre, aun con la
    # selección vacía: una barra lateral incompleta se lee como una
    # falla. Cuando no hay observaciones se toman del conjunto completo,
    # que solo determina el valor inicial de cada control.
    sustitutos, wacc_valor = barra_lateral(
        seleccion if not seleccion.empty else df)

    if seleccion.empty:
        st.info(t('No hay ningún emisor seleccionado.\n\n'
                'Elija al menos uno en la barra lateral para ver el '
                'análisis. Los parámetros del modelo quedan como estaban.'))
        st.stop()

    df = seleccion
    tabla_eva = encabezado(df, sustitutos, wacc_valor)
    st.divider()

    (estructura, indicadores, valor, sensibilidad, costo, riesgo,
     rendimiento, validacion, datos) = st.tabs(
        [t('Estructura'), t('Indicadores'), t('Valor'), t('Sensibilidad'),
         t('Costo de capital'), t('Riesgo'), t('Rendimiento'),
         t('Validación'), t('Datos')])

    with datos:
        pestana_datos()
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