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



