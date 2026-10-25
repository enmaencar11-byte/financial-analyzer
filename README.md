# FinAnalyzer Pro

Sistema automatizado de análisis financiero para emisores del mercado de valores dominicano.

Automated financial analysis system for issuers listed on the Dominican securities market (SIMV).

Trabajo Final de Maestría en Finanzas de Costos — PUCMM, 2026.

---

## El problema

Analizar los estados financieros de una empresa toma horas. Hacerlo para cinco
empresas en cuatro años cada una multiplica el trabajo por veinte, y con él la
probabilidad de un error de transcripción que nadie detecte.

La Superintendencia del Mercado de Valores exige a sus emisores publicar estados
financieros auditados bajo NIIF. Esa información es pública, verificada y
homogénea. Lo que falta es una herramienta accesible para procesarla de forma
sistemática.

---

## Qué hace

Toma estados financieros transcritos a una plantilla de Excel y produce el
conjunto completo de indicadores que un analista calcularía a mano, más los
modelos de riesgo y de costo de capital que la práctica profesional emplea.

**Análisis descriptivo**

- Consolidación de plantillas `.xlsx` a un conjunto de datos único
- 33 indicadores: liquidez (6), rentabilidad (9), apalancamiento (9), actividad (9)
- Análisis vertical y horizontal, con números índice y variación interanual
- Soporte para estados individuales y consolidados con participaciones no controladoras

**Modelos cuantitativos**

- Descomposición DuPont de tres niveles, con atribución logarítmica de la
  variación del rendimiento que suma cien por ciento sin residuo
- Altman Z'' y EM Score, en la variante de cuatro variables para empresas sin
  cotización bursátil
- CAPM con prima de riesgo país y reapalancamiento de Hamada, según la
  metodología de Damodaran para mercados emergentes
- WACC y EVA, este último calculado por dos vías independientes que se contrastan
  entre sí

**Salidas**

- Libro de Excel de diecinueve hojas, una por análisis, con una hoja de
  validación y otra que registra los parámetros empleados
- Figuras a trescientos puntos por pulgada, legibles en escala de grises: ocho
  de los modelos, una por categoría de indicador y una de descomposición del
  rendimiento por emisor
- Panel interactivo con los parámetros del modelo gobernados por controles
  deslizantes

**Pendiente**

- Reporte automatizado en PDF por emisor

Avance del sistema: **16 de 17 módulos**.

---

## Parámetros intercambiables

Los parámetros del modelo de costo de capital son estimaciones y no magnitudes
observadas: el coeficiente de riesgo sistemático procede de otro mercado y la
prima de riesgo país de un diferencial soberano que varía a diario.

Todas las funciones admiten valores que sustituyen a los del archivo, tanto por
línea de instrucciones como por los controles del panel. Esto permite mostrar, y
no solo declarar, cuál es el umbral a partir del cual la conclusión sobre
creación de valor se invierte.

El proceso por lotes y el panel invocan las mismas funciones, de modo que la
cifra que el panel muestra es necesariamente la que el reporte produce.

---

## Verificación

El sistema rechaza datos inconsistentes en lugar de procesarlos en silencio.

| Situación | Comportamiento |
|---|---|
| El balance no cuadra | Se detiene e indica emisor, ejercicio y monto de la diferencia |
| La utilidad neta no coincide con sus porciones atribuibles | Se detiene e indica dónde |
| Un emisor sin inventarios | Devuelve `NaN` en lugar de infinito, sin contaminar los promedios |
| Patrimonio negativo | El ROE se reporta como no significativo |
| Falta un parámetro de mercado o sectorial | Se detiene e indica qué emisor o ejercicio |

Además, cada ejecución comprueba siete identidades algebraicas y las registra en
la hoja `Validacion` del libro de resultados: el cuadre del balance, las dos
bases del análisis vertical, la identidad DuPont en sus dos niveles, la
equivalencia de las dos formulaciones del EVA y la cobertura del catálogo de
indicadores.

