"""
Punto de entrada del panel interactivo.

Streamlit espera por convención un archivo en la raíz del proyecto, lo
que permite abrir el panel con una instrucción breve:

    streamlit run app.py

El panel reside en src/visualization/dashboard.py, junto a las figuras
que emplea. Este archivo no lo duplica: importa su función principal y
la invoca.

La invocación explícita es necesaria y no un adorno. Streamlit vuelve a
ejecutar este archivo ante cada interacción del usuario, mientras que
Python conserva en caché los módulos ya importados: un archivo que se
limitara a importar el panel lo dibujaría la primera vez y dejaría la
página en blanco a partir de la segunda.
"""

from src.visualization.dashboard import main

main()