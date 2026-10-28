"""
Traducción de los textos que el usuario ve.

ALCANCE

Se traduce lo que aparece en el panel y en las figuras: títulos, ejes,
leyendas, rótulos de control, nombres de indicador y encabezados de
tabla. No se traducen los docstrings ni los comentarios del código, que
son documentación para quien lo lea y mantenerlos en dos idiomas
duplicaría el trabajo de cada cambio futuro sin beneficio alguno para el
usuario.

DISEÑO

La clave de cada término es su propia redacción en español. Esa decisión
tiene una consecuencia práctica: en español la traducción es la función
identidad, de modo que el camino por omisión no puede romperse, y un
término sin traducir aparece en español en lugar de mostrar una clave
técnica o provocar un error.

    t('Puntaje Z\\'\\'')      → "Puntaje Z''"   en español
                             → "Z'' score"     en inglés

USO

    from src.idioma import t, fijar

    fijar('en')
    t('Riesgo de insolvencia')     # 'Insolvency risk'

El idioma es un estado del proceso y no un argumento que recorra cada
función. Un panel que debiera pasar el código de idioma a cada llamada
de figura acabaría olvidándolo en alguna, y el resultado sería una
figura en español dentro de una página en inglés.
"""

IDIOMAS = {'es': 'Español', 'en': 'English'}
POR_OMISION = 'es'

_actual = POR_OMISION


def fijar(codigo):
    """Fija el idioma del proceso. Un código desconocido se rechaza."""
    global _actual
    if codigo not in IDIOMAS:
        raise ValueError(f'Idioma desconocido: {codigo}. '
                         f'Opciones: {", ".join(IDIOMAS)}')
    _actual = codigo
    return _actual


def actual():
    """Código del idioma vigente."""
    return _actual


def t(texto):
    """
    Traduce un término al idioma vigente.

    En español devuelve el propio texto. En otro idioma devuelve su
    traducción, o el texto original si no se ha registrado: una cadena
    sin traducir se lee en español, que es inconveniente pero legible,
    mientras que un error interrumpiría la página entera.
    """
    if _actual == POR_OMISION or not isinstance(texto, str):
        return texto
    return TRADUCCIONES.get(_actual, {}).get(texto, texto)


def traducir_columnas(tabla):
    """Devuelve la tabla con sus encabezados traducidos."""
    if _actual == POR_OMISION:
        return tabla
    return tabla.rename(columns=t)


def traducir_valores(serie):
    """Traduce los valores de una columna de texto (zonas, veredictos)."""
    if _actual == POR_OMISION:
        return serie
    return serie.map(lambda v: t(v) if isinstance(v, str) else v)


# ── Diccionario ──────────────────────────────────────────────────

