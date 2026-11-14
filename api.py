from pathlib import Path

import pandas as pd
from flask import Flask
from flask_restful import Api,Resource, abort , reqparse

import scoring

CARPETA_DATOS = Path(__file__).resolve().parent/"Datos"

ratios= scoring.poner_sector(pd.read_csv(CARPETA_DATOS/"ratios.csv"))
predicciones=pd.read_csv(CARPETA_DATOS/"predicciones.csv")

COLUMNAS_RANKING=["ranking","ticker","nombre" , "sector","year" , "score","cumple_deuda", "crecimiento_ingresos", "margen_ebitda","conversion_caja","deuda_neta_ebitda","capex_ventas", "ingresos"]

argumentos =reqparse.RequestParser()
argumentos.add_argument("crecimiento", type=int,default=3,location= "args")
argumentos.add_argument("caja",type=int,default=3 , location="args")
argumentos.add_argument("deuda",type=int,default=3 , location="args")
argumentos.add_argument("capex",type = int,default =3, location="args")
argumentos.add_argument("tamano",type=int ,default =3, location="args")
argumentos.add_argument("horizonte",type=int,default=3, location="args")
argumentos.add_argument("top", type=int,default=10,location="args")


def tabla_a_lista(df):
    df=df.round(4)
    df= df.astype(object).where(df.notna(),None)
    return df.to_dict(orient="records")


def leer_respuestas(args):
    respuestas={}
    for clave in scoring.PREGUNTAS:
        valor=args[clave]
        if valor < 1:
            valor =1
        if valor > 5:
            valor=5
        respuestas[clave]=valor
    return respuestas


class Ranking(Resource):

    def get(self):
        args=argumentos.parse_args()
        respuestas=leer_respuestas(args)
        ranking=scoring.ranking_respuestas(ratios , respuestas)
        ranking=ranking[COLUMNAS_RANKING].head(args["top"])
        return {"respuestas": respuestas, "pesos": scoring.test_a_pesos(respuestas),"ranking": tabla_a_lista(ranking)}


class Tesis(Resource):

    def get(self, nombre):
        if nombre not in scoring.TESIS:
            abort(404 ,message="No existe la tesis "+nombre+". Prueba con Value o Growth")
        respuestas=scoring.TESIS[nombre]
        ranking=scoring.ranking_respuestas(ratios , respuestas)
        ranking =ranking[COLUMNAS_RANKING].head(20)
        return {"tesis": nombre,"respuestas": respuestas, "ranking": tabla_a_lista(ranking)}


class Empresa(Resource):

    def get(self, ticker):
        ticker=ticker.upper()
        historico =ratios[ratios["ticker"]==ticker]
        if len(historico)==0:
            abort(404,message="No existe la empresa "+ticker)
        columnas=["year" , "ingresos","ebitda", "margen_ebitda","crecimiento_ingresos" ,"capex_ventas","conversion_caja","deuda_neta_ebitda"]
        prediccion=predicciones[predicciones["ticker"]==ticker]
        return {"ticker": ticker,"historico": tabla_a_lista(historico[columnas]),"prediccion": tabla_a_lista(prediccion)}


class Prediccion(Resource):

    def get(self, ticker):
        ticker=ticker.upper()
        prediccion=predicciones[predicciones["ticker"]==ticker]
        if len(prediccion)==0:
            abort(404,message="No hay predicción para "+ticker)
        columnas=["ticker","year_prediccion", "pred_margen_ebitda","modelo_margen_ebitda","pred_crecimiento_ingresos","modelo_crecimiento_ingresos"]
        return tabla_a_lista(prediccion[columnas])[0]


def crear_api(server):
    api = Api(server)
    api.add_resource(Ranking, "/api/ranking")
    api.add_resource(Tesis,"/api/tesis/<string:nombre>")
    api.add_resource(Empresa,"/api/empresa/<string:ticker>")
    api.add_resource(Prediccion,"/api/prediccion/<string:ticker>")
    return api


if __name__=="__main__":
    app =Flask(__name__)
    crear_api(app)
    app.run(debug = True)
