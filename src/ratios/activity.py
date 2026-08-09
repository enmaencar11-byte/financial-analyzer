#FinAnalyzer Pro activity.py
#ES: Que tan bien la empresa usa su recursos para generar ventas
#EN: How well does the company use its resources to generate sales?

import pandas as pd

def rotacion_inventarios(df):                                         #How many times did you sell all your inventory?

   return df['costo_ventas'] / df['inventarios']

def dias_inventario(df):
    
    return df['365' * 'inventarios'] / df['costo_ventas']           # How many days does it take to sell everything?

def rotacion_cuentas_x_cobrar(df):
    
    return df['ventas_netas'] / df['cuentas_por_cobrar']            # How quickly does he collect what it is owed?

def rotacion_activos(df):
    
    return df['ventas_netas'] / df['activo_total']                   # How many pesos does it generate for every pesos of assets it owns?