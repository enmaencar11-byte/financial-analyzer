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

from src.idioma import t
from src.analysis import altman as mod_altman
from src.analysis import dupont as mod_dupont
from src.analysis import eva as mod_eva
from src.analysis import horizontal as mod_horizontal
from src.analysis import vertical as mod_vertical
from src.analysis import wacc as mod_wacc
from src import ratios as mod_ratios

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


# Orden canónico de los emisores. Determina qué color, trazo y marcador
# corresponde a cada uno, con independencia de cuáles se estén mostrando.
_UNIVERSO = []


def fijar_universo(emisores):
    """
    Registra el orden canónico de los emisores de la muestra completa.

    El color debe seguir a la entidad y no a su posición en la tabla que
    se está dibujando. Sin este registro, al filtrar un emisor el
    siguiente ocuparía el primer puesto y cambiaría de color: el lector
    que venía siguiendo una línea naranja la vería azul sin que nada en
    los datos hubiera cambiado.

    Se invoca una vez con la muestra completa, antes de dibujar cualquier
    subconjunto. Un emisor no registrado recibe el siguiente puesto libre
    y lo conserva mientras dure la ejecución.
    """
    global _UNIVERSO
    _UNIVERSO = list(dict.fromkeys(emisores))
    return _UNIVERSO


def _puesto(emisor):
    """Puesto canónico de un emisor, registrándolo si no lo estaba."""
    if emisor not in _UNIVERSO:
        _UNIVERSO.append(emisor)
    return _UNIVERSO.index(emisor)


