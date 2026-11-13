import base64
import io
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input,Output,State, ctx,dcc, html
from plotly.subplots import make_subplots

import scoring
from api import crear_api
from ratios import calcular_ratios

CARPETA_DATOS = Path(__file__).resolve().parent/"Datos"

ratios= pd.read_csv(CARPETA_DATOS/"ratios.csv")
#print(ratios)
predicciones=pd.read_csv(CARPETA_DATOS/"predicciones.csv")

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


def formato_veces(valor):
    if pd.isna(valor):
        return "-"
    valor=round(valor,1)
    if valor==0:
        valor=0.0
    return str(valor)+"x"


def formato_millones(valor):
    if pd.isna(valor):
        return "-"
    return str(round(valor/1000000))+" M"


def puntuar_csv(ratios_csv,respuestas):
    year =YEAR_DATOS
    universo=ratios[ratios["year"]==year].copy()
    universo["origen"]="Cotizada"
    nuevas=ratios_csv.sort_values("year").groupby("ticker").tail(1).copy()
    nuevas["year_original"]=nuevas["year"]
    nuevas["year"]=year
    nuevas["origen"]="CSV"
    juntas=pd.concat([universo, nuevas])
    ranking=scoring.ranking_respuestas(juntas, respuestas,year)
    return ranking


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

options_empresas=[]
for ticker in sorted(ratios["ticker"].unique()):
    nombre=ratios[ratios["ticker"]==ticker]["nombre"].iloc[0]
    options_empresas.append({"label": ticker+" - "+nombre,"value": ticker})

options_tesis =[
    {"label": "Tesis Value","value": "Value"},
    {"label": "Tesis Growth","value": "Growth"},
    {"label": "Mi tesis","value": "Mi tesis"},
]

options_top= []
for n in [10,20,40]:
    options_top.append({"label": "Top "+str(n),"value": n})

app=Dash(__name__)
server=app.server

crear_api(server)

