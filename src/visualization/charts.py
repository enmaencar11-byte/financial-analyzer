"""
Generación de las figuras del capítulo de resultados.

Cada función produce una figura que responde una pregunta concreta del
análisis, y la escribe como archivo de imagen apto para su inserción en
el documento. El módulo no calcula nada: toma los resultados que los
módulos de análisis producen y los representa.

CRITERIOS DE REPRESENTACIÓN

La forma del gráfico se elige según la naturaleza del dato y no según su
apariencia. Tres decisiones merecen justificación explícita.

Los cinco factores de la descomposición DuPont no se apilan. Una barra
apilada afirma que sus segmentos suman el total, y el rendimiento sobre
el patrimonio es el producto de sus factores, no su suma. Representarlos
apilados comunicaría una relación aritmética que no existe. Se presentan
en paneles separados, uno por factor.

Los aportes del patrimonio y de la deuda al costo promedio ponderado sí
se apilan, porque efectivamente suman el costo total. La distinción no es
estética: una afirma algo verdadero y la otra algo falso.

Los aportes logarítmicos a la variación del rendimiento suman cien por
ciento por construcción, de modo que admiten una representación de
cascada, que es la forma adecuada para una magnitud descompuesta sin
residuo.

LEGIBILIDAD EN IMPRESIÓN

El documento puede imprimirse en escala de grises, caso en que el color
deja de distinguir las series. Cada emisor lleva por tanto un marcador y
un trazo propios, y cada relleno una trama, de modo que la identidad de
la serie no depende del color. La paleta se verificó además para las
formas más frecuentes de visión cromática deficiente.

Las figuras se escriben a trescientos puntos por pulgada, con un ancho de
seis pulgadas y media, que es el ancho útil de una página tamaño carta
con márgenes de una pulgada. Insertadas sin reescalar conservan la
nitidez del texto.
"""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')          # sin interfaz gráfica: solo escribe archivos

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from src.analysis import altman as mod_altman
from src.analysis import dupont as mod_dupont
from src.analysis import eva as mod_eva
from src.analysis import vertical as mod_vertical
from src.analysis import wacc as mod_wacc

RAIZ = Path(__file__).resolve().parent.parent.parent
DIR_FIGURAS = RAIZ / 'outputs' / 'figuras'

IDENTIFICADORES = ['empresa', 'anio']

# ── Parámetros de salida ─────────────────────────────────────────

RESOLUCION = 300               # puntos por pulgada, apto para impresión
ANCHO = 6.5                    # pulgadas: ancho útil de una página carta
ALTO = 4.0
FORMATO = 'png'

# ── Paleta ───────────────────────────────────────────────────────

# Orden fijo de asignación: el color identifica al emisor y no su
# posición en la tabla. Un filtro que reduzca la muestra no debe
# repintar a los emisores que permanecen.
COLORES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4',
           '#008300', '#6250d6', '#e34948']

# Codificación secundaria para la impresión en escala de grises.
MARCADORES = ['o', 's', '^', 'D', 'v', 'P', 'X', '*']
TRAZOS = ['-', '--', '-.', ':', (0, (3, 1, 1, 1)), (0, (5, 2)),
          (0, (1, 1)), (0, (4, 1, 1, 1, 1, 1))]
TRAMAS = ['', '///', '...', '\\\\\\', 'xxx', '|||', '---', '+++']

# Colores de estado. Reservados: no se emplean para identificar series.
VERDE = '#1baf7a'
AMBAR = '#eda100'
ROJO = '#e34948'
TINTA = '#0b0b0b'
TINTA_SUAVE = '#52514e'
REJILLA = '#d8d7d2'


def _estilo():
    """
    Fija los parámetros comunes de presentación.

    La rejilla y los ejes se mantienen discretos: compiten con los datos
    por la atención del lector y no aportan información propia.
    """
    plt.rcParams.update({
        'figure.dpi': RESOLUCION,
        'savefig.dpi': RESOLUCION,
        'savefig.bbox': 'tight',
        'savefig.facecolor': 'white',
        'font.size': 9,
        'axes.titlesize': 10,
        'axes.titleweight': 'bold',
        'axes.labelsize': 9,
        'axes.edgecolor': TINTA_SUAVE,
        'axes.labelcolor': TINTA,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.color': REJILLA,
        'grid.linewidth': 0.6,
        'legend.frameon': False,
        'legend.fontsize': 8,
        'xtick.color': TINTA_SUAVE,
        'ytick.color': TINTA_SUAVE,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
    })