def _estilo_serie(emisor):
    """
    Color, trazo y marcador que identifican a un emisor.

    Los tres se devuelven juntos porque los tres son codificación de la
    misma identidad: el color para la pantalla, el trazo y el marcador
    para la impresión en escala de grises.
    """
    i = _puesto(emisor)
    return (COLORES[i % len(COLORES)],
            TRAZOS[i % len(TRAZOS)],
            MARCADORES[i % len(MARCADORES)])


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
    """
    Escribe la figura y la cierra, para no acumular memoria.

    Cuando no se indica carpeta de salida, devuelve la figura sin
    escribirla ni cerrarla. Esa variante es la que emplea el panel
    interactivo, que necesita el objeto en memoria y no un archivo.

    De este modo las ocho funciones de figura sirven a los dos destinos
    sin duplicarse: el reporte las escribe y el panel las muestra. Un
    panel con su propio código de dibujo acabaría divergiendo del
    reporte, y entonces no habría manera de saber cuál de los dos
    representa el resultado.
    """
    if dir_salida is None:
        return figura
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

    for emisor in _emisores(df):
        sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
        color, trazo, marcador = _estilo_serie(emisor)
        eje.plot(sub['anio'], sub["Z''"], color=color, linestyle=trazo,
                 marker=marcador, markersize=5, linewidth=2, label=emisor,
                 zorder=3)

    eje.set_xticks(anios)
    eje.set_xlabel(t('Ejercicio'))
    eje.set_ylabel(t("Puntaje Z''"))
    eje.set_title(t("Riesgo de insolvencia — Altman Z'' de cuatro variables"))
    eje.set_ylim(min(0, tabla["Z''"].min() * 1.2),
                 max(superior * 1.2, tabla["Z''"].max() * 1.12))

    # Etiquetas de zona dentro de la propia banda: el lector no debe
    # cotejar la leyenda para saber qué significa cada franja.
    limite = eje.get_xlim()
    for texto, altura, color in (
            (t('Zona segura'), superior, VERDE),
            (t('Zona gris'), (inferior + superior) / 2, AMBAR),
            (t('Zona de peligro'), inferior / 2, ROJO)):
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
                 markersize=4, label=t('ROIC'))
        eje.plot(x, wacc_, color=TINTA_SUAVE, linewidth=2, linestyle='--',
                 marker='s', markersize=4, label=t('WACC'))

        eje.set_title(emisor, fontsize=9)
        eje.set_xticks(anios)
        eje.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f'{v:.0%}'))

    # La leyenda va al pie de la figura y no dentro de un panel: con un
    # área sombreada que ocupa el centro del gráfico, cualquier posición
    # interior se superpone a los datos.
    manejos = [Line2D([], [], color=COLORES[0], linewidth=2, marker='o',
                      markersize=4, label=t('ROIC')),
               Line2D([], [], color=TINTA_SUAVE, linewidth=2, linestyle='--',
                      marker='s', markersize=4, label=t('WACC')),
               Patch(facecolor=VERDE, alpha=0.22, label=t('Crea valor')),
               Patch(facecolor=ROJO, alpha=0.22, label=t('Destruye valor'))]
    figura.suptitle(t('Retorno sobre el capital invertido frente a su costo'),
                    fontsize=10, fontweight='bold', y=1.0)
    figura.supxlabel(t('Ejercicio'), fontsize=9)
    figura.supylabel(t('Tasa anual'), fontsize=9)
    figura.tight_layout()

    # La leyenda se coloca DESPUÉS de tight_layout y por debajo del
    # rótulo del eje. Situada antes, tight_layout no reserva espacio para
    # ella y el rótulo del eje queda impreso encima.
    figura.legend(handles=manejos, loc='lower center', ncols=4, fontsize=7.5,
                  bbox_to_anchor=(0.5, -0.09))
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
    marcas_anio, etiquetas_anio = [], []

    for j, anio in enumerate(anios):
        valores = [
            float(tabla.loc[(tabla['empresa'] == e) & (tabla['anio'] == anio),
                            'EVA'].squeeze() or 0)
            for e in emisores]
        x = posiciones - 0.4 + ancho_barra * (j + 0.5)
        colores = [VERDE if v >= 0 else ROJO for v in valores]
        # Sin trama: el ejercicio va rotulado bajo cada barra, de modo
        # que la identidad no depende del color y una trama adicional
        # solo agregaría ruido visual.
        eje.bar(x, valores, width=ancho_barra * 0.88, color=colores,
                alpha=0.9, edgecolor='white', linewidth=0.8, zorder=2)
        marcas_anio.extend(x)
        etiquetas_anio.extend([str(anio)] * len(x))

    eje.axhline(0, color=TINTA, linewidth=1.1, zorder=3)

    # Los ejercicios van como marcas secundarias del eje y no como
    # rótulos flotantes sobre la línea de cero. Un rótulo situado en cero
    # queda en la parte alta del gráfico cuando la mayoría de los valores
    # es negativa, que es justo donde la leyenda necesita espacio.
    eje.set_xticks(marcas_anio, minor=True)
    eje.set_xticklabels(etiquetas_anio, minor=True, fontsize=6,
                        color=TINTA_SUAVE)
    eje.set_xticks(posiciones)
    eje.set_xticklabels([_partir(e) for e in emisores], fontsize=8)
    eje.tick_params(axis='x', which='major', length=0, pad=16)
    eje.tick_params(axis='x', which='minor', length=2)

    eje.set_ylabel(t('EVA (unidades monetarias)'))
    eje.set_title(t('Valor económico agregado por emisor y ejercicio'))
    eje.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:,.0f}'))
    eje.grid(axis='x', visible=False, which='both')

    # La leyenda va al pie: dentro del área de trazado se superpondría a
    # las barras, cuya orientación depende del signo y no puede preverse.
    figura.legend(handles=[Patch(facecolor=VERDE, alpha=0.9, label=t('Crea valor')),
                           Patch(facecolor=ROJO, alpha=0.9, label=t('Destruye valor'))],
                  loc='lower center', ncols=2, fontsize=8,
                  bbox_to_anchor=(0.5, -0.04))
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
                edgecolor='white', linewidth=1.2, label=t('Patrimonio'))
        eje.bar(x, deuda, width=0.62, bottom=patrimonio, color=COLORES[1],
                alpha=0.9, edgecolor='white', linewidth=1.2,
                hatch='///', label=t('Deuda'))

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
    figura.suptitle(t('Composición del costo promedio ponderado de capital'),
                    fontsize=10, fontweight='bold', y=1.0)
    figura.tight_layout()
    return _guardar(figura, '04_composicion_wacc', dir_salida)


# ── 3b. Catálogo de indicadores ──────────────────────────────────

