# TIC 2025

Este repositorio forma parte del proyecto de integración curricular titulado **“Aplicaciones de la modelización estadística espacio-temporal en ecología”**, desarrollado en la carrera de Matemática Aplicada (Facultad de Ciencias, EPN) por Danny Reina y Adriana Uquillas.

El objetivo principal es modelar la distribución geográfica de especies de la familia **Dendrobatidae** en el **Ecuador continental**, aplicando redes neuronales y técnicas modernas de generación de pseudoausencias, como:

- **Puntos aleatorios (Random Background)**
- **Puntos del grupo objetivo (Target Group Background)**

Se basa en el marco propuesto por [Zbinden et al., 2024], que incorpora una función de pérdida multicomponente (`full_weighted_loss`) ajustada para modelos multiespecie y datos sesgados geográficamente.

---

## Estructura del proyecto

Este repositorio está organizado por etapas del flujo de trabajo:

- **`Limpieza de datos/`**: Preprocesamiento y limpieza de datos de presencia de especies dendrobatidae en la región de interés.
- **`Clusterización Espacial/`**: Análisis espacial para identificación de regiones climáticas, para el entendimiento de la distribución de presencias sobre la región geográfica de interés.
- **`data/`**: Data auxiliar para la ejecución de varios scripts.
- **`Generación Files/`**: Scripts para la generación de archivos finales necesarios para la ejecución del modelo.
- **`SDM/`**: Implementación de red neuronal multiespecie.
- **`shinys/`**: Visualización interactiva de resultados y mapas usando R y Shiny.

Cada carpeta está documentada por separado para guiar al usuario en el uso y replicación del flujo completo.

## Limpieza de datos

Esta etapa consolida y limpia los registros de presencia de especies a partir de múltiples fuentes primarias de datos:

- **Bioweb (PUCE)**
- **Departamento de Biología de la EPN**
- **Global Biodiversity Information Facility (GBIF)**

### Principales tareas realizadas:

- **Lectura y filtrado de campos clave:** se seleccionan solo columnas relevantes como especie, coordenadas, fecha de colecta y taxonomía.
- **Estandarización taxonómica:** los nombres de especies son transformados a minúsculas y descompuestos cuando es necesario (ej. separar género y epíteto).
- **Eliminación de registros incompletos o inválidos:** se remueven filas sin coordenadas, sin especie o con datos inconsistentes.
- **Unificación de estructuras:** se homogeneiza el formato de columnas entre las diferentes fuentes de datos.
- **Tratamiento de duplicados:** se eliminan duplicados usando identificadores únicos como `catalogNumber` o `numeroMuseo`.

El resultado es un dataset consolidado y depurado, listo para ser usado en la generación de pseudoausencias, construcción de matrices de presencia-ausencia y entrenamiento de modelos.

## Clusterización Espacial

Esta etapa realiza una **segmentación del espacio geográfico** en regiones ecológicas similares mediante técnicas de **K-means clustering**. Sirve como análisis exploratorio previo a la modelización, ayudando a entender la variación ambiental en la región de estudio.

### Principales tareas realizadas:

- **Descarga de variables bioclimáticas** desde WorldClim para Ecuador, Perú, Colombia y Panamá.
- **Construcción de una grilla espacial regular** de celdas de 25 km² sobre el área de estudio.
- **Extracción de estadísticas promedio** (ej. temperatura, precipitación) por celda a partir de los rasters climáticos.
- **Estandarización de covariables** para aplicar K-means.
- **Segmentación ecológica con K-means (k=5)** basada en las variables climáticas.
- **Visualización de los clusters espaciales** en un mapa de grilla coloreado.

Esta agrupación permite posteriormente:
- Evaluar balance espacial de presencias/pseudoausencias.
- Interpretar patrones de distribución según condiciones ambientales.