def _emisores(df):
    """Emisores en el orden en que aparecen, sin repetir."""
    return list(dict.fromkeys(df['empresa']))


def _anios(df):
    """Ejercicios ordenados."""
    return sorted(df['anio'].unique())


def _partir(nombre, ancho=14):
    """
    Reparte un nombre largo en varias líneas, sin cortar palabras.

    Los nombres de los emisores dominicanos son largos y, rotulados en
    una sola línea bajo el eje, se solapan entre sí. Partirlos conserva
    la horizontalidad, que se lee mejor que un rótulo inclinado.
    """
    lineas, actual = [], ''
    for palabra in str(nombre).split():
        if actual and len(actual) + 1 + len(palabra) > ancho:
            lineas.append(actual)
            actual = palabra
        else:
            actual = f'{actual} {palabra}'.strip()
    if actual:
        lineas.append(actual)
    return '\n'.join(lineas)


def _guardar(figura, nombre, dir_salida):
    """Escribe la figura y la cierra, para no acumular memoria."""
    dir_salida = Path(dir_salida)
    dir_salida.mkdir(parents=True, exist_ok=True)
    ruta = dir_salida / f'{nombre}.{FORMATO}'
    figura.savefig(ruta)
    plt.close(figura)
    return ruta


def _paneles(cantidad, alto_panel=2.1, columnas=None, compartir_y=False):
    """
    Dispone una rejilla de paneles para un conjunto de series.

    Los paneles separados son la forma correcta cuando varias series
    comparten escala pero no deben leerse superpuestas: con cinco emisores
    y dos medidas, un solo eje produciría diez trazos indistinguibles.

    El argumento compartir_y decide una cuestión de fondo y no de
    apariencia. Cuando la figura invita a comparar magnitudes entre
    paneles, la escala debe ser común: con escalas independientes, una
    diferencia de un punto porcentual y otra de seis ocupan el mismo
    espacio y la comparación resulta imposible. Cuando los paneles
    representan magnitudes de órdenes distintos, en cambio, una escala
    común aplastaría las menores contra el eje.

    Las etiquetas del eje horizontal se habilitan en el panel inferior de
    cada columna. La última fila puede quedar incompleta, y sin este
    ajuste los paneles de la fila anterior que no tienen otro debajo
    quedarían sin ejercicios rotulados.
    """
    columnas = columnas or min(cantidad, 3)
    filas = int(np.ceil(cantidad / columnas))
    figura, ejes = plt.subplots(filas, columnas, figsize=(ANCHO, alto_panel * filas),
                               sharex=True, sharey=compartir_y, squeeze=False)
    planos = ejes.ravel()
    for eje in planos[cantidad:]:
        eje.set_visible(False)

    for indice in range(cantidad):
        debajo = indice + columnas
        if debajo >= cantidad:
            planos[indice].tick_params(labelbottom=True)

    return figura, planos[:cantidad]


# ── 1. Riesgo de insolvencia ─────────────────────────────────────

def altman(df, dir_salida=DIR_FIGURAS):
    """
    Puntaje Z'' por emisor y ejercicio, sobre las tres zonas de
    clasificación.

    DECISIÓN DE DISEÑO: el eje vertical se extiende siempre hasta
    comprender los dos umbrales, aun cuando ningún emisor se aproxime a
    ellos. Un eje ajustado a los datos observados ocultaría las zonas y
    con ello el único referente que da sentido al puntaje: la distancia
    que separa a cada emisor de la zona de peligro es información, y un
    eje que empiece en el mínimo observado la suprime.
    """
    _estilo()
    tabla = mod_altman.calcular(df)
    anios = _anios(df)
    figura, eje = plt.subplots(figsize=(ANCHO, ALTO))

    limites = mod_altman.umbrales()
    inferior = limites['zona_peligro_hasta']
    superior = limites['zona_segura_desde']

    # Bandas de zona. Color de estado, no de serie.
    eje.axhspan(superior, max(superior * 2.6, tabla["Z''"].max() * 1.12),
                color=VERDE, alpha=0.08, zorder=0)
    eje.axhspan(inferior, superior, color=AMBAR, alpha=0.10, zorder=0)
    eje.axhspan(min(0, tabla["Z''"].min() * 1.2), inferior,
                color=ROJO, alpha=0.10, zorder=0)

    for umbral in (inferior, superior):
        eje.axhline(umbral, color=TINTA_SUAVE, linewidth=0.8,
                    linestyle='--', zorder=1)

    for i, emisor in enumerate(_emisores(df)):
        sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
        eje.plot(sub['anio'], sub["Z''"], color=COLORES[i % len(COLORES)],
                 linestyle=TRAZOS[i % len(TRAZOS)], marker=MARCADORES[i % len(MARCADORES)],
                 markersize=5, linewidth=2, label=emisor, zorder=3)

    eje.set_xticks(anios)
    eje.set_xlabel('Ejercicio')
    eje.set_ylabel("Puntaje Z''")
    eje.set_title("Riesgo de insolvencia — Altman Z'' de cuatro variables")
    eje.set_ylim(min(0, tabla["Z''"].min() * 1.2),
                 max(superior * 1.2, tabla["Z''"].max() * 1.12))

    # Etiquetas de zona dentro de la propia banda: el lector no debe
    # cotejar la leyenda para saber qué significa cada franja.
    limite = eje.get_xlim()
    for texto, altura, color in (
            ('Zona segura', superior, VERDE),
            ('Zona gris', (inferior + superior) / 2, AMBAR),
            ('Zona de peligro', inferior / 2, ROJO)):
        if eje.get_ylim()[0] <= altura <= eje.get_ylim()[1]:
            eje.annotate(texto, xy=(limite[1], altura), xytext=(-4, 4),
                         textcoords='offset points', ha='right', va='bottom',
                         fontsize=7, color=color, style='italic')

    eje.legend(loc='upper left', ncols=2)
    return _guardar(figura, '01_altman_zonas', dir_salida)


