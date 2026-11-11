from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input,Output,dcc, html

import scoring

CARPETA_DATOS = Path(__file__).resolve().parent/"Datos"

ratios= pd.read_csv(CARPETA_DATOS/"ratios.csv")
#print(ratios)

YEAR_DATOS =scoring.ultimo_year_completo(ratios)

NOMBRES_CRITERIOS={
    "crecimiento_ingresos": "Crecimiento",
    "margen_ebitda": "Margen EBITDA" ,
    "conversion_caja": "Conversión de caja",
    "deuda_neta_ebitda": "Deuda neta / EBITDA",
    "capex_ventas": "Capex / ventas",
    "ingresos": "Tamaño",
}

estilo_izquierda = {"backgroundColor": "white","padding": "15px","margin": "10px","border": "1px solid #dddddd","borderRadius": "5px","width": "30%"}
estilo_derecha={"backgroundColor": "white","padding": "15px","margin": "10px","border": "1px solid #dddddd","borderRadius": "5px", "width": "70%"}


def formato_porcentaje(valor):
    if pd.isna(valor):
        return "-"
    return str(round(valor * 100,1))+" %"


def crear_pregunta(clave):
    return html.Div(
        children=[
            html.P(scoring.PREGUNTAS[clave]),
            dcc.Slider(min=1, max=5, step=1,value =3,marks={1: "1",2: "2",3: "3",4: "4",5: "5"},id="slider_"+clave),
        ]
    )


preguntas= []
for clave in scoring.PREGUNTAS:
    preguntas.append(crear_pregunta(clave))

options_top= []
for n in [10,20,40]:
    options_top.append({"label": "Top "+str(n),"value": n})

app=Dash(__name__)
server=app.server

app.layout=html.Div(
    style={"fontFamily": "Arial","backgroundColor": "#f2f2f2"},
    children=[
        html.H1("Private Equity Screener",style={"textAlign": "center" ,"paddingTop": "15px"}),
        html.P("Ranking de empresas según tu tesis de inversión. Datos de la SEC, año "+str(YEAR_DATOS), style={"textAlign": "center"}),
        html.Div(
            style ={"display": "flex"} ,
            children=[
                html.Div(
                    style=estilo_izquierda,
                    children=[html.H3("Test del inversor")]+preguntas+[html.H3("Pesos"),html.Div(id= "texto_pesos")],
                ),
                html.Div(
                    style=estilo_derecha,
                    children=[
                        dcc.Dropdown(options=options_top,value=10,id="dropdown_top" , clearable=False,style = {"width": "200px"}),
                        dcc.Graph(id ="grafico_ranking"),
                        html.Div(id="tabla_ranking"),
                    ],
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("texto_pesos", "children"),
    Output("grafico_ranking","figure"),
    Output("tabla_ranking","children"),
    Input("slider_crecimiento","value"),
    Input("slider_caja","value"),
    Input("slider_deuda","value"),
    Input("slider_capex","value") ,
    Input("slider_tamano","value"),
    Input("dropdown_top" , "value"),
)
def actualizar(crecimiento,caja, deuda,capex, tamano,top):
    respuestas ={"crecimiento": crecimiento,"caja": caja,"deuda": deuda,"capex": capex,"tamano": tamano}
    pesos=scoring.test_a_pesos(respuestas)
    umbrales = scoring.test_a_umbrales(respuestas)
    ranking=scoring.puntuar(ratios, pesos,umbrales)
    mejores= ranking.head(top)
    # print(mejores)

    texto=[]
    for criterio in pesos:
        texto.append(html.P(NOMBRES_CRITERIOS[criterio]+": "+str(round(pesos[criterio] * 100))+" %"))

    fig=go.Figure()
    fig.add_trace(go.Bar(x=mejores["ticker"],y=mejores["score"],marker_color="#1f77b4"))
    fig.update_layout(title= "Score de 0 a 100",yaxis_range=[0, 100])

    filas=[html.Tr([html.Th("#"), html.Th("Ticker"), html.Th("Empresa"), html.Th("Score"), html.Th("Crecimiento"), html.Th("Margen EBITDA"), html.Th("Deuda")])]
    for i in range(len(mejores)):
        fila=mejores.iloc[i]
        if fila["cumple_deuda"]:
            deuda_texto="Cumple"
        else:
            deuda_texto ="Excede"
        filas.append(html.Tr([
            html.Td(str(fila["ranking"])),
            html.Td(fila["ticker"]),
            html.Td(fila["nombre"]),
            html.Td(str(fila["score"])) ,
            html.Td(formato_porcentaje(fila["crecimiento_ingresos"])) ,
            html.Td(formato_porcentaje(fila["margen_ebitda"])),
            html.Td(deuda_texto),
        ]))
    tabla = html.Table(filas ,style= {"width": "100%"})
    return texto,fig,tabla


if __name__=="__main__":
    app.run(debug = True)