def indicadores(df, categoria, dir_salida=DIR_FIGURAS):
    """
    Evolución de los indicadores de una categoría, un panel por indicador.

    Las cuatro categorías se representan por separado y no en una sola
    figura. Treinta y tres paneles en una página no se leen, y la
    categoría es además la unidad con que el análisis financiero los
    interpreta: la liquidez y la rentabilidad responden preguntas
    distintas y se comentan en apartados distintos.

    Cada panel lleva su propia escala vertical, porque los indicadores de
    una misma categoría difieren en orden de magnitud: una razón
    corriente se mueve alrededor de la unidad y un capital de trabajo
    neto en millones. Compartir escala aplastaría los primeros contra el
    eje.

    Los indicadores que no varían en el período se presentan como una
    línea plana y no como una ampliación del error de representación en
    punto flotante, conforme al criterio de _escala_factor.
    """
    if categoria not in mod_ratios.CATEGORIAS:
        raise ValueError(f'Categoría desconocida: {categoria}. '
                         f'Opciones: {", ".join(mod_ratios.CATEGORIAS)}')

    tabla = mod_ratios.calcular_todos(df, categoria=categoria)
    nombres = [c for c in tabla.columns if c not in IDENTIFICADORES]
    emisores = _emisores(df)
    anios = _anios(df)

    _estilo()
    figura, ejes = _paneles(len(nombres), alto_panel=1.9,
                            columnas=min(3, len(nombres)))

    for eje, nombre in zip(ejes, nombres):
        for emisor in emisores:
            sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
            color, trazo, marcador = _estilo_serie(emisor)
            eje.plot(sub['anio'], sub[nombre], color=color, linestyle=trazo,
                     marker=marcador, markersize=4, linewidth=1.6,
                     label=emisor)

        _escala_factor(eje, tabla[nombre])
        eje.set_title(t(nombre), fontsize=8)
        eje.set_xticks(anios)
        eje.tick_params(labelsize=7)

    manejos = [Line2D([], [], color=_estilo_serie(e)[0],
                      linestyle=_estilo_serie(e)[1],
                      marker=_estilo_serie(e)[2],
                      markersize=4, linewidth=1.6, label=e)
               for e in emisores]
    figura.legend(handles=manejos, loc='lower center',
                  ncols=min(3, len(emisores)), fontsize=7.5,
                  bbox_to_anchor=(0.5, -0.09))
    figura.suptitle(t('Indicadores de {cat} — evolución {a}–{b}').format(
                        cat=t(categoria.lower()), a=anios[0], b=anios[-1]),
                    fontsize=10, fontweight='bold', y=1.0)
    figura.tight_layout()

    seguro = categoria.lower().replace(' ', '_')
    return _guardar(figura, f'09_indicadores_{seguro}', dir_salida)


# ── 4. Descomposición del rendimiento ────────────────────────────

# Por debajo de esta proporción respecto de su propia magnitud, la
# variación de un factor se considera nula y no una tendencia.
TOLERANCIA_CONSTANTE = 1e-3