# ── 2. Creación o destrucción de valor ───────────────────────────

def roic_wacc(df, dir_salida=DIR_FIGURAS, **sustitutos):
    """
    Retorno sobre el capital invertido frente a su costo, por emisor.

    El área entre las dos curvas es el objeto de lectura: su signo decide
    si el emisor crea o destruye valor, y su amplitud indica la holgura
    con que lo hace. Se colorea según el signo, lo que convierte la
    comparación en algo que se resuelve de un vistazo.

    Se emplean paneles separados y no un solo eje porque cinco emisores
    con dos medidas producirían diez trazos sobre la misma escala.
    """
    _estilo()
    tabla = mod_eva.calcular(df, **sustitutos)
    emisores = _emisores(df)
    anios = _anios(df)
    # Escala vertical común: la figura se lee comparando la amplitud del
    # área entre las curvas, y esa comparación exige una escala única.
    figura, ejes = _paneles(len(emisores), alto_panel=2.0, compartir_y=True)

    for eje, emisor in zip(ejes, emisores):
        sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
        x = sub['anio'].to_numpy()
        roic = sub['ROIC'].to_numpy(dtype=float)
        wacc_ = sub['WACC'].to_numpy(dtype=float)

        eje.fill_between(x, roic, wacc_, where=roic >= wacc_,
                         color=VERDE, alpha=0.22, interpolate=True)
        eje.fill_between(x, roic, wacc_, where=roic < wacc_,
                         color=ROJO, alpha=0.22, interpolate=True)
        eje.plot(x, roic, color=COLORES[0], linewidth=2, marker='o',
                 markersize=4, label='ROIC')
        eje.plot(x, wacc_, color=TINTA_SUAVE, linewidth=2, linestyle='--',
                 marker='s', markersize=4, label='WACC')

        eje.set_title(emisor, fontsize=9)
        eje.set_xticks(anios)
        eje.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f'{v:.0%}'))

    # La leyenda va al pie de la figura y no dentro de un panel: con un
    # área sombreada que ocupa el centro del gráfico, cualquier posición
    # interior se superpone a los datos.
    manejos = [Line2D([], [], color=COLORES[0], linewidth=2, marker='o',
                      markersize=4, label='ROIC'),
               Line2D([], [], color=TINTA_SUAVE, linewidth=2, linestyle='--',
                      marker='s', markersize=4, label='WACC'),
               Patch(facecolor=VERDE, alpha=0.22, label='Crea valor'),
               Patch(facecolor=ROJO, alpha=0.22, label='Destruye valor')]
    figura.legend(handles=manejos, loc='lower center', ncols=4, fontsize=7.5,
                  bbox_to_anchor=(0.5, -0.05))
    figura.suptitle('Retorno sobre el capital invertido frente a su costo',
                    fontsize=10, fontweight='bold', y=1.0)
    figura.supxlabel('Ejercicio', fontsize=9)
    figura.supylabel('Tasa anual', fontsize=9)
    figura.tight_layout()
    return _guardar(figura, '02_roic_vs_wacc', dir_salida)


