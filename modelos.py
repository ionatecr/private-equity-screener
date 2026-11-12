from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_absolute_error, mean_squared_error,r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CARPETA_DATOS=Path(__file__).resolve().parent/"Datos"

VARIABLES=[
    "margen_ebitda","crecimiento_ingresos" ,"capex_ventas","conversion_caja" ,
    "deuda_neta_ebitda","margen_anterior", "crecimiento_anterior", "log_ingresos",
]

OBJETIVOS={
    "margen_ebitda": "margen_siguiente",
    "crecimiento_ingresos": "crecimiento_siguiente",
}

LIMITES={
    "margen_ebitda": [-1,1],
    "crecimiento_ingresos": [-0.5, 1],
    "capex_ventas": [0,0.5],
    "conversion_caja": [-3 , 3],
    "deuda_neta_ebitda": [-10, 10],
}


def preparar_panel(ratios):
    df= ratios.copy()
    df=df.sort_values(["ticker","year"])
    for columna in LIMITES:
        df[columna]=df[columna].clip(LIMITES[columna][0],LIMITES[columna][1])
    df["margen_anterior"]=df.groupby("ticker")["margen_ebitda"].shift(1)
    df["crecimiento_anterior"] =df.groupby("ticker")["crecimiento_ingresos"].shift(1)
    df["log_ingresos"]= np.log(df["ingresos"].clip(lower=1))
    df["margen_siguiente"] = df.groupby("ticker")["margen_ebitda"].shift(-1)
    df["crecimiento_siguiente"]=df.groupby("ticker")["crecimiento_ingresos"].shift(-1)
    siguiente_year= df.groupby("ticker")["year"].shift(-1)
    df.loc[siguiente_year!=df["year"]+1,"margen_siguiente"]=np.nan
    df.loc[siguiente_year!=df["year"]+1 , "crecimiento_siguiente"]=np.nan
    for columna in VARIABLES:
        df[columna]=df[columna].fillna(df[columna].median())
    return df


def crear_modelos():
    modelos={}
    modelos["ElasticNet"]=Pipeline([
        ("escalado",StandardScaler()),
        ("modelo", ElasticNet(alpha=0.01,random_state=123)),
    ])
    modelos["RandomForest"]=RandomForestRegressor(n_estimators = 200,max_depth=5,random_state=123)
    return modelos


def metricas(y_real,y_pred):
    mae=mean_absolute_error(y_real,y_pred)
    rmse= np.sqrt(mean_squared_error(y_real,y_pred))
    r2= r2_score(y_real , y_pred)
    return mae,rmse,r2


def evaluar(panel,year_corte):
    filas = []
    mejores={}
    for metrica in OBJETIVOS:
        objetivo=OBJETIVOS[metrica]
        datos=panel[panel[objetivo].notna()]
        train = datos[datos["year"] < year_corte]
        test=datos[datos["year"]>= year_corte]
        X_train=train[VARIABLES]
        y_train = train[objetivo]
        X_test=test[VARIABLES]
        y_test=test[objetivo]
        #print(train)
        mae,rmse , r2=metricas(y_test, test[metrica])
        filas.append({"objetivo": metrica, "modelo": "Igual que este año", "MAE": mae,"RMSE": rmse , "R2": r2})
        mejor_mae= mae
        mejores[metrica]= "Igual que este año"
        modelos=crear_modelos()
        for nombre in modelos:
            modelo=modelos[nombre]
            modelo.fit(X_train, y_train)
            y_pred=modelo.predict(X_test)
            mae,rmse , r2=metricas(y_test,y_pred)
            filas.append({"objetivo": metrica,"modelo": nombre,"MAE": mae,"RMSE": rmse , "R2": r2})
            if mae < mejor_mae:
                mejor_mae = mae
                mejores[metrica]=nombre
    return pd.DataFrame(filas),mejores


def predecir(panel,mejores):
    ultimas=panel.sort_values("year").groupby("ticker").tail(1).copy()
    resultado= ultimas[["ticker","nombre","year","margen_ebitda","crecimiento_ingresos"]].copy()
    years_prediccion=[]
    for a in resultado["year"]:
        years_prediccion.append(a+1)
    resultado["year_prediccion"]=years_prediccion
    for metrica in OBJETIVOS:
        objetivo=OBJETIVOS[metrica]
        datos=panel[panel[objetivo].notna()]
        modelos=crear_modelos()
        for nombre in modelos:
            modelo=modelos[nombre]
            modelo.fit(datos[VARIABLES], datos[objetivo])
            resultado["pred_"+metrica+"_"+nombre]=modelo.predict(ultimas[VARIABLES])
        resultado["pred_"+metrica+"_Igual que este año"]=ultimas[metrica].values
        resultado["pred_"+metrica]=resultado["pred_"+metrica+"_"+mejores[metrica]]
        resultado["modelo_"+metrica]=mejores[metrica]
    return resultado


def entrenar_todo(ratios):
    panel=preparar_panel(ratios)
    ultimo= int(panel[panel["margen_siguiente"].notna()]["year"].max())
    year_corte=ultimo-2
    tabla,mejores=evaluar(panel ,year_corte)
    #print(mejores)
    predicciones= predecir(panel, mejores)
    return tabla, predicciones


if __name__=="__main__":
    ratios = pd.read_csv(CARPETA_DATOS/"ratios.csv")
    tabla, predicciones=entrenar_todo(ratios)
    tabla.to_csv(CARPETA_DATOS/"metricas_modelos.csv", index=False)
    predicciones.to_csv(CARPETA_DATOS/"predicciones.csv" ,index=False)
    print(tabla)
    print(predicciones[["ticker","year_prediccion" , "pred_margen_ebitda","pred_crecimiento_ingresos"]].head(10))
