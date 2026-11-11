import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

CARPETA_DATOS=Path(__file__).resolve().parent/"Datos"
CABECERA={"User-Agent": "Private Equity Screener ionatecr12@gmail.com"}

TICKERS=[
    "AAPL","MSFT", "GOOGL", "AMZN","META", "NVDA","ADBE","ORCL","KO","PEP","PG","HSY","JNJ","PFE","MRK","CAT","DE","HD","WMT","MCD",
]

ETIQUETAS={
    "ingresos": ["Revenues","RevenueFromContractWithCustomerExcludingAssessedTax"],
    "ebit": ["OperatingIncomeLoss"],
    "amortizacion": ["DepreciationDepletionAndAmortization"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "flujo_operativo": ["NetCashProvidedByUsedInOperatingActivities"],
    "caja": ["CashAndCashEquivalentsAtCarryingValue"],
    "deuda": ["LongTermDebt"],
}


def leer_ciks():
    url="https://www.sec.gov/files/company_tickers.json"
    respuesta=requests.get(url, headers=CABECERA)
    datos=respuesta.json()
    ciks={}
    for clave in datos:
        empresa= datos[clave]
        ciks[empresa["ticker"]] = [str(empresa["cik_str"]).zfill(10),empresa["title"]]
    return ciks


def valores_anuales(hechos,etiqueta):
    if etiqueta not in hechos:
        return {}
    valores={}
    for fila in hechos[etiqueta]["units"]["USD"]:
        if fila["form"] !="10-K":
            continue
        fin=pd.to_datetime(fila["end"])
        if "start" in fila:
            dias=(fin - pd.to_datetime(fila["start"])).days
            if dias < 330 or dias > 400:
                continue
        valores[fin.year] = fila["val"]
    return valores


def descargar_empresa(ticker,cik , nombre):
    url="https://data.sec.gov/api/xbrl/companyfacts/CIK"+cik+".json"
    respuesta =requests.get(url,headers=CABECERA)
    print(respuesta.status_code)
    hechos=respuesta.json()["facts"]["us-gaap"]
    tabla= {}
    for metrica in ETIQUETAS:
        juntos={}
        for etiqueta in ETIQUETAS[metrica]:
            valores=valores_anuales(hechos, etiqueta)
            for year in valores:
                if year not in juntos:
                    juntos[year]=valores[year]
        tabla[metrica]=juntos
    filas=[]
    for year in tabla["ingresos"]:
        fila={"ticker": ticker,"nombre": nombre,"year": year}
        for metrica in tabla:
            fila[metrica]=tabla[metrica].get(year)
        filas.append(fila)
    return filas


def calcular_ratios(df):
    df=df.sort_values(["ticker", "year"])
    df["ebitda"]=df["ebit"]+df["amortizacion"]
    df["margen_ebitda"]=df["ebitda"]/df["ingresos"]
    df["crecimiento_ingresos"]= df.groupby("ticker")["ingresos"].pct_change()
    df["capex_ventas"]=df["capex"]/df["ingresos"]
    df["flujo_caja_libre"]=df["flujo_operativo"]-df["capex"]
    df["conversion_caja"]=df["flujo_caja_libre"]/df["ebitda"]
    df["deuda_neta"]= df["deuda"]-df["caja"]
    df["deuda_neta_ebitda"] = df["deuda_neta"]/df["ebitda"]
    df=df.replace([np.inf,-np.inf] , np.nan)
    return df


if __name__=="__main__":
    ciks=leer_ciks()
    #print(ciks["AAPL"])
    filas=[]
    for ticker in TICKERS:
        cik ,nombre = ciks[ticker]
        print(ticker)
        filas=filas+descargar_empresa(ticker, cik, nombre)
        time.sleep(0.2)
    df=pd.DataFrame(filas)
    df=df[df["year"]>=2016]
    CARPETA_DATOS.mkdir(exist_ok = True)
    df.to_csv(CARPETA_DATOS/"financieros.csv",index= False)
    ratios=calcular_ratios(df)
    ratios.to_csv(CARPETA_DATOS/"ratios.csv",index=False)
    print(ratios.isna().sum())
    print(ratios[ratios["ticker"]=="AAPL"])