def eva(df, dir_salida=DIR_FIGURAS, **sustitutos):
    """
    Valor económico agregado por emisor y ejercicio.

    Una magnitud con signo se representa como barras sobre un eje cero, y
    no como una línea: el cruce del eje es el hecho relevante, y la barra
    lo vuelve inmediato. El color distingue el signo, que es una
    polaridad y no una identidad, de modo que emplea los colores de
    estado y no los de serie.
    """
    _estilo()
    tabla = mod_eva.calcular(df, **sustitutos)
    emisores = _emisores(df)
    anios = _anios(df)
    figura, eje = plt.subplots(figsize=(ANCHO, ALTO + 0.4))

    ancho_barra = 0.8 / len(anios)
    posiciones = np.arange(len(emisores))

    for j, anio in enumerate(anios):
        valores = [
            float(tabla.loc[(tabla['empresa'] == e) & (tabla['anio'] == anio),
                            'EVA'].squeeze() or 0)
            for e in emisores]
        x = posiciones - 0.4 + ancho_barra * (j + 0.5)
        colores = [VERDE if v >= 0 else ROJO for v in valores]
        # Sin trama: el ejercicio va rotulado sobre cada barra, de modo
        # que la identidad no depende del color y una trama adicional
        # solo agregaría ruido visual.
        eje.bar(x, valores, width=ancho_barra * 0.88, color=colores,
                alpha=0.9, edgecolor='white', linewidth=0.8, zorder=2)
        for xi, v in zip(x, valores):
            eje.annotate(str(anio), xy=(xi, 0), xytext=(0, -3 if v >= 0 else 3),
                         textcoords='offset points', ha='center',
                         va='top' if v >= 0 else 'bottom',
                         fontsize=6, color=TINTA_SUAVE, rotation=90)

    eje.axhline(0, color=TINTA, linewidth=1.1, zorder=3)
    eje.set_xticks(posiciones)
    eje.set_xticklabels([_partir(e) for e in emisores], fontsize=8)
    eje.set_ylabel('EVA (unidades monetarias)')
    eje.set_title('Valor económico agregado por emisor y ejercicio')
    eje.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:,.0f}'))
    eje.grid(axis='x', visible=False)

    eje.legend(handles=[Patch(facecolor=VERDE, alpha=0.85, label='Crea valor'),
                        Patch(facecolor=ROJO, alpha=0.85, label='Destruye valor')],
               loc='upper left', ncols=2)
    figura.tight_layout()
    return _guardar(figura, '03_eva', dir_salida)


# ── 3. Costo del capital ─────────────────────────────────────────

def composicion_wacc(df, dir_salida=DIR_FIGURAS, **sustitutos):
    """
    Descomposición del costo promedio ponderado en sus dos aportes.

    Los segmentos se apilan porque efectivamente suman el total: el
    aporte del patrimonio más el aporte de la deuda es el costo promedio
    ponderado, por definición. Es la diferencia con la descomposición
    DuPont, cuyos factores se multiplican y por tanto no admiten esta
    representación.
    """
    _estilo()
    tabla = mod_wacc.calcular(df, **sustitutos)
    emisores = _emisores(df)
    anios = _anios(df)
    figura, ejes = _paneles(len(emisores), alto_panel=2.0)

    for eje, emisor in zip(ejes, emisores):
        sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
        x = np.arange(len(sub))
        patrimonio = sub['Aporte del patrimonio'].to_numpy(dtype=float)
        deuda = sub['Aporte de la deuda'].to_numpy(dtype=float)

        eje.bar(x, patrimonio, width=0.62, color=COLORES[0], alpha=0.9,
                edgecolor='white', linewidth=1.2, label='Patrimonio')
        eje.bar(x, deuda, width=0.62, bottom=patrimonio, color=COLORES[1],
                alpha=0.9, edgecolor='white', linewidth=1.2,
                hatch='///', label='Deuda')

        for xi, total in zip(x, patrimonio + deuda):
            eje.annotate(f'{total:.1%}', xy=(xi, total), xytext=(0, 3),
                         textcoords='offset points', ha='center',
                         fontsize=7, color=TINTA)

        eje.set_title(emisor, fontsize=9)
        eje.set_xticks(x)
        eje.set_xticklabels([str(a) for a in sub['anio']], fontsize=7)
        eje.set_ylim(0, (patrimonio + deuda).max() * 1.28)
        eje.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
        eje.grid(axis='x', visible=False)

    manejos, etiquetas = ejes[0].get_legend_handles_labels()
    figura.legend(manejos, etiquetas, loc='lower center', ncols=2,
                  fontsize=7.5, bbox_to_anchor=(0.5, -0.11))
    figura.suptitle('Composición del costo promedio ponderado de capital',
                    fontsize=10, fontweight='bold', y=1.0)
    figura.tight_layout()
    return _guardar(figura, '04_composicion_wacc', dir_salida)


