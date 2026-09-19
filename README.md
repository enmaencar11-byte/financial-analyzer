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
conjunto completo de indicadores que un analista calcularía a mano.

**Funcionando**

- Consolidación de plantillas `.xlsx` a un conjunto de datos único
- 33 indicadores: liquidez (6), rentabilidad (9), apalancamiento (9), actividad (9)
- Análisis vertical y horizontal, con números índice y variación interanual
- Soporte para estados individuales y consolidados con participaciones no controladoras
- Verificación automática de consistencia contable

**En desarrollo**

- Análisis DuPont de tres niveles
- Altman Z'' y EM Score para mercados emergentes
- CAPM y WACC con prima de riesgo país (metodología Damodaran)
- EVA (valor económico agregado)
- Tablero interactivo y reporte automatizado en PDF

Avance del sistema: **10 de 16 módulos**.

---

## Verificación

El sistema rechaza datos inconsistentes en lugar de procesarlos en silencio.

| Situación | Comportamiento |
|---|---|
| El balance no cuadra | Se detiene e indica emisor, ejercicio y monto de la diferencia |
| La utilidad neta no coincide con sus porciones atribuibles | Se detiene e indica dónde |
| Un emisor sin inventarios | Devuelve `NaN` en lugar de infinito, sin contaminar los promedios |
| Patrimonio negativo | El ROE se reporta como no significativo |

Estas comprobaciones forman parte del protocolo de validación de la investigación.

---

## Instalación

```bash
git clone https://github.com/enmaencar11-byte/financial-analyzer.git
cd financial-analyzer
pip install -r requirements.txt
```

## Uso

```bash
# Consolidar las plantillas de data/raw/ en un único CSV
python -m src.etl

# Ver los indicadores por categoría
python -c "import pandas as pd; from src.ratios import mostrar; mostrar(pd.read_csv('data/processed/emisores_consolidado.csv'))"
```

---

## Estructura
src/
├── config.py los nombres de las 48 columnas
├── utils.py división segura y utilidades compartidas
├── etl.py lee las plantillas .xlsx y produce el CSV
├── data_loader.py lee el CSV y lo valida
├── ratios/ las 33 razones financieras
├── analysis/ vertical, horizontal y los modelos
├── visualization/ gráficos y tablero
└── reporting/ generación del reporte


Los datos de los emisores no se versionan. Solo la estructura de carpetas.

---

## Tecnologías

Python 3 · pandas · NumPy · openpyxl

Previstas: pytest, matplotlib, Streamlit, ReportLab.

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