def _escala_factor(eje, valores):
    """
    Fija la escala vertical de un factor y suprime la notación de
    desplazamiento del eje.

    Dos correcciones, ambas de fondo y no de apariencia.

    La primera. Matplotlib ajusta el eje al intervalo de los datos. Si un
    factor permanece constante a lo largo del período, ese intervalo se
    reduce al error de representación en punto flotante, del orden de
    1e-17, y la figura presenta como tendencia lo que es ruido
    aritmético. Un lector concluiría que el factor subió y bajó cuando no
    se movió. Cuando la variación resulta despreciable frente a la propia
    magnitud del factor, se impone una banda alrededor de su valor, con
    lo que la línea se lee plana, que es lo que efectivamente ocurrió.

    La segunda. Para intervalos estrechos, Matplotlib rotula el eje con
    un desplazamiento del tipo '1e-8+1.1e-1' que se sitúa sobre el título
    del panel. Suprimirlo obliga a rotular los valores completos, que es
    además lo que corresponde en un documento impreso.
    """
    numeros = pd.to_numeric(valores, errors='coerce').dropna()
    if numeros.empty:
        return

    minimo, maximo = float(numeros.min()), float(numeros.max())
    centro = (minimo + maximo) / 2
    escala = max(abs(centro), 1e-12)

    if (maximo - minimo) < escala * TOLERANCIA_CONSTANTE:
        margen = max(abs(centro) * 0.08, 1e-6)
        eje.set_ylim(centro - margen, centro + margen)

    try:
        eje.ticklabel_format(axis='y', style='plain', useOffset=False)
    except AttributeError:
        pass


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
        for emisor in emisores:
            sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
            color, trazo, marcador = _estilo_serie(emisor)
            eje.plot(sub['anio'], sub[factor], color=color, linestyle=trazo,
                     marker=marcador, markersize=4, linewidth=1.6,
                     label=emisor)

        _escala_factor(eje, tabla[factor])
        eje.set_title(t(factor), fontsize=8.5)
        eje.set_xticks(anios)
        eje.tick_params(labelsize=7)

    ejes[-1].set_title(t('ROE (producto de los factores)'), fontsize=8.5)

    manejos = [Line2D([], [], color=_estilo_serie(e)[0],
                      linestyle=_estilo_serie(e)[1],
                      marker=_estilo_serie(e)[2],
                      markersize=4, linewidth=1.6, label=e)
               for e in emisores]
    figura.legend(handles=manejos, loc='lower center',
                  ncols=min(3, len(emisores)), fontsize=7.5,
                  bbox_to_anchor=(0.5, -0.11))
    figura.suptitle(t('Descomposición DuPont de nivel {n} — evolución por factor').format(n=nivel),
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
    eje.set_xticklabels([t(n) for n in nombres] + [t('Total')],
                        rotation=18, ha='right',
                        fontsize=8)
    eje.set_ylabel(t('Aporte a la variación del ROE (%)'))
    eje.grid(axis='x', visible=False)

    # El encabezado declara la variación efectiva del rendimiento, sin la
    # cual los porcentajes de aporte carecen de referente.
    subtitulo = ''
    if not fila_total.empty and len(columnas_valor) == 2:
        inicial = float(fila_total[columnas_valor[0]].squeeze())
        final = float(fila_total[columnas_valor[1]].squeeze())
        etiqueta_i = columnas_valor[0].split()[-1]
        etiqueta_f = columnas_valor[1].split()[-1]
        subtitulo = (t('El ROE pasó de {i} en {ai} a {f} en {af}').format(
            i=f'{inicial:.2%}', ai=etiqueta_i, f=f'{final:.2%}', af=etiqueta_f))

    eje.set_title(t('Aporte de cada factor a la variación del ROE — {e}').format(e=emisor))
    if subtitulo:
        eje.annotate(subtitulo, xy=(0.5, 1.015), xycoords='axes fraction',
                     ha='center', va='bottom', fontsize=8,
                     color=TINTA_SUAVE)
        eje.set_title(t('Aporte de cada factor a la variación del ROE — {e}').format(e=emisor),
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

    for emisor in emisores:
        sub = tabla[tabla['empresa'] == emisor].sort_values('wacc')
        color, trazo, marcador = _estilo_serie(emisor)
        # Un marcador cada cuatro puntos: con veintiún valores por serie,
        # marcarlos todos convierte la línea en una hilera de símbolos.
        eje.plot(sub['wacc'], sub['EVA promedio'], color=color,
                 linestyle=trazo, marker=marcador, markevery=4,
                 markersize=4.5, linewidth=1.8, label=emisor, zorder=3)

        # Umbral por interpolación lineal entre los dos valores que
        # rodean el cambio de signo.
        x = sub['wacc'].to_numpy(dtype=float)
        y = sub['EVA promedio'].to_numpy(dtype=float)
        cruces = np.where(np.diff(np.sign(y)) != 0)[0]
        if len(cruces):
            k = cruces[0]
            umbral = x[k] + (0 - y[k]) * (x[k + 1] - x[k]) / (y[k + 1] - y[k])
            umbrales_hallados.append((umbral, emisor))
            eje.plot([umbral], [0], marker='o', markersize=7,
                     markerfacecolor='white', markeredgewidth=1.6,
                     markeredgecolor=color, zorder=4)

    # Las etiquetas de umbral se colocan en una segunda pasada, escalonadas
    # en altura cuando dos emisores cruzan el eje a distancia menor que la
    # que ocupa el propio rótulo. Dos etiquetas superpuestas no se leen, y
    # el umbral es justamente la cifra que la figura existe para mostrar.
    separacion = (eje.get_xlim()[1] - eje.get_xlim()[0]) * 0.055
    nivel, anterior = 0, None
    for umbral, emisor in sorted(umbrales_hallados, key=lambda par: par[0]):
        if anterior is not None and umbral - anterior < separacion:
            nivel += 1
        else:
            nivel = 0
        eje.annotate(f'{umbral:.2%}', xy=(umbral, 0),
                     xytext=(0, -14 - 11 * nivel),
                     textcoords='offset points', ha='center', fontsize=7,
                     color=_estilo_serie(emisor)[0], fontweight='bold')
        anterior = umbral

    eje.axhline(0, color=TINTA, linewidth=1.1, zorder=2)
    eje.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
    eje.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:,.0f}'))
    eje.set_xlabel(t('Costo promedio ponderado de capital supuesto'))
    eje.set_ylabel(t('EVA promedio del período'))
    eje.set_title(t('Sensibilidad del valor económico agregado al costo de capital'))
    # En la esquina inferior izquierda, que es la única región que las
    # curvas descendentes dejan libre en todos los casos.
    eje.annotate(t('Por encima del eje cero el emisor crea valor'),
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
                    label=t(nombres.get(partida, partida)))
            acumulado += valores

        resto = 100 - acumulado
        eje.bar(x, resto, width=0.62, bottom=acumulado, color=REJILLA,
                edgecolor='white', linewidth=1.2, label=t('Resto del activo'))

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
    figura.suptitle(t('Composición del activo total — análisis vertical'),
                    fontsize=10, fontweight='bold', y=1.0)
    figura.tight_layout()
    return _guardar(figura, '08_vertical_activo', dir_salida)


def vertical_resultados(df, dir_salida=DIR_FIGURAS):
    """
    Estructura del estado de resultados, como porcentaje de las ventas.

    Los segmentos se apilan porque son partes de un todo: el costo de
    ventas, los gastos operativos, el costo financiero, el impuesto y la
    utilidad neta agotan la venta de cada ejercicio. Es lo que el
    análisis vertical establece al tomar las ventas como base.

    La figura responde una pregunta que los indicadores de rentabilidad
    no responden. El margen neto dice cuánto queda de cada peso vendido;
    esta dice adónde se fue el resto, que es lo que permite actuar: un
    margen que cae porque subió el costo de ventas exige una respuesta
    distinta de uno que cae porque subió el gasto financiero.
    """
    _estilo()
    tabla = mod_vertical.vertical_resultados(df)

    # Cada tramo se obtiene por diferencia respecto del anterior, de modo
    # que la suma reproduzca el cien por ciento de las ventas sin
    # solapamientos. La utilidad bruta, por ejemplo, ya contiene a la
    # operativa, y apilarlas juntas contaría dos veces lo mismo.
    tramos = [
        ('Costo de ventas', lambda r: r['costo_ventas']),
        ('Gastos operativos', lambda r: r['total_gastos_operativos']),
        ('Costo financiero neto',
         lambda r: r['utilidad_operativa'] - r['utilidad_antes_impuestos']),
        ('Impuesto sobre la renta', lambda r: r['impuesto_renta']),
        ('Utilidad neta', lambda r: r['utilidad_neta']),
    ]

    emisores = _emisores(df)
    figura, ejes = _paneles(len(emisores), alto_panel=2.1)

    for eje, emisor in zip(ejes, emisores):
        sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
        x = np.arange(len(sub))
        acumulado = np.zeros(len(sub))

        for k, (etiqueta, formula) in enumerate(tramos):
            valores = formula(sub).to_numpy(dtype=float)
            eje.bar(x, valores, width=0.62, bottom=acumulado,
                    color=COLORES[k % len(COLORES)], alpha=0.9,
                    edgecolor='white', linewidth=1.2,
                    hatch=TRAMAS[k % len(TRAMAS)], label=t(etiqueta))
            acumulado += valores

        # La utilidad neta se rotula por ser la cifra que el lector busca.
        for xi, valor in zip(x, tramos[-1][1](sub).to_numpy(dtype=float)):
            eje.annotate(f'{valor:.1f}%', xy=(xi, acumulado[int(xi)]),
                         xytext=(0, 3), textcoords='offset points',
                         ha='center', fontsize=7, color=TINTA)

        eje.set_title(emisor, fontsize=9)
        eje.set_xticks(x)
        eje.set_xticklabels([str(a) for a in sub['anio']], fontsize=7)
        eje.set_ylim(0, max(float(acumulado.max()) * 1.12, 100))
        eje.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))
        eje.grid(axis='x', visible=False)

    manejos, etiquetas = ejes[0].get_legend_handles_labels()
    figura.legend(manejos, etiquetas, loc='lower center', ncols=3,
                  fontsize=7.5, bbox_to_anchor=(0.5, -0.14))
    figura.suptitle(t('Estructura del estado de resultados — análisis vertical'),
                    fontsize=10, fontweight='bold', y=1.0)
    figura.tight_layout()
    return _guardar(figura, '10_vertical_resultados', dir_salida)


