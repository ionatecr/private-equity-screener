import time
from pathlib import Path

import pandas as pd
import requests

CARPETA_DATOS=Path(__file__).resolve().parent/"Datos"
CABECERA={"User-Agent": "Private Equity Screener privateequityscreener@gmail.com"}

TICKERS=[
    "AAPL", "MSFT","GOOGL","AMZN","META","NVDA", "ADBE","CRM" , "ORCL","CSCO",
    "KO" ,"PEP","PG", "CL","KMB" ,"MDLZ", "HSY","GIS","KHC","CPB",
    "JNJ", "PFE","MRK","ABT","TMO","MMM","HON" , "CAT" ,"DE","GE",
    "HD","LOW","WMT","TGT","COST","NKE","MCD","SBUX", "YUM","CMG" ,
]

ETIQUETAS={
    "ingresos": ["Revenues","RevenueFromContractWithCustomerExcludingAssessedTax","SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "ebit": ["OperatingIncomeLoss"],
    "beneficio_antes_impuestos": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest","IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"] ,
    "intereses": ["InterestExpense","InterestExpenseNonoperating"] ,
    "amortizacion": ["DepreciationDepletionAndAmortization","DepreciationAndAmortization","DepreciationAmortizationAndAccretionNet"],
    "depreciacion": ["Depreciation"],
    "amortizacion_intangibles": ["AmortizationOfIntangibleAssets"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "flujo_operativo": ["NetCashProvidedByUsedInOperatingActivities"],
    "caja": ["CashAndCashEquivalentsAtCarryingValue" ,"CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "deuda": ["LongTermDebt","LongTermDebtNoncurrent" , "LongTermDebtAndCapitalLeaseObligations"],
}

STOCK=["caja","deuda"]


def leer_ciks():
    url="https://www.sec.gov/files/company_tickers.json"
    respuesta=requests.get(url, headers=CABECERA)
    datos=respuesta.json()
    #print(datos)
    ciks={}
    for clave in datos:
        empresa= datos[clave]
        ciks[empresa["ticker"]] = [str(empresa["cik_str"]).zfill(10),empresa["title"]]
    return ciks


def valores_anuales(hechos,etiqueta,es_stock):
    if etiqueta not in hechos:
        return {}
    unidades=hechos[etiqueta]["units"]
    if "USD" not in unidades:
        return {}
    valores={}
    for fila in unidades["USD"]:
        if fila.get("form")!="10-K":
            continue
        fin=pd.to_datetime(fila["end"])
        if not es_stock:
            if "start" not in fila:
                continue
            dias=(fin - pd.to_datetime(fila["start"])).days
            if dias < 330 or dias > 400:
                continue
        valores[fin.year] = fila["val"]
    return valores


def descargar_empresa(ticker,cik , nombre):
    url="https://data.sec.gov/api/xbrl/companyfacts/CIK"+cik+".json"
    respuesta=requests.get(url, headers=CABECERA)
    if respuesta.status_code!=200:
        print("No se ha podido descargar",ticker)
        return []
    hechos=respuesta.json()["facts"].get("us-gaap", {})
    tabla= {}
    for metrica in ETIQUETAS:
        es_stock=metrica in STOCK
        juntos={}
        for etiqueta in ETIQUETAS[metrica]:
            valores=valores_anuales(hechos,etiqueta,es_stock)
            #print(valores)
            for year in valores:
                if year not in juntos:
                    juntos[year]=valores[year]
        tabla[metrica]=juntos
    years= list(tabla["ingresos"].keys())
    years.sort()
    filas=[]
    for year in years:
        fila={"ticker": ticker,"nombre": nombre,"year": year}
        for metrica in tabla:
            fila[metrica]=tabla[metrica].get(year)
        filas.append(fila)
    return filas


def descargar_todo():
    ciks=leer_ciks()
    filas=[]
    for ticker in TICKERS:
        if ticker not in ciks:
            print("Ticker no encontrado",ticker)
            continue
        cik ,nombre = ciks[ticker]
        filas=filas+descargar_empresa(ticker, cik, nombre)
        print("Descargado",ticker)
        time.sleep(0.2)
    df=pd.DataFrame(filas)
    df=df[df["year"]>=df["year"].max()-10]
    CARPETA_DATOS.mkdir(exist_ok = True)
    df.to_csv(CARPETA_DATOS/"financieros.csv",index= False)
    return df


if __name__=="__main__":
    df=descargar_todo()
    print(df.head())
    print(df.shape)