_EN = {
    # Encabezado y navegación
    'FinAnalyzer Pro': 'FinAnalyzer Pro',
    'Análisis de estados financieros de emisores no financieros '
    'dominicanos, {periodo}':
        'Financial statement analysis of Dominican non-financial issuers, '
        '{periodo}',
    'Muestra': 'Sample',
    'Emisores': 'Issuers',
    'Ejercicios': 'Fiscal years',
    'Parámetros del modelo': 'Model parameters',
    'Costo de capital impuesto': 'Imposed cost of capital',
    'Estructura': 'Structure',
    'Indicadores': 'Ratios',
    'Valor': 'Value',
    'Sensibilidad': 'Sensitivity',
    'Costo de capital': 'Cost of capital',
    'Riesgo': 'Risk',
    'Rendimiento': 'Return',
    'Validación': 'Validation',
    'Análisis vertical': 'Common-size analysis',
    'Análisis horizontal': 'Trend analysis',
    'Idioma': 'Language',

    # Indicadores del encabezado
    'WACC promedio': 'Average WACC',
    'EVA agregado': 'Aggregate EVA',
    'Observaciones que crean valor': 'Observations creating value',
    'Emisores incluidos en la selección actual.':
        'Issuers included in the current selection.',
    'Promedio simple del costo promedio ponderado de capital sobre todas '
    'las observaciones.':
        'Simple average of the weighted average cost of capital across all '
        'observations.',
    'Suma del valor económico agregado de todos los emisores y ejercicios.':
        'Sum of economic value added across all issuers and fiscal years.',
    'Observaciones con valor económico agregado positivo.':
        'Observations with positive economic value added.',

    # Controles
    'Tasa libre de riesgo': 'Risk-free rate',
    'Prima de riesgo de mercado': 'Equity risk premium',
    'Prima de riesgo país': 'Country risk premium',
    'Beta desapalancado del sector': 'Sector unlevered beta',
    'Costo de la deuda antes de impuestos': 'Pre-tax cost of debt',
    'Imponer un WACC': 'Impose a WACC',
    'WACC impuesto': 'Imposed WACC',
    'Parámetros sustituidos:': 'Substituted parameters:',
    'Categoría': 'Category',
    'Tabla': 'Table',
    'Nivel de descomposición': 'Decomposition level',
    'Emisor para la descomposición de la variación':
        'Issuer for the decomposition of the change',
    'Balance general': 'Balance sheet',
    'Estado de resultados': 'Income statement',
    'Números índice': 'Index numbers',
    'Variación interanual (%)': 'Year-over-year change (%)',
    'Variación absoluta': 'Absolute change',

    # Mensajes
    'Todos los parámetros provienen del archivo.':
        'All parameters come from the parameter file.',
    'La selección no deja observaciones.':
        'The selection leaves no observations.',
    'Todas las comprobaciones de consistencia interna se satisfacen.':
        'All internal consistency checks are satisfied.',
    'Alguna comprobación no se satisface. Revise los datos de entrada.':
        'A check is not satisfied. Review the input data.',

    # Secciones
    'Composición y evolución': 'Composition and change',
    'Razones financieras': 'Financial ratios',
    'Creación y destrucción de valor': 'Value creation and destruction',
    'Sensibilidad al costo de capital': 'Sensitivity to the cost of capital',
    'Costo del capital': 'Cost of capital',
    'Riesgo de insolvencia': 'Insolvency risk',
    'Descomposición del rendimiento': 'Decomposition of return',
    'Consistencia interna': 'Internal consistency',
    '**Costo del patrimonio**': '**Cost of equity**',
    '**Costo promedio ponderado**': '**Weighted average cost**',

    # Títulos de figura
    "Riesgo de insolvencia — Altman Z'' de cuatro variables":
        "Insolvency risk — four-variable Altman Z''",
    'Retorno sobre el capital invertido frente a su costo':
        'Return on invested capital against its cost',
    'Valor económico agregado por emisor y ejercicio':
        'Economic value added by issuer and fiscal year',
    'Composición del costo promedio ponderado de capital':
        'Composition of the weighted average cost of capital',
    'Sensibilidad del valor económico agregado al costo de capital':
        'Sensitivity of economic value added to the cost of capital',
    'Composición del activo total — análisis vertical':
        'Composition of total assets — common-size analysis',
    'Estructura del estado de resultados — análisis vertical':
        'Income statement structure — common-size analysis',

    # Ejes y rótulos de figura
    'Ejercicio': 'Fiscal year',
    'Tasa anual': 'Annual rate',
    "Puntaje Z''": "Z'' score",
    'EVA (unidades monetarias)': 'EVA (monetary units)',
    'EVA promedio del período': 'Average EVA for the period',
    'Costo promedio ponderado de capital supuesto':
        'Assumed weighted average cost of capital',
    'Aporte a la variación del ROE (%)':
        'Contribution to the change in ROE (%)',
    'ROE (producto de los factores)': 'ROE (product of the factors)',
    'Por encima del eje cero el emisor crea valor':
        'Above the zero axis the issuer creates value',
    'Zona segura': 'Safe zone',
    'Zona gris': 'Grey zone',
    'Zona de peligro': 'Distress zone',
    'Crea valor': 'Creates value',
    'Destruye valor': 'Destroys value',
    'Patrimonio': 'Equity',
    'Deuda': 'Debt',
    'Resto del activo': 'Other assets',
    'Costo de ventas': 'Cost of sales',
    'Gastos operativos': 'Operating expenses',
    'Costo financiero neto': 'Net financial cost',
    'Impuesto sobre la renta': 'Income tax',
    'Total': 'Total',

    # Partidas
    'Efectivo': 'Cash',
    'Cuentas por cobrar': 'Accounts receivable',
    'Inventarios': 'Inventories',
    'Propiedad, planta y equipo': 'Property, plant and equipment',
    'Intangibles': 'Intangibles',
    'Otros corrientes': 'Other current',
    'Otros no corrientes': 'Other non-current',
    'Ventas netas': 'Net sales',
    'Utilidad operativa': 'Operating income',
    'Utilidad neta': 'Net income',
    'Activo total': 'Total assets',
    'Deuda financiera': 'Financial debt',
    'EBITDA': 'EBITDA',

    # Categorías. Las variantes en minúscula existen porque el título en
    # español las lleva dentro de la frase ('Indicadores de liquidez') y el
    # inglés las lleva al principio ('Liquidity ratios'), de modo que la
    # capitalización depende del idioma y no del código que las compone.
    'liquidez': 'Liquidity',
    'rentabilidad': 'Profitability',
    'apalancamiento': 'Leverage',
    'actividad': 'Activity',
    'Liquidez': 'Liquidity',
    'Rentabilidad': 'Profitability',
    'Apalancamiento': 'Leverage',
    'Actividad': 'Activity',

    # Indicadores — liquidez
    'Razón corriente': 'Current ratio',
    'Prueba ácida': 'Quick ratio',
    'Razón de efectivo': 'Cash ratio',
    'Capital de trabajo neto': 'Net working capital',
    'Capital de trabajo / Activos': 'Working capital / Assets',
    'Deuda CP / Deuda total': 'Short-term debt / Total debt',

    # Indicadores — rentabilidad
    'Margen bruto': 'Gross margin',
    'Margen operativo': 'Operating margin',
    'Margen EBITDA': 'EBITDA margin',
    'Margen neto': 'Net margin',
    'Margen NOPAT': 'NOPAT margin',
    'ROA': 'ROA',
    'ROE': 'ROE',
    'ROIC': 'ROIC',
    'ROCE': 'ROCE',

    # Indicadores — apalancamiento
    'Endeudamiento total': 'Total debt ratio',
    'Endeudamiento financiero': 'Financial debt ratio',
    'Deuda / Patrimonio': 'Debt / Equity',
    'Apalancamiento financiero': 'Financial leverage',
    'Cobertura de intereses (EBIT)': 'Interest coverage (EBIT)',
    'Cobertura de intereses (EBITDA)': 'Interest coverage (EBITDA)',
    'Deuda financiera / EBITDA': 'Financial debt / EBITDA',
    'Deuda neta / EBITDA': 'Net debt / EBITDA',
    'Calidad de la deuda': 'Debt quality',

    # Indicadores — actividad
    'Rotación de activos': 'Asset turnover',
    'Rotación de inventarios': 'Inventory turnover',
    'Días de inventario': 'Days inventory',
    'Rotación de cuentas por cobrar': 'Receivables turnover',
    'Días de cobro (DSO)': 'Days sales outstanding (DSO)',
    'Rotación de cuentas por pagar': 'Payables turnover',
    'Días de pago (DPO)': 'Days payable outstanding (DPO)',
    'Ciclo operativo': 'Operating cycle',
    'Ciclo de conversión de efectivo': 'Cash conversion cycle',

    # DuPont
    'Carga fiscal': 'Tax burden',
    'Carga financiera': 'Interest burden',
    'ROE calculado': 'Computed ROE',
    'ROE reportado': 'Reported ROE',

    # Altman
    'X1 Capital de trabajo / Activo': 'X1 Working capital / Assets',
    'X2 Utilidades retenidas / Activo': 'X2 Retained earnings / Assets',
    'X3 Utilidad operativa / Activo': 'X3 Operating income / Assets',
    'X4 Patrimonio / Pasivo': 'X4 Equity / Liabilities',
    'Aporte X1': 'X1 contribution',
    'Aporte X2': 'X2 contribution',
    'Aporte X3': 'X3 contribution',
    'Aporte X4': 'X4 contribution',
    "Z''": "Z''",
    'EM Score': 'EM Score',
    'Zona': 'Zone',
    'Segura': 'Safe',
    'Gris': 'Grey',
    'Peligro': 'Distress',
    'No aplica': 'Not applicable',

    # Costo de capital
    'Rf': 'Rf',
    'ERP': 'ERP',
    'CRP': 'CRP',
    'Beta desapalancado': 'Unlevered beta',
    'Tasa impuesto': 'Tax rate',
    'D/E financiera': 'Financial D/E',
    'Beta reapalancado': 'Relevered beta',
    'Prima por riesgo sistemático': 'Systematic risk premium',
    'Ke': 'Ke',
    'Kd': 'Kd',
    'Kd después de impuestos': 'After-tax Kd',
    'Capital total': 'Total capital',
    'Peso patrimonio': 'Equity weight',
    'Peso deuda': 'Debt weight',
    'Aporte del patrimonio': 'Equity contribution',
    'Aporte de la deuda': 'Debt contribution',
    'WACC': 'WACC',

    # EVA
    'Capital invertido': 'Invested capital',
    'NOPAT': 'NOPAT',
    'Diferencial ROIC − WACC': 'ROIC − WACC spread',
    'Cargo por uso de capital': 'Capital charge',
    'EVA': 'EVA',
    'Resultado': 'Result',
    'EVA directo': 'Direct EVA',
    'EVA por diferencial': 'Spread-based EVA',
    'Diferencia relativa': 'Relative difference',
    'Coincide': 'Agrees',

    # Validación
    'Comprobación': 'Check',
    'Observaciones': 'Observations',
    'Satisfacen': 'Satisfied',
    'Discrepancia máxima': 'Maximum discrepancy',
    'Identidad DuPont nivel 2': 'DuPont identity, level 2',
    'Identidad DuPont nivel 3': 'DuPont identity, level 3',
    'Equivalencia de las formulaciones del EVA':
        'Equivalence of the EVA formulations',
    'Satisface': 'Satisfied',
    'Revisar': 'Review',

    # Mensajes del proceso por lotes
    'Libro escrito en {archivo}': 'Workbook written to {archivo}',
    'Hojas: {n}': 'Sheets: {n}',
    'ATENCIÓN: {n} comprobación(es) no se satisfacen. Revise la hoja {hoja}.':
        'WARNING: {n} check(s) are not satisfied. See the {hoja} sheet.',
    'Archivo cargado correctamente': 'File loaded successfully',

    # Hojas del libro de resultados
    'Datos': 'Data',
    'Vertical balance': 'Common-size balance sheet',
    'Vertical resultados': 'Common-size income statement',
    'Horizontal interanual': 'Year-over-year change',
    'Horizontal absoluta': 'Absolute change',
    'Horizontal indices': 'Index numbers',
    'Ratios detalle': 'Ratios detail',
    'DuPont nivel 1': 'DuPont level 1',
    'DuPont nivel 2': 'DuPont level 2',
    'DuPont nivel 3': 'DuPont level 3',
    'DuPont verificacion': 'DuPont verification',
    'Altman': 'Altman',
    'CAPM': 'CAPM',
    'EVA verificacion': 'EVA verification',
    'Validacion': 'Validation',
    'Parametros usados': 'Parameters used',

    # Tabla de validación del reporte
    'Condición': 'Condition',
    'Tolerancia': 'Tolerance',
    'Cuadre del balance': 'Balance sheet balances',
    'Activo = Pasivo + Patrimonio': 'Assets = Liabilities + Equity',
    'Base del vertical del balance': 'Common-size balance sheet base',
    'Base del vertical de resultados': 'Common-size income statement base',
    'Producto de los factores = ROE': 'Product of the factors = ROE',
    'NOPAT − CI×WACC = (ROIC − WACC)×CI':
        'NOPAT − IC×WACC = (ROIC − WACC)×IC',
    'Indicadores calculados': 'Ratios computed',
    'Catálogo completo': 'Complete catalogue',

    # Hoja de parámetros empleados
    'Concepto': 'Item',
    'Origen': 'Source',
    'Fecha de ejecución': 'Run date',
    'Instrucción de ejecución': 'Command line',
    'Archivo de parámetros o datos': 'Parameter file or data',
    'Estados financieros': 'Financial statements',
    'Calculado': 'Computed',
    'wacc impuesto': 'imposed wacc',

    # Resumen en pantalla del proceso por lotes
    'VALIDACIÓN — CONSISTENCIA INTERNA':
        'VALIDATION — INTERNAL CONSISTENCY',
    'RESULTADO POR EMISOR Y EJERCICIO':
        'RESULT BY ISSUER AND FISCAL YEAR',
    'Juicio EVA': 'EVA verdict',

    # Carga de plantillas y parámetros
    'Datos': 'Data',
    'Emisor': 'Issuer',
    'Sector': 'Sector',
    'Eliminar': 'Remove',
    'Guardado.': 'Saved.',
    'Plantillas': 'Templates',
    'Por emisor': 'By issuer',
    'Por ejercicio': 'By fiscal year',
    'Plantillas cargadas': 'Loaded templates',
    'Plantillas de los emisores': 'Issuer templates',
    'Guardar parámetros de mercado': 'Save market parameters',
    'Guardar parámetros sectoriales': 'Save sector parameters',
    '{n} plantilla(s) incorporada(s).': '{n} template(s) loaded.',
    'Todavía no hay ninguna plantilla cargada.':
        'No template has been loaded yet.',
    'Parámetros del modelo de costo de capital':
        'Cost of capital model parameters',
    'Todavía no hay datos cargados. Suba al menos una plantilla para '
    'comenzar.':
        'No data has been loaded yet. Upload at least one template to '
        'begin.',
    'La plantilla quedó guardada pero no se incorporó. Corrija el archivo '
    'y vuelva a subirlo, o elimínelo de la lista.':
        'The template was saved but not loaded. Correct the file and '
        'upload it again, or remove it from the list.',
    'El sistema no calcula un costo de capital sobre parámetros ausentes: '
    'se detiene e indica cuál falta. Complételos aquí.':
        'The system does not compute a cost of capital on missing '
        'parameters: it stops and names the one that is absent. Fill them '
        'in here.',
    'El archivo debe haberse abierto y guardado en Excel al menos una vez '
    'después de llenarlo: las celdas con fórmula se leen vacías en caso '
    'contrario.':
        'The file must have been opened and saved in Excel at least once '
        'after being filled in: cells containing formulas read as empty '
        'otherwise.',
    'Los parámetros son estimaciones y constituyen decisiones '
    'metodológicas: registre la fuente y su fecha, porque un costo de '
    'capital sin ellas no es verificable.':
        'The parameters are estimates and constitute methodological '
        'decisions: record the source and its date, because a cost of '
        'capital without them is not verifiable.',
    'Arrastre aquí las plantillas de Excel, una por emisor. El sistema las '
    'guarda, las consolida y comprueba el cuadre del balance y la '
    'distribución del resultado antes de aceptarlas.':
        'Drop the Excel templates here, one per issuer. The system saves '
        'them, consolidates them and checks that the balance sheet '
        'balances and the result is correctly distributed before '
        'accepting them.',

    # Ayudas de los controles de parámetro
    'Rendimiento del bono del Tesoro de los Estados Unidos.':
        'Yield on United States Treasury bonds.',
    'Exceso histórico del mercado accionario sobre la tasa libre de riesgo.':
        'Historical excess of the equity market over the risk-free rate.',
    'Diferencial soberano de la República Dominicana. Es el parámetro al que '
    'el resultado resulta más sensible, por ser el único que entra como '
    'término aditivo independiente del coeficiente de riesgo sistemático.':
        'Sovereign spread of the Dominican Republic. It is the parameter the '
        'result is most sensitive to, being the only one that enters as an '
        'additive term independent of the systematic risk coefficient.',
    'Coeficiente de riesgo sistemático del sector, antes de ajustar por la '
    'estructura de capital del emisor. Un valor sustituto se aplica por '
    'igual a todos los emisores, lo que es apropiado para el análisis de '
    'sensibilidad pero no para un cálculo definitivo cuando la muestra '
    'abarca sectores distintos.':
        'Systematic risk coefficient of the sector, before adjusting for the '
        "issuer's capital structure. A substituted value applies equally to "
        'every issuer, which suits sensitivity analysis but not a definitive '
        'calculation when the sample spans different sectors.',
    'Sustituye al costo contable que se obtiene de los estados financieros.':
        'Replaces the accounting cost obtained from the financial statements.',

    # Párrafos explicativos del panel
    'Cada parámetro parte del valor registrado en el archivo. Actívelo para '
    'sustituirlo y observar el efecto sobre el resultado.':
        'Each parameter starts from the value recorded in the parameter '
        'file. Enable it to substitute that value and observe the effect on '
        'the result.',
    'Reemplaza al costo promedio ponderado que el modelo calcula. Sirve para '
    'contrastar el resultado frente a un costo de capital objetivo, sin '
    'recorrer la cadena completa del modelo.':
        'Replaces the weighted average cost the model computes. It serves to '
        'test the result against a target cost of capital without running '
        'the full chain of the model.',
    'Un valor ausente indica que el indicador no aplica al emisor y '
    'ejercicio correspondientes, no que valga cero. Un ROE calculado sobre '
    'patrimonio negativo, por ejemplo, resultaría positivo por cancelación '
    'de signos y carecería de significado económico, de modo que se excluye.':
        'A missing value means the ratio does not apply to that issuer and '
        'fiscal year, not that it equals zero. A ROE computed on negative '
        'equity, for instance, would come out positive because the signs '
        'cancel, and would carry no economic meaning, so it is excluded.',
    'El valor económico agregado contrasta el resultado operativo después de '
    'impuestos con el costo del capital empleado para generarlo. Una empresa '
    'puede presentar utilidad contable positiva y destruir valor económico, '
    'si el rendimiento del capital invertido no compensa el costo de los '
    'recursos.':
        'Economic value added contrasts after-tax operating income with the '
        'cost of the capital employed to generate it. A company may report '
        'positive accounting profit and still destroy economic value, if the '
        'return on invested capital does not cover the cost of the resources.',
    'El umbral es la cifra que acota la conclusión. Por encima de ese costo '
    'de capital el emisor destruye valor; por debajo, lo crea. La distancia '
    'que lo separa del costo estimado indica cuán robusta es la conclusión '
    'frente al supuesto adoptado.':
        'The threshold is the figure that bounds the conclusion. Above that '
        'cost of capital the issuer destroys value; below it, it creates '
        'value. The distance between the threshold and the estimated cost '
        'indicates how robust the conclusion is to the assumption adopted.',
    'La figura emplea los parámetros del archivo con independencia de los '
    'controles, pues su objeto es precisamente recorrer el intervalo '
    'completo de costos de capital posibles.':
        'The figure uses the parameters from the file regardless of the '
        'controls, since its purpose is precisely to span the full range of '
        'possible costs of capital.',
    'El costo promedio ponderado combina el costo del patrimonio, estimado '
    'por el modelo de valoración de activos de capital, con el costo de la '
    'deuda, obtenido de los estados financieros. El endeudamiento incide en '
    'dos direcciones opuestas: incrementa el riesgo que percibe el '
    'accionista y, a la vez, aumenta la participación de una fuente más '
    'barata y fiscalmente deducible.':
        'The weighted average cost combines the cost of equity, estimated by '
        'the capital asset pricing model, with the cost of debt, obtained '
        'from the financial statements. Leverage acts in two opposite '
        'directions: it raises the risk the shareholder perceives while '
        'increasing the share of a cheaper, tax-deductible source.',
    "El puntaje Z'' de cuatro variables corresponde a empresas sin "
    'cotización bursátil, que es la condición de los emisores dominicanos '
    'del mercado de valores: colocan deuda y no acciones, de modo que no '
    'existe precio de mercado de su patrimonio.':
        "The four-variable Z'' score applies to companies without a listed "
        'share price, which is the condition of Dominican issuers in the '
        'securities market: they place debt rather than equity, so no market '
        'price of their equity exists.',
    'El rendimiento sobre el patrimonio es el producto de sus factores, no '
    'su suma. La descomposición permite atribuir una variación a su causa: '
    'el desempeño de la operación, el costo del financiamiento o la carga '
    'tributaria, cada una de las cuales exige una respuesta distinta.':
        'Return on equity is the product of its factors, not their sum. The '
        'decomposition allows a change to be attributed to its cause: '
        'operating performance, the cost of financing or the tax burden, '
        'each of which calls for a different response.',
    'Las identidades algebraicas del sistema se comprueban en cada '
    'ejecución. Son verificaciones de consistencia interna: contrastan el '
    'sistema contra sí mismo y no contra una fuente externa, de modo que '
    'detectan incoherencia de cálculo y no error de origen en los datos.':
        'The algebraic identities of the system are checked on every run. '
        'They are internal consistency checks: they test the system against '
        'itself rather than against an external source, so they detect '
        'computational inconsistency and not errors in the source data.',
    'Las discrepancias del orden de 1e-17 no constituyen error: son el '
    'residuo de la aritmética de punto flotante, que no representa los '
    'números reales con precisión infinita.':
        'Discrepancies on the order of 1e-17 are not errors: they are the '
        'residue of floating-point arithmetic, which does not represent real '
        'numbers with infinite precision.',
    'Elija uno para el análisis individual, o varios para compararlos. El '
    'color de cada emisor no cambia al filtrar.':
        'Choose one for individual analysis, or several to compare them. '
        'Each issuer keeps its colour when the selection changes.',
    'Cada categoría responde una pregunta distinta sobre la misma empresa.':
        'Each category answers a different question about the same company.',
    'Cada partida como porcentaje de un total del mismo ejercicio: el activo '
    'total en el balance, las ventas netas en el estado de resultados. La '
    'lectura de márgenes es inmediata, porque la fila de utilidad bruta '
    '**es** el margen bruto.':
        'Each line item as a percentage of a total from the same fiscal '
        'year: total assets on the balance sheet, net sales on the income '
        'statement. Margins read directly, because the gross profit row '
        '**is** the gross margin.',
    'La variación de cada partida respecto del ejercicio anterior, y los '
    'números índice respecto de un año base igual a cien. Los índices '
    'permiten comparar en una misma escala partidas de magnitudes muy '
    'distintas.':
        'The change in each line item against the prior fiscal year, and '
        'index numbers against a base year equal to one hundred. Indices '
        'allow line items of very different magnitudes to be compared on a '
        'single scale.',
    'El primer ejercicio de cada emisor queda sin variación interanual '
    'porque no tiene período de comparación. La fila se conserva para que '
    'las tablas puedan alinearse entre sí.':
        'The first fiscal year of each issuer has no year-over-year change '
        'because it has no period to compare against. The row is kept so '
        'that the tables can be aligned with one another.',
    'El nivel 2 descompone en tres factores; el nivel 3 desagrega el margen '
    'neto en carga fiscal, carga financiera y margen operativo.':
        'Level 2 decomposes into three factors; level 3 breaks the net '
        'margin into tax burden, interest burden and operating margin.',
    'No hay ningún emisor seleccionado.\n\nElija al menos uno en la barra '
    'lateral para ver el análisis. Los parámetros del modelo quedan como '
    'estaban.':
        'No issuer is selected.\n\nChoose at least one in the sidebar to '
        'see the analysis. The model parameters are left as they were.',
    'Acota el período. El análisis horizontal y la descomposición de la '
    'variación toman como base el primer ejercicio del intervalo.':
        'Narrows the period. Trend analysis and the decomposition of the '
        'change take the first fiscal year of the range as their base.',

    # Plantillas con sustitución. Las llaves se conservan y el texto se
    # compone con .format(), de modo que el orden de los elementos pueda
    # diferir entre idiomas sin tocar el código que las usa.
    'Descomposición DuPont de nivel {n} — evolución por factor':
        'DuPont decomposition, level {n} — change by factor',
    'Indicadores de {cat} — evolución {a}–{b}':
        '{cat} ratios — {a}–{b}',
    'Aporte de cada factor a la variación del ROE — {e}':
        'Contribution of each factor to the change in ROE — {e}',
    'El ROE pasó de {i} en {ai} a {f} en {af}':
        'ROE moved from {i} in {ai} to {f} in {af}',
    'Evolución de las magnitudes principales — {b} = 100':
        'Change in the main magnitudes — {b} = 100',
    'El sistema calcula **{n} indicadores** agrupados en cuatro categorías. '
    'Ninguno responde por sí solo si la empresa va bien: el margen neto no '
    'sabe si puede pagar la nómina del mes, y la razón corriente no sabe si '
    'el negocio es rentable. Se leen en conjunto.':
        'The system computes **{n} ratios** grouped into four categories. '
        'None answers on its own whether the company is doing well: the net '
        'margin does not know whether payroll can be met this month, and the '
        'current ratio does not know whether the business is profitable. '
        'They are read together.',
    '{n} de {total}': '{n} of {total}',
    '{n} de {total} emisores · ejercicios {a}–{b}':
        '{n} of {total} issuers · fiscal years {a}–{b}',
    'No se encontró {archivo}.':
        'Could not find {archivo}.',
    'Ejecute antes `python -m src.etl` para consolidar las plantillas.':
        'Run `python -m src.etl` first to consolidate the templates.',

    # Empresa y año, encabezados de tabla
    'empresa': 'issuer',
    'anio': 'year',
}

TRADUCCIONES = {'en': _EN}