def horizontal_indices(df, dir_salida=DIR_FIGURAS, partidas=None,
                       anio_base=None):
    """
    Evolución de las magnitudes principales, con el primer ejercicio
    igual a cien.

    Los números índice permiten comparar en una misma escala partidas de
    magnitudes muy distintas: las ventas y el patrimonio de un emisor
    difieren en orden de magnitud, pero sus índices se leen juntos y
    revelan cuál creció más deprisa.

    Esa comparación es el objeto del análisis horizontal. Que las ventas
    crezcan veinte por ciento no dice nada por sí solo; que crezcan
    veinte mientras la deuda financiera crece sesenta dice bastante.
    """
    _estilo()
    tabla = mod_horizontal.numeros_indice(df[
        [c for c in df.columns
         if c in IDENTIFICADORES or pd.api.types.is_numeric_dtype(df[c])]],
        anio_base=anio_base)

    partidas = partidas or ['ventas_netas', 'utilidad_operativa',
                            'utilidad_neta', 'activo_total',
                            'patrimonio_total', 'deuda_financiera_total']
    partidas = [p for p in partidas if p in tabla.columns]

    nombres = {'ventas_netas': 'Ventas netas',
               'utilidad_operativa': 'Utilidad operativa',
               'utilidad_neta': 'Utilidad neta',
               'activo_total': 'Activo total',
               'patrimonio_total': 'Patrimonio',
               'deuda_financiera_total': 'Deuda financiera',
               'ebitda': 'EBITDA'}

    emisores = _emisores(df)
    anios = _anios(df)
    figura, ejes = _paneles(len(emisores), alto_panel=2.3)

    for eje, emisor in zip(ejes, emisores):
        sub = tabla[tabla['empresa'] == emisor].sort_values('anio')
        for k, partida in enumerate(partidas):
            eje.plot(sub['anio'], sub[partida], color=COLORES[k % len(COLORES)],
                     linestyle=TRAZOS[k % len(TRAZOS)],
                     marker=MARCADORES[k % len(MARCADORES)], markersize=4,
                     linewidth=1.6, label=t(nombres.get(partida, partida)))

        # La referencia: por encima de cien la partida creció.
        eje.axhline(100, color=TINTA_SUAVE, linewidth=0.9, linestyle='--',
                    zorder=1)
        eje.set_title(emisor, fontsize=9)
        eje.set_xticks(anios)
        eje.tick_params(labelsize=7)

    manejos, etiquetas = ejes[0].get_legend_handles_labels()
    figura.legend(manejos, etiquetas, loc='lower center', ncols=3,
                  fontsize=7.5, bbox_to_anchor=(0.5, -0.16))
    base = anio_base or anios[0]
    figura.suptitle(t('Evolución de las magnitudes principales — {b} = 100').format(b=base), fontsize=10, fontweight='bold', y=1.0)
    figura.tight_layout()
    return _guardar(figura, '11_horizontal_indices', dir_salida)


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
        ('Estructura de resultados',
         lambda: vertical_resultados(df, dir_salida)),
        ('Números índice', lambda: horizontal_indices(df, dir_salida)),
    ]

    # Una figura por categoría de indicador. El catálogo es la fuente:
    # añadir un indicador a src/ratios lo incorpora aquí sin tocar nada.
    for categoria in mod_ratios.CATEGORIAS:
        tareas.append((f'Indicadores de {categoria.lower()}',
                       lambda c=categoria: indicadores(df, c, dir_salida)))

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
    import argparse

    from src import idioma
    from src.data_loader import cargar_datos
    from src.parametros import incorporar

    argumentos = argparse.ArgumentParser(
        prog='python -m src.visualization.charts',
        description='Genera las figuras del capítulo de resultados.')
    argumentos.add_argument('--idioma', default=idioma.POR_OMISION,
                            choices=list(idioma.IDIOMAS),
                            help='Idioma de los títulos, ejes y leyendas.')
    argumentos.add_argument('--salida', default=str(DIR_FIGURAS),
                            help='Carpeta donde escribir las figuras.')
    opciones = argumentos.parse_args()

    # El idioma se fija antes de dibujar: los rótulos se traducen al
    # construir cada figura y no admiten cambio posterior.
    idioma.fijar(opciones.idioma)

    print(f'\nGenerando figuras en {opciones.salida}\n')
    datos = incorporar(cargar_datos(
        RAIZ / 'data' / 'processed' / 'emisores_consolidado.csv'))
    generar_todos(datos, opciones.salida)