# ── 4. Descomposición del rendimiento ────────────────────────────

def dupont_factores(df, dir_salida=DIR_FIGURAS, nivel=3):
    """
    Evolución de cada factor de la descomposición DuPont.

    Un panel por factor, con una línea por emisor. Los factores NO se
    apilan ni se suman en una sola barra: el rendimiento sobre el
    patrimonio es su producto, y una representación apilada afirmaría una
    relación aditiva inexistente.

    Cada panel lleva su propia escala vertical, porque los factores
    difieren en orden de magnitud: una carga fiscal se mueve entre cero y
    uno, un apalancamiento entre uno y cuatro. Compartir escala
    aplastaría los primeros contra el eje.
    """
    _estilo()
    tabla = (mod_dupont.dupont_nivel_3(df) if nivel == 3
             else mod_dupont.dupont_nivel_2(df))
    factores = [c for c in tabla.columns
                if c not in IDENTIFICADORES
                and not c.startswith('ROE')]
    emisores = _emisores(df)
    anios = _anios(df)

    figura, ejes = _paneles(len(factores) + 1, alto_panel=1.9,
                            columnas=min(3, len(factores) + 1))

    for eje, factor in zip(ejes, factores + ['ROE reportado']):
        for i, emisor in enumerate(emisores):
            sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
            eje.plot(sub['anio'], sub[factor], color=COLORES[i % len(COLORES)],
                     linestyle=TRAZOS[i % len(TRAZOS)],
                     marker=MARCADORES[i % len(MARCADORES)],
                     markersize=4, linewidth=1.6, label=emisor)
        eje.set_title(factor, fontsize=8.5)
        eje.set_xticks(anios)
        eje.tick_params(labelsize=7)

    ejes[-1].set_title('ROE (producto de los factores)', fontsize=8.5)

    manejos = [Line2D([], [], color=COLORES[i % len(COLORES)],
                      linestyle=TRAZOS[i % len(TRAZOS)],
                      marker=MARCADORES[i % len(MARCADORES)],
                      markersize=4, linewidth=1.6, label=e)
               for i, e in enumerate(emisores)]
    figura.legend(handles=manejos, loc='lower center',
                  ncols=min(3, len(emisores)), fontsize=7.5,
                  bbox_to_anchor=(0.5, -0.11))
    figura.suptitle(f'Descomposición DuPont de nivel {nivel} — evolución por factor',
                    fontsize=10, fontweight='bold', y=1.0)
    figura.tight_layout()
    return _guardar(figura, f'05_dupont_factores_nivel{nivel}', dir_salida)


