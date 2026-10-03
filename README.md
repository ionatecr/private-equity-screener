# Private Equity Screener

**Ranking de empresas según tu tesis de inversión.** Aplicación web interactiva que traduce la tesis de un inversor en criterios cuantitativos, puntúa y ordena un universo de empresas y estima cómo pueden evolucionar sus métricas principales.

Proyecto de la asignatura *Desarrollo de Aplicaciones para la Visualización de Datos* (curso 2026-2027).

## Motivación

La motivación de este proyecto nace del trabajo que estoy desarrollando en mis prácticas en un search fund. El objetivo de un search fund es adquirir una empresa y, para ello, hay que llevar a cabo un proceso de análisis bastante exhaustivo. Esto implica consultar los estados financieros de cientos de compañías, calcular sus ingresos, márgenes EBITDA, CAPEX, conversión de caja, etc., y comparar cómo han evolucionado.

Actualmente, gran parte de este trabajo es bastante manual: hay que ir empresa por empresa, descargar o consultar los datos y después hacer los cálculos y comparaciones en hojas de cálculo. Esto hace que el proceso sea lento y también difícil de repetir siempre con los mismos criterios.

Además, una empresa no es buena o mala en sí misma, sino respecto a una determinada tesis de inversión. Un inversor que busca negocios value, estables y generadores de caja no va a valorar lo mismo que otro que busca empresas con un crecimiento elevado.

Existen plataformas como Bloomberg, Capital IQ o FactSet que cubren parte de este tipo de análisis, pero tienen licencias muy elevadas y están principalmente orientadas a empresas cotizadas. Para empresas privadas existen muchas menos herramientas que permitan hacer este análisis de forma conjunta. Por ejemplo, Sabi permite consultar empresas, pero principalmente de una en una.

Como los datos de las empresas privadas no son abiertos, las empresas cotizadas se utilizarán como universo de demostración. La idea es que la herramienta permita además subir un CSV con empresas privadas y aplicarles la misma tesis y los mismos criterios.

## Descripción

Para un inversor, una empresa no es buena o mala en abstracto: depende de la tesis de inversión que se esté utilizando. Una persona que busca un negocio estable y generador de caja puede dar mucha importancia a la conversión de caja o al nivel de deuda, mientras que alguien que busca crecimiento puede estar más interesado en la evolución de los ingresos.

Private Equity Screener parte de esta idea:

1. El usuario responde un **test de inversor**, en el que indica sus preferencias en aspectos como crecimiento frente a estabilidad, tamaño, tolerancia a la deuda, intensidad de capex y horizonte de inversión.
2. El test se traduce en **pesos y umbrales** para los diferentes criterios. Estos parámetros se pueden modificar después mediante controles deslizantes.
3. La aplicación calcula un **score de 0 a 100** para cada empresa, mostrando también qué aporta cada criterio al resultado final, y genera un ranking.
4. Los modelos de predicción estiman el **margen EBITDA y el crecimiento de ingresos del año siguiente**. Además, un **backtest** permite comprobar cómo habría funcionado la tesis utilizando datos históricos.

Las métricas utilizadas serán ingresos, EBITDA, margen EBITDA, CAPEX, caja, flujo de caja libre después de impuestos y deuda neta sobre EBITDA. Estas métricas son aplicables tanto a empresas cotizadas como privadas, por lo que el mismo framework se puede utilizar posteriormente con los datos de un CSV propio.

## Objetivos

- Convertir una tesis de inversión en criterios cuantitativos mediante un test inicial.
- Puntuar y ordenar un universo de empresas con un score transparente y fácil de entender.
- Estimar la evolución del margen EBITDA y del crecimiento de ingresos del año siguiente.
- Comparar los modelos de predicción con un modelo ingenuo de persistencia para comprobar si realmente aportan una mejora.
- Entregar una aplicación desplegada en una URL pública.
- Mantener el código estructurado y actualizado durante todo el desarrollo del proyecto.

## Alcance

- **Incluye:** universo de empresas cotizadas con datos de los últimos diez años, score por tesis, ficha de empresa, comparador de tesis, predicción, backtest y carga de CSV.
- **No incluye:** valoración por precio de mercado, análisis cualitativo, recomendaciones de compra ni negociación de valores.

## Datos

- **SEC EDGAR** (`data.sec.gov`, *Company Facts*, datos XBRL): API pública, gratuita y sin clave. Tiene un límite de 10 peticiones por segundo y requiere una cabecera `User-Agent`, por lo que los datos se guardarán en caché local.
- Listado de tickers y sectores de la propia SEC.
- Refresco automático mediante una tarea programada en GitHub Actions.

## Arquitectura

```text
SEC EDGAR  ->  Pipeline pandas  ->  Scoring y modelos  ->  API Flask  ->  App Dash (Render)
(XBRL)         (limpieza, ratios)   (scikit-learn)         /score /predict
```

- **Pipeline:** normalización de etiquetas XBRL, cálculo de ratios, filtro de empresas con al menos seis años de datos, tratamiento de nulos y valores extremos y construcción de una tabla de panel empresa-año.
- **Ratios:** EBITDA como resultado de explotación más amortizaciones y flujo de caja libre como caja operativa menos CAPEX.
- **Score:** percentil de cada criterio dentro del universo o del sector, criterios eliminatorios y combinación ponderada.
- **Modelo principal:** modelo de panel con Ridge y GradientBoosting, utilizando variables retrasadas, validación temporal y comparación con un modelo ingenuo.
- **Ampliaciones previstas:** agrupación con K-means, detección de anomalías con Isolation Forest y backtest de la tesis.
- **Aplicación:** Dash con pestañas de test y tesis, ranking con radar, ficha de empresa, comparador, backtest y carga de CSV. La aplicación consumirá la API Flask.

## Estructura prevista del repositorio

```text
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

Durante todo el semestre habrá commits y actualizaciones periódicas, además de mejoras continuas del proyecto.

## Cómo ejecutarlo

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Riesgos

- **Datos XBRL incompletos o inconsistentes entre empresas:** se normalizan los datos y se excluyen las empresas que no alcanzan el mínimo de histórico.
- **Capacidad predictiva limitada con pocos años por empresa:** se utiliza un modelo de panel y se compara con un modelo ingenuo para que la mejora real sea explícita.
- **Límites de uso de la API:** se utiliza caché local y se controlan las peticiones para evitar descargas innecesarias.
