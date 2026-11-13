from pathlib import Path

import pandas as pd

CARPETA_DATOS=Path(__file__).resolve().parent/"Datos"

PREGUNTAS={
    "crecimiento": "¿Prefieres estabilidad (1) o crecimiento (5)?",
    "caja": "¿Cuánto te importa que la empresa genere caja?",
    "deuda": "¿Cuánta deuda estás dispuesto a aceptar?",
    "capex": "¿Aceptas negocios con mucha inversión en capex?",
    "tamano": "¿Prefieres empresas pequeñas (1) o grandes (5)?",
}

CRITERIOS={
    "crecimiento_ingresos": "mayor",
    "margen_ebitda": "mayor",
    "conversion_caja": "mayor" ,
    "deuda_neta_ebitda": "menor",
    "capex_ventas": "menor",
    "ingresos": "mayor" ,
}

TESIS={
    "Value": {"crecimiento": 1,"caja": 5,"deuda": 2,"capex": 1,"tamano": 3},
    "Growth": {"crecimiento": 5,"caja": 2, "deuda": 3,"capex": 4,"tamano": 3},
}


def test_a_pesos(respuestas):
    importancias={}
    importancias["crecimiento_ingresos"]=respuestas["crecimiento"]
    importancias["margen_ebitda"]=6-respuestas["crecimiento"]
    importancias["conversion_caja"]= respuestas["caja"]
    importancias["deuda_neta_ebitda"]=6-respuestas["deuda"]
    importancias["capex_ventas"]=6-respuestas["capex"]
    importancias["ingresos"]=abs(respuestas["tamano"]-3)
    total =0
    for criterio in importancias:
        total= total+importancias[criterio]
    pesos= {}
    for criterio in importancias:
        pesos[criterio]=importancias[criterio]/total
    return pesos


def test_a_umbrales(respuestas):
    umbrales={}
    umbrales["deuda_maxima"]=respuestas["deuda"]+0.5
    if respuestas["tamano"] > 3:
        umbrales["tamano"]="mayor"
    else:
        umbrales["tamano"]="menor"
    return umbrales


def ultimo_year_completo(ratios):
    conteo=ratios["year"].value_counts()
    maximo=conteo.max()
    years=list(conteo.index)
    years.sort(reverse=True)
    for year in years:
        if conteo[year]>= 0.8 * maximo:
            return year
    return years[0]


def puntuar(ratios,pesos,umbrales,year = None):
    if year is None:
        year=ultimo_year_completo(ratios)
    #print(year)
    df =ratios[ratios["year"]==year].copy()
    direcciones={}
    for c in CRITERIOS:
        direcciones[c]=CRITERIOS[c]
    direcciones["ingresos"]=umbrales["tamano"]
    df["score"]=0.0
    for criterio in pesos:
        percentil =df[criterio].rank(pct=True)
        if direcciones[criterio]=="menor":
            percentil=1-percentil+1/len(df)
        percentil=percentil.fillna(0.5)
        #print(percentil)
        df["aporte_"+criterio]=percentil * pesos[criterio] * 100
        df["score"]=df["score"]+df["aporte_"+criterio]
    df["score"]=df["score"].round(1)
    df["cumple_deuda"] = df["deuda_neta_ebitda"].fillna(0)<=umbrales["deuda_maxima"]
    df = df.sort_values("score",ascending=False)
    df["ranking"]=range(1,len(df)+1)
    return df


def ranking_respuestas(ratios,respuestas,year =None):
    pesos=test_a_pesos(respuestas)
    umbrales=test_a_umbrales(respuestas)
    return puntuar(ratios, pesos,umbrales, year)


def backtest(ratios,pesos,umbrales,top= 10):
    years=list(ratios["year"].unique())
    years.sort()
    ultimo=ultimo_year_completo(ratios)
    filas=[]
    for year in years:
        if year>=ultimo:
            continue
        if len(ratios[ratios["year"] ==year]) < 10:
            continue
        ranking=puntuar(ratios,pesos, umbrales , year)
        siguiente=ratios[ratios["year"] == year+1][["ticker","crecimiento_ingresos", "margen_ebitda"]]
        mejores = ranking.head(top)[["ticker"]].merge(siguiente,on="ticker")
        todas=ranking[["ticker"]].merge(siguiente,on ="ticker")
        # print(mejores)
        fila={
            "year": year,
            "crecimiento_top": mejores["crecimiento_ingresos"].median(),
            "crecimiento_universo": todas["crecimiento_ingresos"].median(),
            "margen_top": mejores["margen_ebitda"].median(),
            "margen_universo": todas["margen_ebitda"].median(),
        }
        filas.append(fila)
    return pd.DataFrame(filas)


def hacer_test():
    respuestas= {}
    for clave in PREGUNTAS:
        valor=int(input("Del 1 al 5. "+PREGUNTAS[clave]+" "))
        if valor < 1:
            valor=1
        if valor > 5:
            valor=5
        respuestas[clave]=valor
    return respuestas


if __name__=="__main__":
    ratios=pd.read_csv(CARPETA_DATOS/"ratios.csv")
    respuestas=hacer_test()
    pesos=test_a_pesos(respuestas)
    umbrales=test_a_umbrales(respuestas)
    print(pesos)
    ranking=puntuar(ratios,pesos, umbrales)
    print(ranking[["ranking","ticker","nombre","score", "cumple_deuda"]].head(20))
