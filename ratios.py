from pathlib import Path

import numpy as np
import pandas as pd

CARPETA_DATOS=Path(__file__).resolve().parent/"Datos"

def dividir(a, b):
    resultado=a/b
    resultado=resultado.replace([np.inf,-np.inf],np.nan)
    return resultado


def calcular_ratios(df):
    df =df.copy()
    df=df.sort_values(["ticker", "year"])
    #print(df)
    ebit_aproximado = df["beneficio_antes_impuestos"]+df["intereses"].fillna(0)
    df["ebit"] =df["ebit"].fillna(ebit_aproximado)
    amortizacion_separada=df["depreciacion"]+df["amortizacion_intangibles"].fillna(0)
    df["amortizacion"]=df["amortizacion"].fillna(amortizacion_separada)
    df["ebitda"]=df["ebit"]+df["amortizacion"]
    df["margen_ebitda"] =dividir(df["ebitda"], df["ingresos"])
    df["crecimiento_ingresos"]= df.groupby("ticker")["ingresos"].pct_change()
    df["capex_ventas"]=dividir(df["capex"],df["ingresos"])
    df["flujo_caja_libre"]=df["flujo_operativo"]-df["capex"]
    df["conversion_caja"]=dividir(df["flujo_caja_libre"] ,df["ebitda"])
    df["deuda_neta"]= df["deuda"]-df["caja"].fillna(0)
    df["deuda_neta_ebitda"]=dividir(df["deuda_neta"],df["ebitda"])
    df.loc[df["ebitda"]<=0, "deuda_neta_ebitda"]=np.nan
    return df


if __name__=="__main__":
    financieros=pd.read_csv(CARPETA_DATOS/"financieros.csv")
    ratios=calcular_ratios(financieros)
    years_por_empresa=ratios.groupby("ticker")["year"].count()
    # print(years_por_empresa)
    validas=[]
    for ticker in years_por_empresa.index:
        if years_por_empresa[ticker]>=6:
            validas.append(ticker)
        else:
            print("Se quita", ticker,"por tener menos de 6 años de datos")
    ratios = ratios[ratios["ticker"].isin(validas)]
    ratios.to_csv(CARPETA_DATOS/"ratios.csv",index=False)
    print(ratios[["ticker","year" , "ingresos", "margen_ebitda" ,"crecimiento_ingresos","conversion_caja", "deuda_neta_ebitda"]].tail(10))
