# FinAnalyzer Pro — config.py
# ES: Define en un solo lugar los nombres exactos
#     de todas las columnas que el sistema
#     espera encontrar en el CSV.
# EN: Defines in one place the exact column names
#     that the system expects to find in the CSV.
#
# El orden de esta lista replica el orden de las filas
# de FinAnalyzer_Plantilla_Datos.xlsx. Si se agrega una
# fila a la plantilla, debe agregarse aquí en la misma
# posición relativa.

# ── BALANCE GENERAL / BALANCE SHEET ──────────────────────
COLUMNAS_BALANCE = [
    'empresa',                        # company name
    'anio',                           # year

    # Activos corrientes / Current assets
    'efectivo_equivalentes',          # cash and equivalents
    'cuentas_por_cobrar',             # accounts receivable
    'inventarios',                    # inventories
    'otros_activos_corrientes',       # other current assets
    'activo_corriente_total',         # total current assets

    # Activos no corrientes / Non-current assets
    'propiedad_planta_equipo_neto',   # net PP&E
    'activos_intangibles',            # intangibles and goodwill
    'otros_activos_no_corrientes',    # other non-current assets
    'activo_no_corriente_total',      # total non-current assets
    'activo_total',                   # total assets

    # Pasivos corrientes / Current liabilities
    'cuentas_por_pagar',              # accounts payable
    'deuda_financiera_corto_plazo',   # short-term financial debt
    'otros_pasivos_corrientes',       # other current liabilities
    'pasivo_corriente_total',         # total current liabilities

    # Pasivos no corrientes / Non-current liabilities
    'deuda_financiera_largo_plazo',   # long-term financial debt
    'otros_pasivos_no_corrientes',    # other non-current liabilities
    'pasivo_no_corriente_total',      # total non-current liabilities
    'pasivo_total',                   # total liabilities

    # Patrimonio / Equity
    'capital_social',                 # share capital
    'utilidades_retenidas',           # retained earnings
    'otras_reservas',                 # other reserves / OCI
    'patrimonio_controladora',        # equity attributable to owners of the parent
    'participaciones_no_controladoras',  # non-controlling interests
    'patrimonio_total',               # total equity

    # Partidas derivadas / Derived items
    # Vienen calculadas desde la plantilla. Se conservan en el CSV
    # para que el ETL sea un mapeo directo y para poder verificar
    # los cálculos del sistema contra la hoja de cálculo.
    'deuda_financiera_total',         # short-term + long-term debt
    'capital_trabajo_neto',           # current assets - current liabilities
]

# ── ESTADO DE RESULTADOS / INCOME STATEMENT ───────────────
COLUMNAS_RESULTADOS = [
    'ventas_netas',                   # net sales / operating revenue
    'costo_ventas',                   # cost of goods sold
    'utilidad_bruta',                 # gross profit
    'gastos_ventas',                  # selling expenses
    'gastos_administracion',          # administrative expenses
    'depreciacion_amortizacion',      # depreciation & amortization
    'otros_gastos_operativos',        # other operating expenses
    'total_gastos_operativos',        # total operating expenses
    'utilidad_operativa',             # operating income (EBIT)
    'ingresos_financieros',           # financial income
    'gastos_financieros',             # financial expenses (interest)
    'otros_ingresos_netos',           # other net income (expenses)
    'utilidad_antes_impuestos',       # income before taxes (EBT)
    'impuesto_renta',                 # income tax
    'utilidad_neta',                  # net income
    'utilidad_neta_controladora',     # profit attributable to owners of the parent
    'utilidad_neta_no_controladoras', # profit attributable to NCI

    # Derivadas para WACC / EVA / Derived for WACC / EVA
    'ebitda',                         # EBIT + D&A
    'tasa_impuesto_efectiva',         # effective tax rate
    'nopat',                          # net operating profit after tax
]

# ── TODAS LAS COLUMNAS / ALL COLUMNS ─────────────────────
# ES: Combinación de ambas listas para validación completa
# EN: Combined list for full CSV validation
TODAS_LAS_COLUMNAS = COLUMNAS_BALANCE + COLUMNAS_RESULTADOS