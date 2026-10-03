# Private Equity Screener

**Ranking de empresas según tu tesis de inversión.** Aplicación web interactiva que traduce la tesis de un inversor en criterios cuantitativos, puntúa y ordena un universo de empresas, y estima cómo evolucionarán sus métricas clave.

Proyecto de la asignatura *Desarrollo de Aplicaciones para la Visualización de Datos* (curso 2026-2027).

## Motivación

La motivación de este proyecto nace del trabajo que estoy desarrollando en mis prácticas en un search fund. El objetivo de un search fund es adquirir una empresa, y para ello hay que llevar a cabo un proceso de análisis exhaustivo que resulta tedioso y muy manual: consultar los estados financieros de cientos de compañías, calcular sus ingresos, márgenes EBITDA, CAPEX y conversión de caja, y comparar todas estas evoluciones en hojas de cálculo. Es un trabajo lento y difícil de repetir con criterios consistentes.

Una empresa no es buena o mala en sí, sino respecto a una tesis de inversión (por ejemplo, negocios value, estables y generadores de caja, frente a negocios growth, orientados al crecimiento). Plataformas como Bloomberg, Capital IQ o FactSet cubren este terreno, pero con licencias muy elevadas y orientadas a empresas cotizadas, y apenas existen screeners que permitan ordenar empresas privadas, ya que herramientas como Sabi solo permiten buscarlas una a una.

Como los datos de las empresas privadas no son abiertos, las empresas cotizadas servirán como universo de demostración, y la herramienta permitirá subir un CSV con empresas privadas para puntuarlas con la misma tesis.

## Descripción

Para un inversor, una empresa no es buena o mala en abstracto: lo es respecto a su tesis de inversión. Quien busca un negocio estable y generador de caja no valora lo mismo que quien persigue crecimiento.

Private Equity Screener parte de esa idea:

1. El usuario responde un **test de inversor** (crecimiento frente a estabilidad, tamaño, tolerancia a la deuda, intensidad de capex, horizonte).
2. El test se traduce en **pesos y umbrales** que se pueden ajustar con controles deslizantes.
3. La app calcula un **score de 0 a 100** por empresa, con el desglose de lo que aporta cada criterio, y devuelve un **ranking**.
4. Modelos de predicción estiman el **margen EBITDA y el crecimiento de ingresos del año siguiente**, y un **backtest** comprueba cómo habría funcionado la tesis en el pasado.

Las métricas (ingresos, EBITDA, margen EBITDA, capex, caja, flujo de caja libre después de impuestos, deuda neta sobre EBITDA) son las mismas para una empresa cotizada que para una privada, por lo que el marco sirve también para private equity. La aplicación permitirá subir un CSV propio con la misma estructura.

## Objetivos

- Convertir una tesis de inversión en criterios cuantitativos mediante un test inicial.
- Puntuar y ordenar un universo de empresas con un score transparente y explicable.
- Estimar la evolución del próximo año con modelos de predicción y medir cuánto mejoran a un modelo ingenuo de persistencia.
- Entregar una aplicación desplegada en una URL pública, con código estructurado y actualizado de forma continua.

## Alcance

- **Incluye:** universo de empresas cotizadas con datos de los últimos diez años, score por tesis, ficha de empresa, comparador de tesis, predicción, backtest y carga de CSV.
- **No incluye:** valoración por precio de mercado, análisis cualitativo, recomendaciones de compra ni negociación de valores.

## Datos

- **SEC EDGAR** (`data.sec.gov`, *company facts*, datos XBRL): API pública, gratuita y sin clave. Límite de 10 peticiones por segundo y cabecera `User-Agent` obligatoria, por lo que los datos se guardan en caché local.
- Listado de tickers y sectores de la propia SEC.
- Refresco automático con una tarea programada en GitHub Actions.

## Arquitectura

```
SEC EDGAR  ->  Pipeline pandas  ->  Scoring y modelos  ->  API Flask  ->  App Dash (Render)
(XBRL)         (limpieza, ratios)   (scikit-learn)         /score /predict
```

- **Pipeline:** normalización de etiquetas XBRL, cálculo de ratios (EBITDA como resultado de explotación más amortizaciones; flujo de caja libre como caja operativa menos capex), filtro de empresas con al menos seis años de datos, tratamiento de nulos y valores extremos, tabla de panel empresa-año.
- **Score:** percentil de cada criterio dentro del universo o sector, criterios eliminatorios y combinación ponderada.
- **Modelo principal:** modelo de panel (Ridge y GradientBoosting) con variables retrasadas, validación temporal y comparación con un modelo ingenuo.
- **Ampliaciones previstas:** agrupación con K-means, detección de anomalías con Isolation Forest y backtest de la tesis.
- **Aplicación:** Dash con pestañas (test y tesis, ranking con radar, ficha de empresa, comparador, backtest, carga de CSV) que consume la API Flask.

## Estructura prevista del repositorio

```
private-equity-screener/
├── data/                # caché de datos (no versionada) y datos de ejemplo
├── notebooks/           # análisis exploratorio
├── src/
│   ├── data/            # descarga y normalización desde EDGAR
│   ├── features/        # ratios y tabla de panel
│   ├── scoring/         # test de inversor y score
│   ├── models/          # entrenamiento y predicción
│   ├── api/             # API Flask
│   └── app/             # aplicación Dash (layout, callbacks, assets)
├── tests/               # pruebas con pytest
├── .github/workflows/   # CI y refresco de datos
├── requirements.txt
└── README.md
```

## Plan de trabajo inicial

| Fechas | Hitos |
|---|---|
| 5 oct | Propuesta en PDF y repositorio creado con este README |
| 6 – 19 oct | Pipeline de datos desde EDGAR, ratios y análisis exploratorio. Prueba intertrimestral (19 oct) |
| 20 oct – 2 nov | Scoring, test de inversor y primera versión de la app Dash en local |
| 3 – 9 nov | API Flask y modelo predictivo con validación temporal. Primer despliegue en Render (versión mínima) |
| 10 – 23 nov | Backtest, alertas, agrupación, pruebas, integración continua y mejoras de diseño e interacción |
| 24 – 30 nov | Ensayo y presentación de la aplicación (26 y 30 nov) |

Durante todo el semestre: commits y actualizaciones periódicas, y mejora continua del proyecto.

## Cómo ejecutarlo

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Riesgos

- **Datos XBRL incompletos o inconsistentes entre empresas:** se normalizan y se excluyen las que no alcanzan el mínimo de histórico.
- **Capacidad predictiva limitada con pocos años por empresa:** se usa un modelo de panel y se compara con un modelo ingenuo para que la mejora real sea explícita.
- **Límites de uso de la API:** caché local y peticiones moderadas.