Son verificaciones de consistencia interna: contrastan el sistema contra sí
mismo y no contra una fuente externa, de modo que detectan incoherencia de
cálculo y no error de origen en los datos. Constituyen el primer nivel del
protocolo de validación de la investigación.

---

## Requisitos

Python 3.10 o posterior.

## Instalación

```bash
git clone https://github.com/enmaencar11-byte/financial-analyzer.git
cd financial-analyzer
python -m pip install -r requirements.txt
```

---

## Uso

Todas las instrucciones se ejecutan desde la raíz del proyecto.

### 1. Preparar los datos

Las plantillas de Excel, una por emisor, van en `data/raw/`. El proceso las
consolida en un único archivo:

```bash
python -m src.etl
```

Los parámetros externos se registran en dos archivos con una sola fuente de
verdad: `data/parametros_mercado.csv`, una fila por ejercicio, y
`data/parametros_sector.csv`, una fila por emisor.

### 2. Ejecutar el análisis

```bash
python -m src.main
```

Produce `outputs/resultados.xlsx` e imprime la tabla de validación.

Los parámetros del modelo pueden sustituirse en la propia instrucción:

```bash
python -m src.main --crp 0.015 --salida outputs/escenario_crp15.xlsx
python -m src.main --wacc 0.09 --salida outputs/escenario_wacc9.xlsx
python -m src.main --rf 0.045 --erp 0.05 --crp 0.03 --beta 0.80
python -m src.main --help
```

Si se sustituyen los cuatro parámetros de mercado, el proceso no consulta el
archivo de parámetros.

### 3. Generar las figuras

```bash
python -m src.visualization.charts
```

Escribe las figuras en `outputs/figuras/`.

### 4. Abrir el panel interactivo

```bash
python -m streamlit run app.py
```

Se abre en el navegador, en esta misma computadora. No queda publicado en
internet ni accesible desde otro equipo. Para cerrarlo, `Ctrl+C` en la terminal.

El panel permite restringir la muestra a los emisores y ejercicios elegidos, y
gobernar cada parámetro del modelo por separado, lo que permite atribuir un
cambio del resultado al parámetro que efectivamente se movió.

---

## Estructura

```
src/
├── config.py          los nombres de las 48 columnas
├── utils.py           división segura y formato de tablas
├── etl.py             lee las plantillas .xlsx y produce el CSV
├── data_loader.py     lee el CSV y lo valida
├── parametros.py      incorpora los parámetros externos al conjunto de datos
├── main.py            orquesta el proceso y escribe el libro de resultados
├── ratios/            las 33 razones financieras
├── analysis/          vertical, horizontal, DuPont, Altman, CAPM, WACC, EVA
├── visualization/     figuras y panel interactivo
└── reporting/         generación del reporte en PDF
```

Los datos de los emisores no se versionan; solo la estructura de carpetas. Los
dos archivos de parámetros sí, por constituir decisiones metodológicas que deben
poder justificarse.

---

## Tecnologías

Python 3 · pandas · NumPy · openpyxl · matplotlib · Streamlit

Previstas: pytest, ReportLab.

---

## La investigación

- **Fuente:** Superintendencia del Mercado de Valores (SIMV)
- **Período:** 2022 – 2025
- **Muestra:** 5 emisores no financieros
- **Marco normativo:** NIIF
- **Validación:** protocolo de tres niveles (exactitud de cálculo, consistencia
  frente a calificadoras de riesgo independientes, y coherencia del diagnóstico)

---

## Autor

**Enmanuel Figuereo Encarnación**
Licenciado en Matemáticas · Maestría en Finanzas de Costos, PUCMM
Santiago de los Caballeros, República Dominicana

enmaencar11@gmail.com ·
[LinkedIn](https://www.linkedin.com/in/enmanuel-figuereo-encarnaci%C3%B3n-22899a419/)