def dupont_contribucion(df, emisor=None, dir_salida=DIR_FIGURAS, nivel=3,
                        anio_inicial=None, anio_final=None):
    """
    Aporte de cada factor a la variación del rendimiento, en cascada.

    La cascada es la forma adecuada porque los aportes logarítmicos suman
    exactamente cien por ciento, sin residuo: cada barra parte de donde
    terminó la anterior y la última cierra en el total. Una
    representación en barras independientes perdería esa propiedad, que
    es justamente lo que hace exacta a la descomposición.

    La tabla de contribución incluye una fila final con el rendimiento
    mismo, cuyo aporte es por construcción el cien por ciento. Esa fila
    no es un factor sino el total, y se excluye de las barras de la
    cascada: incorporarla duplicaría la suma. Se emplea, en cambio, para
    rotular la variación efectiva del rendimiento, que es el dato que da
    sentido a los porcentajes.

    Si no se indica emisor se toma el primero de la muestra. El uso
    habitual es generar una figura por emisor.
    """
    _estilo()
    contribucion = mod_dupont.contribucion_factores(
        df, nivel=nivel, anio_inicial=anio_inicial, anio_final=anio_final)

    emisor = emisor or _emisores(df)[0]
    sub = contribucion[contribucion['empresa'] == emisor].copy()
    if sub.empty:
        raise ValueError(f'El emisor {emisor} no está en la muestra.')

    columna_aporte = next(c for c in sub.columns if 'aporte' in c.lower())
    columna_factor = next(c for c in ('factor', 'Factor') if c in sub.columns)
    columnas_valor = [c for c in sub.columns if c.lower().startswith('valor')]

    # La fila del rendimiento es el total, no un factor.
    es_total = sub[columna_factor].astype(str).str.upper().str.startswith('ROE')
    fila_total = sub[es_total]
    factores = sub[~es_total & sub[columna_aporte].notna()]

    if factores.empty:
        raise ValueError(
            f'No hay aportes calculables para {emisor}. La descomposición '
            f'logarítmica exige que todos los factores conserven signo '
            f'positivo en ambos ejercicios.')

    aportes = factores[columna_aporte].to_numpy(dtype=float)
    nombres = factores[columna_factor].tolist()
    total = float(np.sum(aportes))

    figura, eje = plt.subplots(figsize=(ANCHO, ALTO + 0.3))

    base = np.concatenate([[0.0], np.cumsum(aportes)[:-1]])
    colores = [VERDE if a >= 0 else ROJO for a in aportes]
    eje.bar(np.arange(len(aportes)), aportes, bottom=base, width=0.62,
            color=colores, alpha=0.88, edgecolor='white', linewidth=1.0,
            zorder=2)

    # Trazos de enlace entre el cierre de una barra y el arranque de la
    # siguiente: hacen visible que la cascada no deja residuo.
    cierres = base + aportes
    for i in range(len(aportes) - 1):
        eje.plot([i + 0.31, i + 1 - 0.31], [cierres[i], cierres[i]],
                 color=TINTA_SUAVE, linewidth=0.8, linestyle=':', zorder=1)
    eje.plot([len(aportes) - 1 + 0.31, len(aportes) - 0.31],
             [cierres[-1], cierres[-1]], color=TINTA_SUAVE,
             linewidth=0.8, linestyle=':', zorder=1)

    # La barra de cierre arranca del eje cero: es el total, no un tramo.
    eje.bar([len(aportes)], [total], width=0.62, color=COLORES[0],
            alpha=0.9, edgecolor='white', linewidth=1.0, zorder=2)

    for i, (a, b) in enumerate(zip(aportes, base)):
        altura = b + a
        eje.annotate(f'{a:+.1f}%', xy=(i, altura),
                     xytext=(0, 5 if a >= 0 else -12),
                     textcoords='offset points', ha='center', fontsize=7.5,
                     color=TINTA)
    eje.annotate(f'{total:.1f}%', xy=(len(aportes), total), xytext=(0, 5),
                 textcoords='offset points', ha='center', fontsize=8,
                 fontweight='bold', color=TINTA)

    eje.axhline(0, color=TINTA, linewidth=1.0, zorder=3)

    # Margen superior e inferior para las etiquetas de valor. Sin él, la
    # barra más alta llega al borde del eje y su rótulo se monta sobre el
    # título.
    tope = max(float(np.max(cierres)), float(np.max(base)), total, 0.0)
    piso = min(float(np.min(cierres)), float(np.min(base)), total, 0.0)
    holgura = max(tope - piso, 1.0) * 0.12
    eje.set_ylim(piso - holgura, tope + holgura)

    eje.set_xticks(np.arange(len(aportes) + 1))
    eje.set_xticklabels(nombres + ['Total'], rotation=18, ha='right',
                        fontsize=8)
    eje.set_ylabel('Aporte a la variación del ROE (%)')
    eje.grid(axis='x', visible=False)

    # El encabezado declara la variación efectiva del rendimiento, sin la
    # cual los porcentajes de aporte carecen de referente.
    subtitulo = ''
    if not fila_total.empty and len(columnas_valor) == 2:
        inicial = float(fila_total[columnas_valor[0]].squeeze())
        final = float(fila_total[columnas_valor[1]].squeeze())
        etiqueta_i = columnas_valor[0].split()[-1]
        etiqueta_f = columnas_valor[1].split()[-1]
        subtitulo = (f'El ROE pasó de {inicial:.2%} en {etiqueta_i} '
                     f'a {final:.2%} en {etiqueta_f}')

    eje.set_title(f'Aporte de cada factor a la variación del ROE — {emisor}')
    if subtitulo:
        eje.annotate(subtitulo, xy=(0.5, 1.015), xycoords='axes fraction',
                     ha='center', va='bottom', fontsize=8,
                     color=TINTA_SUAVE)
        eje.set_title(f'Aporte de cada factor a la variación del ROE — {emisor}',
                      pad=22)

    figura.tight_layout()

    seguro = ''.join(c if c.isalnum() else '_' for c in emisor).strip('_')
    return _guardar(figura, f'06_dupont_contribucion_{seguro}', dir_salida)


# ── 5. Sensibilidad ──────────────────────────────────────────────