app.layout=html.Div(
    style={"fontFamily": "Arial","backgroundColor": "#f2f2f2"},
    children=[
        html.H1("Private Equity Screener",style={"textAlign": "center" ,"paddingTop": "15px"}),
        html.P("Ranking de empresas según tu tesis de inversión. Datos de la SEC, año "+str(YEAR_DATOS), style={"textAlign": "center"}),
        dcc.Tabs(children =[
        dcc.Tab(label="Ranking",children=[
        html.Div(
            style ={"display": "flex"} ,
            children=[
                html.Div(
                    style=estilo_izquierda,
                    children=[html.H3("Test del inversor"),html.Div([html.Button("Value" ,id ="boton_value", n_clicks=0), html.Button("Growth",id="boton_growth",n_clicks=0),html.Button("Neutra",id="boton_neutra",n_clicks = 0)])]+preguntas+[html.H3("Pesos"),html.Div(id= "texto_pesos")],
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
        ]),
        dcc.Tab(label ="Ficha de empresa" , children=[
            html.Div(
                style={"backgroundColor": "white","padding": "15px","margin": "10px", "border": "1px solid #dddddd","borderRadius": "5px"},
                children=[
                    dcc.Dropdown(options =options_empresas, value="AAPL",id= "dropdown_empresa",clearable=False,style={"width": "400px"}),
                    html.Div(id="datos_empresa",style = {"display": "flex","justifyContent": "space-around","marginTop": "15px"}),
                    dcc.Graph(id="grafico_empresa"),
                ],
            ) ,
        ]),
        dcc.Tab(label="Comparar tesis",children = [
            html.Div(
                style={"backgroundColor": "white","padding": "15px","margin": "10px", "border": "1px solid #dddddd","borderRadius": "5px"},
                children=[
                    html.Div(style={"display": "flex"}, children=[
                        dcc.Dropdown(options= options_tesis,value="Value",id="dropdown_tesis_1",clearable= False,style={"width": "250px","marginRight": "20px"}),
                        dcc.Dropdown(options = options_tesis,value="Growth",id="dropdown_tesis_2", clearable=False,style={"width": "250px"}),
                    ]),
                    html.Div(id="texto_comparar",style= {"marginTop": "15px"}),
                    dcc.Graph(id="grafico_comparar"),
                ],
            ) ,
        ]),
        dcc.Tab(label="Backtest",children=[
            html.Div(
                style={"backgroundColor": "white","padding": "15px","margin": "10px", "border": "1px solid #dddddd","borderRadius": "5px"},
                children=[
                    html.P("Cada año se cogen las 10 mejores empresas con tu tesis y se mira qué pasó al año siguiente, comparado con la mediana de todas.") ,
                    html.Div(id="texto_backtest"),
                    dcc.Graph(id="grafico_backtest"),
                ],
            ) ,
        ]),
        dcc.Tab(label ="Tus empresas", children=[
            html.Div(
                style={"backgroundColor": "white","padding": "15px","margin": "10px", "border": "1px solid #dddddd","borderRadius": "5px"},
                children=[
                    html.P("Sube un CSV con tus empresas privadas (columnas: ticker, nombre, year, ingresos, ebit, amortizacion, capex, flujo_operativo, caja, deuda) y se puntúan junto a las cotizadas."),
                    dcc.Upload(
                        id="subir_csv",
                        children=html.Div(["Arrastra aquí tu CSV o ",html.A("elígelo")]),
                        style={"width": "100%" , "height": "60px","lineHeight": "60px" ,"borderWidth": "1px","borderStyle": "dashed","borderRadius": "5px","textAlign": "center"},
                    ),
                    html.P(["¿No tienes uno? ", html.A("Descarga la plantilla",href="/assets/plantilla_privadas.csv",download= "plantilla_privadas.csv")]),
                    html.Div(id = "resultado_csv") ,
                ],
            ) ,
        ]),
        ]),
    ],
)


@app.callback(
    Output("slider_crecimiento","value"),
    Output("slider_caja" ,"value"),
    Output("slider_deuda","value"),
    Output("slider_capex", "value"),
    Output("slider_tamano", "value"),
    Input("boton_value","n_clicks"),
    Input("boton_growth","n_clicks"),
    Input("boton_neutra", "n_clicks"),
    prevent_initial_call = True,
)
def elegir_tesis(n_value, n_growth,n_neutra):
    if ctx.triggered_id=="boton_value":
        respuestas=scoring.TESIS["Value"]
    elif ctx.triggered_id== "boton_growth":
        respuestas=scoring.TESIS["Growth"]
    else:
        respuestas={"crecimiento": 3, "caja": 3,"deuda": 3,"capex": 3,"tamano": 3}
    return respuestas["crecimiento"], respuestas["caja"], respuestas["deuda"], respuestas["capex"], respuestas["tamano"]


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
    for criterio in NOMBRES_CRITERIOS:
        fig.add_trace(go.Bar(x=mejores["ticker"],y=mejores["aporte_"+criterio],name=NOMBRES_CRITERIOS[criterio]))
    fig.update_layout(title= "Score de 0 a 100 (lo que aporta cada criterio)",yaxis_range=[0, 100],barmode="stack")

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


@app.callback(
    Output("datos_empresa", "children"),
    Output("grafico_empresa","figure"),
    Input("dropdown_empresa","value"),
)
def ficha_empresa(ticker):
    df=ratios[ratios["ticker"]==ticker]
    if YEAR_DATOS in list(df["year"]):
        ultima=df[df["year"]==YEAR_DATOS].iloc[0]
    else:
        ultima= df[df["year"]==df["year"].max()].iloc[0]
    prediccion= predicciones[predicciones["ticker"]== ticker]
    datos=[
        html.Div([html.P("Ingresos "+str(ultima["year"])), html.H3(formato_millones(ultima["ingresos"]))]),
        html.Div([html.P("Crecimiento"),html.H3(formato_porcentaje(ultima["crecimiento_ingresos"]))]),
        html.Div([html.P("Margen EBITDA"),html.H3(formato_porcentaje(ultima["margen_ebitda"]))]),
        html.Div([html.P("Deuda neta / EBITDA"),html.H3(formato_veces(ultima["deuda_neta_ebitda"]))]),
    ]
    fig=make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df["year"], y = df["ingresos"]/1000000 , name= "Ingresos (M USD)"),secondary_y=False)
    fig.add_trace(go.Scatter(x = df["year"],y = df["margen_ebitda"] * 100,name="Margen EBITDA (%)",mode = "lines+markers"),secondary_y = True)
    if len(prediccion) > 0:
        year_pred=prediccion["year_prediccion"].iloc[0]
        margen_pred=prediccion["pred_margen_ebitda"].iloc[0]
        fig.add_trace(go.Scatter(x=[year_pred],y=[margen_pred * 100], name="Margen previsto (%)",mode="markers" , marker=dict(size=12, symbol="star")), secondary_y=True)
        datos.append(html.Div([html.P("Margen previsto "+str(year_pred)) , html.H3(formato_porcentaje(margen_pred))]))
    fig.update_layout(title=ticker+": ingresos y margen EBITDA")
    return datos,fig


@app.callback(
    Output("texto_comparar" , "children"),
    Output("grafico_comparar", "figure"),
    Input("dropdown_tesis_1","value"),
    Input("dropdown_tesis_2","value"),
    Input("slider_crecimiento","value"),
    Input("slider_caja","value"),
    Input("slider_deuda","value"),
    Input("slider_capex","value") ,
    Input("slider_tamano","value"),
)
def comparar_tesis(tesis_1,tesis_2,crecimiento, caja,deuda ,capex,tamano):
    mi_tesis= {"crecimiento": crecimiento, "caja": caja,"deuda": deuda,"capex": capex, "tamano": tamano}
    if tesis_1=="Mi tesis":
        respuestas_1=mi_tesis
    else:
        respuestas_1 = scoring.TESIS[tesis_1]
    if tesis_2=="Mi tesis":
        respuestas_2 =mi_tesis
    else:
        respuestas_2=scoring.TESIS[tesis_2]
    ranking_1= scoring.ranking_respuestas(ratios,respuestas_1)
    ranking_2=scoring.ranking_respuestas(ratios,respuestas_2)
    juntos=ranking_1[["ticker", "ranking"]].merge(ranking_2[["ticker","ranking"]], on="ticker",suffixes=("_1","_2"))
    juntos["salto"]= juntos["ranking_1"]-juntos["ranking_2"]
    en_comun= 0
    top_2=list(ranking_2["ticker"].head(10))
    for ticker in ranking_1["ticker"].head(10):
        if ticker in top_2:
            en_comun=en_comun+1
    mayor_subida=juntos.sort_values("salto",ascending=False).iloc[0]
    mayor_bajada=juntos.sort_values("salto").iloc[0]
    texto=[
        html.P("Empresas en común en el top 10: "+str(en_comun)+" de 10"),
        html.P("La que más sube con "+tesis_2+": "+mayor_subida["ticker"]+" (del "+str(mayor_subida["ranking_1"])+" al "+str(mayor_subida["ranking_2"])+")"),
        html.P("La que más baja con "+tesis_2+": "+mayor_bajada["ticker"]+" (del "+str(mayor_bajada["ranking_1"])+" al "+str(mayor_bajada["ranking_2"])+")"),
    ]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x = juntos["ranking_1"], y=juntos["ranking_2"],text=juntos["ticker"],mode="markers+text",textposition= "top center"))
    fig.update_xaxes(title="Puesto con "+tesis_1, autorange="reversed")
    fig.update_yaxes(title = "Puesto con "+tesis_2,autorange="reversed")
    fig.update_layout(height=550)
    return texto,fig


