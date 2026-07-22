# FinAnalyzer Pro — config.py
# ES: Define en un solo lugar los nombres exactos
#     de todas las columnas que el sistema
#     espera encontrar en el CSV.
# EN: Defines in one place the exact column names
#     that the system expects to find in the CSV.

# ── BALANCE GENERAL / BALANCE SHEET ──────────────────────
COLUMNAS_BALANCE = [
    'empresa',                        # company name
    'anio',                           # year
    'efectivo_equivalentes',          # cash and equivalents
    'cuentas_por_cobrar',             # accounts receivable
    'inventarios',                    # inventories
    'otros_activos_corrientes',       # other current assets
    'activo_corriente_total',         # total current assets
    'propiedad_planta_equipo_neto',   # net PP&E
    'otros_activos_no_corrientes',    # other non-current assets
    'activo_total',                   # total assets
    'cuentas_por_pagar',              # accounts payable
    'deuda_financiera_corto_plazo',   # short-term financial debt
    'otros_pasivos_corrientes',       # other current liabilities
    'pasivo_corriente_total',         # total current liabilities
    'deuda_financiera_largo_plazo',   # long-term financial debt
    'otros_pasivos_no_corrientes',    # other non-current liabilities
    'pasivo_total',                   # total liabilities
    'capital_social',                 # share capital
    'utilidades_retenidas',           # retained earnings
    'patrimonio_total',               # total equity
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
    'tasa_impuesto_efectiva',         # effective tax rate
    'nopat',                          # net operating profit after tax
]

# ── TODAS LAS COLUMNAS / ALL COLUMNS ─────────────────────
# ES: Combinación de ambas listas para validación completa
# EN: Combined list for full CSV validation
TODAS_LAS_COLUMNAS = COLUMNAS_BALANCE + COLUMNAS_RESULTADOS