def sensibilidad_eva(df, dir_salida=DIR_FIGURAS, valores=None):
    """
    Valor económico agregado promedio en función del costo de capital.

    El objeto de la figura es el cruce del eje cero, que marca el umbral
    a partir del cual cada emisor pasa de crear a destruir valor. La
    lectura relevante no es el valor puntual del indicador sino la
    distancia que separa a cada emisor de ese umbral, y esa distancia es
    lo que la figura hace visible.

    Es la representación de la limitación que el trabajo declara: los
    parámetros del modelo de costo de capital son estimaciones, y mostrar
    el umbral acota la conclusión en lugar de afirmarla sin reservas.
    """
    _estilo()
    valores = valores if valores is not None else np.arange(0.06, 0.161, 0.005)
    tabla = mod_eva.sensibilidad(df, 'wacc', valores)
    emisores = _emisores(df)

    figura, eje = plt.subplots(figsize=(ANCHO, ALTO))
    eje.axhspan(0, 1, transform=eje.get_xaxis_transform(),
                color=VERDE, alpha=0.05, zorder=0)

    umbrales_hallados = []

    for i, emisor in enumerate(emisores):
        sub = tabla[tabla['empresa'] == emisor].sort_values('wacc')
        # Un marcador cada cuatro puntos: con veintiún valores por serie,
        # marcarlos todos convierte la línea en una hilera de símbolos.
        eje.plot(sub['wacc'], sub['EVA promedio'],
                 color=COLORES[i % len(COLORES)],
                 linestyle=TRAZOS[i % len(TRAZOS)],
                 marker=MARCADORES[i % len(MARCADORES)], markevery=4,
                 markersize=4.5, linewidth=1.8, label=emisor, zorder=3)

        # Umbral por interpolación lineal entre los dos valores que
        # rodean el cambio de signo.
        x = sub['wacc'].to_numpy(dtype=float)
        y = sub['EVA promedio'].to_numpy(dtype=float)
        cruces = np.where(np.diff(np.sign(y)) != 0)[0]
        if len(cruces):
            k = cruces[0]
            umbral = x[k] + (0 - y[k]) * (x[k + 1] - x[k]) / (y[k + 1] - y[k])
            umbrales_hallados.append((umbral, i))
            eje.plot([umbral], [0], marker='o', markersize=7,
                     markerfacecolor='white', markeredgewidth=1.6,
                     markeredgecolor=COLORES[i % len(COLORES)], zorder=4)

    # Las etiquetas de umbral se colocan en una segunda pasada, escalonadas
    # en altura cuando dos emisores cruzan el eje a distancia menor que la
    # que ocupa el propio rótulo. Dos etiquetas superpuestas no se leen, y
    # el umbral es justamente la cifra que la figura existe para mostrar.
    separacion = (eje.get_xlim()[1] - eje.get_xlim()[0]) * 0.055
    nivel, anterior = 0, None
    for umbral, i in sorted(umbrales_hallados):
        if anterior is not None and umbral - anterior < separacion:
            nivel += 1
        else:
            nivel = 0
        eje.annotate(f'{umbral:.2%}', xy=(umbral, 0),
                     xytext=(0, -14 - 11 * nivel),
                     textcoords='offset points', ha='center', fontsize=7,
                     color=COLORES[i % len(COLORES)], fontweight='bold')
        anterior = umbral

    eje.axhline(0, color=TINTA, linewidth=1.1, zorder=2)
    eje.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
    eje.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:,.0f}'))
    eje.set_xlabel('Costo promedio ponderado de capital supuesto')
    eje.set_ylabel('EVA promedio del período')
    eje.set_title('Sensibilidad del valor económico agregado al costo de capital')
    # En la esquina inferior izquierda, que es la única región que las
    # curvas descendentes dejan libre en todos los casos.
    eje.annotate('Por encima del eje cero el emisor crea valor',
                 xy=(0.015, 0.03), xycoords='axes fraction',
                 fontsize=7, style='italic', color=TINTA_SUAVE)
    eje.legend(loc='upper right', ncols=1)
    figura.tight_layout()
    return _guardar(figura, '07_sensibilidad_eva', dir_salida)


# ── 6. Estructura del activo ─────────────────────────────────────