@app.callback(
    Output("texto_backtest","children"),
    Output("grafico_backtest", "figure"),
    Input("slider_crecimiento","value"),
    Input("slider_caja","value"),
    Input("slider_deuda","value"),
    Input("slider_capex","value") ,
    Input("slider_tamano","value"),
)
def hacer_backtest(crecimiento,caja, deuda,capex, tamano):
    respuestas ={"crecimiento": crecimiento,"caja": caja,"deuda": deuda,"capex": capex,"tamano": tamano}
    pesos=scoring.test_a_pesos(respuestas)
    umbrales = scoring.test_a_umbrales(respuestas)
    resultado=scoring.backtest(ratios, pesos, umbrales)
    resultado= resultado.dropna()
    #print(resultado)
    gana = 0
    for i in range(len(resultado)):
        if resultado["crecimiento_top"].iloc[i] > resultado["crecimiento_universo"].iloc[i]:
            gana=gana+1
    diferencia_crecimiento=(resultado["crecimiento_top"]-resultado["crecimiento_universo"]).mean()
    diferencia_margen=(resultado["margen_top"]-resultado["margen_universo"]).mean()
    texto=[
        html.P("Años en que tu top 10 creció más que la mediana: "+str(gana)+" de "+str(len(resultado))),
        html.P("Crecimiento extra medio: "+formato_porcentaje(diferencia_crecimiento)),
        html.P("Margen EBITDA extra medio: "+formato_porcentaje(diferencia_margen)),
    ]
    fig=make_subplots(rows=1,cols=2,subplot_titles= ["Crecimiento al año siguiente (%)","Margen EBITDA al año siguiente (%)"])
    fig.add_trace(go.Bar(x=resultado["year"],y=resultado["crecimiento_top"] * 100,name="Top 10 de tu tesis", marker_color="#1f77b4"),row =1 ,col =1)
    fig.add_trace(go.Bar(x = resultado["year"],y= resultado["crecimiento_universo"] * 100,name="Mediana de todas", marker_color="#aaaaaa"),row=1,col = 1)
    fig.add_trace(go.Bar(x=resultado["year"],y=resultado["margen_top"] * 100,name="Top 10 de tu tesis",marker_color ="#1f77b4",showlegend=False),row=1 ,col=2)
    fig.add_trace(go.Bar(x=resultado["year"],y=resultado["margen_universo"] * 100,name="Mediana de todas",marker_color="#aaaaaa",showlegend =False),row=1,col= 2)
    fig.update_layout(barmode="group",height=450)
    return texto,fig


