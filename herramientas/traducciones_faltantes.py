"""
Lista las cadenas marcadas para traducir que no tienen traducción.

Una traducción se degrada en silencio: una cadena sin registrar aparece
en español dentro de una página en inglés, y nadie lo advierte hasta que
alguien mira la pantalla. Esta comprobación la hace visible.

    python -m herramientas.traducciones_faltantes

Detecta las llamadas t('...') con texto literal. No alcanza las de la
forma t(variable) —los rótulos que provienen de un diccionario, por
ejemplo—, de modo que una salida vacía es condición necesaria y no
suficiente.
"""

import ast
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src import idioma                                       # noqa: E402

MODULOS = ['src/visualization/charts.py', 'src/visualization/dashboard.py']


def faltantes(idiomas=None):
    """Devuelve {idioma: {cadena: [ubicaciones]}} de lo no traducido."""
    idiomas = idiomas or [c for c in idioma.IDIOMAS if c != idioma.POR_OMISION]
    resultado = {c: {} for c in idiomas}

    for ruta in MODULOS:
        completa = RAIZ / ruta
        if not completa.exists():
            continue
        arbol = ast.parse(completa.read_text(encoding='utf-8'))
        for nodo in ast.walk(arbol):
            if not (isinstance(nodo, ast.Call)
                    and getattr(nodo.func, 'id', '') == 't'):
                continue
            for arg in nodo.args:
                if not (isinstance(arg, ast.Constant)
                        and isinstance(arg.value, str)):
                    continue
                for codigo in idiomas:
                    if arg.value not in idioma.TRADUCCIONES.get(codigo, {}):
                        resultado[codigo].setdefault(arg.value, []).append(
                            f'{completa.name}:{arg.lineno}')
    return resultado


def main():
    """Imprime el informe y devuelve 1 si falta alguna traducción."""
    informe = faltantes()
    pendientes = 0

    for codigo, cadenas in informe.items():
        nombre = idioma.IDIOMAS[codigo]
        if not cadenas:
            print(f'{nombre}: todas las cadenas están traducidas.')
            continue
        pendientes += len(cadenas)
        print(f'{nombre}: {len(cadenas)} cadenas sin traducir\n')
        for texto in sorted(cadenas, key=len):
            corto = ' '.join(texto.split())
            if len(corto) > 90:
                corto = corto[:87] + '...'
            print(f'  [{cadenas[texto][0]:22s}] {corto}')
        print()

    return 1 if pendientes else 0


if __name__ == '__main__':
    raise SystemExit(main())