def vertical_activo(df, dir_salida=DIR_FIGURAS, partidas=None):
    """
    Composición del activo por emisor y ejercicio.

    Los segmentos se apilan porque son partes de un todo que suman cien
    por ciento del activo total, que es precisamente lo que el análisis
    vertical establece. Cada partida lleva trama propia para que la
    composición se distinga también en escala de grises.
    """
    _estilo()
    tabla = mod_vertical.vertical_balance(df)
    partidas = partidas or ['efectivo_equivalentes', 'cuentas_por_cobrar',
                            'inventarios', 'propiedad_planta_equipo_neto']
    partidas = [p for p in partidas if p in tabla.columns]

    nombres = {'efectivo_equivalentes': 'Efectivo',
               'cuentas_por_cobrar': 'Cuentas por cobrar',
               'inventarios': 'Inventarios',
               'propiedad_planta_equipo_neto': 'Propiedad, planta y equipo',
               'activos_intangibles': 'Intangibles',
               'otros_activos_corrientes': 'Otros corrientes',
               'otros_activos_no_corrientes': 'Otros no corrientes'}

    emisores = _emisores(df)
    figura, ejes = _paneles(len(emisores), alto_panel=2.0)

    for eje, emisor in zip(ejes, emisores):
        sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
        x = np.arange(len(sub))
        acumulado = np.zeros(len(sub))

        for k, partida in enumerate(partidas):
            valores = sub[partida].to_numpy(dtype=float)
            eje.bar(x, valores, width=0.62, bottom=acumulado,
                    color=COLORES[k % len(COLORES)], alpha=0.9,
                    edgecolor='white', linewidth=1.2,
                    hatch=TRAMAS[k % len(TRAMAS)],
                    label=nombres.get(partida, partida))
            acumulado += valores

        resto = 100 - acumulado
        eje.bar(x, resto, width=0.62, bottom=acumulado, color=REJILLA,
                edgecolor='white', linewidth=1.2, label='Resto del activo')

        eje.set_title(emisor, fontsize=9)
        eje.set_xticks(x)
        eje.set_xticklabels([str(a) for a in sub['anio']], fontsize=7)
        eje.set_ylim(0, 100)
        eje.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
        eje.grid(axis='x', visible=False)

    manejos, etiquetas = ejes[0].get_legend_handles_labels()
    figura.legend(manejos, etiquetas, loc='lower center',
                  ncols=min(3, len(etiquetas)), fontsize=7.5,
                  bbox_to_anchor=(0.5, -0.12))
    figura.suptitle('Composición del activo total — análisis vertical',
                    fontsize=10, fontweight='bold', y=1.0)
    figura.tight_layout()
    return _guardar(figura, '08_vertical_activo', dir_salida)


# ── Generación completa ──────────────────────────────────────────

def generar_todos(df, dir_salida=DIR_FIGURAS, por_emisor=True, **sustitutos):
    """
    Produce el conjunto completo de figuras y devuelve las rutas escritas.

    Si una figura falla no se interrumpe el resto: se registra el motivo y
    se continúa. Es preferible obtener siete figuras y un aviso a no
    obtener ninguna, sobre todo cuando la causa suele ser un dato ausente
    en un emisor concreto y no un error del código.
    """
    rutas = []
    fallos = []

    tareas = [
        ('Altman', lambda: altman(df, dir_salida)),
        ('ROIC vs WACC', lambda: roic_wacc(df, dir_salida, **sustitutos)),
        ('EVA', lambda: eva(df, dir_salida, **sustitutos)),
        ('Composición del WACC',
         lambda: composicion_wacc(df, dir_salida, **sustitutos)),
        ('DuPont nivel 2', lambda: dupont_factores(df, dir_salida, nivel=2)),
        ('DuPont nivel 3', lambda: dupont_factores(df, dir_salida, nivel=3)),
        ('Sensibilidad del EVA', lambda: sensibilidad_eva(df, dir_salida)),
        ('Composición del activo', lambda: vertical_activo(df, dir_salida)),
    ]

    if por_emisor:
        for emisor in _emisores(df):
            tareas.append((
                f'Contribución DuPont — {emisor}',
                lambda e=emisor: dupont_contribucion(df, e, dir_salida)))

    for nombre, tarea in tareas:
        try:
            ruta = tarea()
            rutas.append(ruta)
            print(f'  [ok]    {nombre}')
        except Exception as error:                       # noqa: BLE001
            fallos.append((nombre, error))
            print(f'  [falla] {nombre}: {type(error).__name__}: {error}')

    print()
    print(f'{len(rutas)} figuras escritas en {Path(dir_salida)}')
    if fallos:
        print(f'{len(fallos)} no se pudieron generar.')
    return rutas


if __name__ == '__main__':
    from src.data_loader import cargar_datos
    from src.parametros import incorporar

    print(f'\nGenerando figuras en {DIR_FIGURAS}\n')
    datos = incorporar(cargar_datos(
        RAIZ / 'data' / 'processed' / 'emisores_consolidado.csv'))
    generar_todos(datos)