@app.callback(
    Output("resultado_csv","children"),
    Input("subir_csv" ,"contents"),
    Input("slider_crecimiento","value"),
    Input("slider_caja","value"),
    Input("slider_deuda","value"),
    Input("slider_capex","value") ,
    Input("slider_tamano","value"),
    State("subir_csv","filename"),
)
def subir_csv(contenido,crecimiento,caja, deuda,capex, tamano,nombre_archivo):
    if contenido is None:
        return ""
    tipo,texto_base64=contenido.split(",")
    try:
        texto_csv=base64.b64decode(texto_base64).decode("utf-8")
        df= pd.read_csv(io.StringIO(texto_csv))
    except Exception:
        return html.P("No se ha podido leer "+str(nombre_archivo)+", tiene que ser un CSV.")
    for columna in ["ticker","year","ingresos"]:
        if columna not in df.columns:
            return html.P("Falta la columna "+columna+". Mira la plantilla.")
    respuestas ={"crecimiento": crecimiento,"caja": caja,"deuda": deuda,"capex": capex,"tamano": tamano}
    ratios_csv= calcular_ratios(df)
    ranking=puntuar_csv(ratios_csv,respuestas)
    privadas=ranking[ranking["origen"]== "CSV"]
    textos=[]
    for i in range(len(privadas)):
        fila=privadas.iloc[i]
        textos.append(html.H4(fila["nombre"]+": "+str(fila["score"])+" puntos, puesto "+str(fila["ranking"])+" de "+str(len(ranking))))
    filas=[html.Tr([html.Th("#"), html.Th("Ticker"),html.Th("Empresa"), html.Th("Score"),html.Th("Crecimiento"),html.Th("Margen EBITDA")])]
    for i in range(len(ranking)):
        fila=ranking.iloc[i]
        if fila["origen"]=="CSV":
            estilo_fila={"backgroundColor": "#fff3c4","fontWeight": "bold"}
        else:
            estilo_fila={}
        filas.append(html.Tr(style=estilo_fila ,children=[
            html.Td(str(fila["ranking"])),
            html.Td(fila["ticker"]),
            html.Td(fila["nombre"]),
            html.Td(str(fila["score"])) ,
            html.Td(formato_porcentaje(fila["crecimiento_ingresos"])) ,
            html.Td(formato_porcentaje(fila["margen_ebitda"])),
        ]))
    return html.Div(textos+[html.Table(filas,style={"width": "100%"})])


if __name__=="__main__":
    app.run(debug = True)
