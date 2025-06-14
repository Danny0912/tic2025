# app.R
library(shiny)
library(leaflet)
library(sf)
library(readr)
library(dplyr)
library(shinyWidgets)
library(bslib)          # Para theming y layout moderno
library(shinycssloaders) # Para indicadores de carga
library(htmltools)       # Para htmlEscape

# --- Configuración Inicial ---
# Asegúrate de que estos archivos están en una carpeta 'www' junto a app.R
data_path <- "www/data_combinada_final.csv"
grid_path <- "www/grid_clima.geojson"

# --- Carga y Preparación de Datos ---
tryCatch({
  especies <- read_csv(data_path)
  # Asegúrate de que la columna 'fecha' es de tipo Date
  if (!inherits(especies$fecha, "Date")) {
    especies$fecha <- as.Date(especies$fecha)
  }
  # Validar columnas necesarias
  stopifnot(all(c("longitud", "latitud", "especie", "fecha") %in% names(especies)))
  
  grid_clima <- st_read(grid_path)
  stopifnot(inherits(grid_clima, "sf"), "cluster" %in% names(grid_clima))
  
  # Asegurar que el CRS sea WGS84 (EPSG:4326)
  grid_clima <- st_transform(grid_clima, crs = 4326)
  grid_clima$cluster <- factor(grid_clima$cluster)
  
  
  # Convertir especies a objeto espacial (manejando NA en coordenadas)
  especies_sf <- especies %>%
    filter(!is.na(longitud) & !is.na(latitud)) %>%
    st_as_sf(coords = c("longitud", "latitud"), crs = 4326, na.fail = FALSE)
  
  # Validar que la conversión fue exitosa
  if (nrow(especies_sf) == 0 && nrow(especies) > 0) {
    stop("No se pudieron convertir las coordenadas de las especies a formato espacial.")
  }
  
  # Definir opciones iniciales para filtros
  initial_species <- sort(unique(especies_sf$especie))
  min_date <- min(especies_sf$fecha, na.rm = TRUE)
  max_date <- max(especies_sf$fecha, na.rm = TRUE)
  
  # Usamos levels(grid_clima$cluster) que devuelve los niveles únicos SIN incluir NA.
  paleta_clusters <- colorFactor(palette = "viridis",
                                 domain = levels(grid_clima$cluster), # Usar los niveles del factor
                                 na.color = "#A0A0A0") # Gris para NAs
  
  
}, error = function(e) {
  # Si hay un error al cargar datos, muestra un mensaje y detiene la app
  stop(paste("Error al cargar o procesar los datos:", e$message))
})


# --- UI (Interfaz de Usuario) ---
ui <- page_sidebar(
  title = "Mapa de Clusters Climáticos y Especies",
  theme = bs_theme(version = 5, bootswatch = "flatly"), # Elige un tema de Bootswatch
  
  sidebar = sidebar(
    title = "Filtros",
    # Usar pickerInput para mejor selección múltiple
    pickerInput("especie_seleccionada",
                "Selecciona especies:",
                choices = initial_species,
                selected = initial_species, # mostrar todo al inicio
                multiple = TRUE,
                options = pickerOptions(
                  actionsBox = TRUE, # Botones Seleccionar/Deseleccionar todo
                  liveSearch = TRUE, # Habilitar búsqueda
                  deselectAllText = "Ninguna",
                  selectAllText = "Todas",
                  noneSelectedText = "No hay selección"
                )),
    
    dateRangeInput("fecha_rango",
                   "Selecciona rango de fechas:",
                   start = min_date,
                   end = max_date,
                   min = min_date,
                   max = max_date,
                   format = "yyyy-mm-dd",
                   separator = " a "),
    
    actionButton("reset", "Resetear Filtros", icon = icon("refresh"), class = "btn-secondary") # Estilo del botón
  ),
  
  # Ajusta el valor '100px' si el header/footer ocupa más o menos espacio
  withSpinner(leafletOutput("mapa", width = "100%", height = "calc(100vh - 100px)"), type = 6, color = "#0dcaf0")
)

# --- Server (Lógica de la Aplicación) ---
server <- function(input, output, session) {
  
  # --- Datos Reactivos ---
  especies_filtradas_r <- reactive({
    # Depender de los inputs
    req(input$especie_seleccionada, input$fecha_rango)
    
    # Filtrar basado en la selección actual
    especies_sf %>%
      filter(
        especie %in% input$especie_seleccionada,
        fecha >= input$fecha_rango[1],
        fecha <= input$fecha_rango[2]
      )
  })
  
  # --- Renderizado Inicial del Mapa ---
  output$mapa <- renderLeaflet({
    leaflet(options = leafletOptions(minZoom = 2)) %>%
      # Añadir varias capas base
      addProviderTiles(providers$CartoDB.PositronNoLabels, group = "Claro") %>%
      addProviderTiles(providers$CartoDB.DarkMatterNoLabels, group = "Oscuro") %>%
      addProviderTiles(providers$Esri.WorldImagery, group = "Satélite") %>%
      
      # Añadir clusters climáticos (con estilo más visible)
      addPolygons(data = grid_clima,
                  fillColor = ~paleta_clusters(cluster), # Usa la paleta corregida
                  fillOpacity = 0.7,
                  color = "black",
                  weight = 0.5, ### CORRECCIÓN MENOR: Reduje un poco el grosor del borde para que no domine
                  smoothFactor = 0.5,
                  highlightOptions = highlightOptions(
                    weight = 2, # Resaltado más sutil
                    color = "#FFFFFF",
                    fillOpacity = 0.9, # Un poco más opaco al resaltar
                    bringToFront = TRUE),
                  # Muestra info al pasar el mouse
                  label = ~paste("Cluster:", ifelse(is.na(cluster), "NA", as.character(cluster))), # Muestra NA si es NA
                  # popup = ~paste("Cluster:", ifelse(is.na(cluster), "NA", as.character(cluster))), # O usa popup
                  group = "Clusters Climáticos",
                  layerId = ~paste0("cluster_", row.names(grid_clima))) %>% # ID único asegurado
      
      # Añadir leyenda de clusters
      addLegend(position = "bottomright",
                pal = paleta_clusters,
                values = grid_clima$cluster, # 'values' debe tener todos los datos (incluyendo NA) para que la leyenda se muestre bien
                title = "Clusters Climáticos",
                opacity = 0.8,
                layerId = "cluster_legend",
                group = "Clusters Climáticos",
                na.label = "NA") %>% # Etiqueta para el color NA en la leyenda
      
      # Añadir control de capas (incluyendo capas base)
      addLayersControl(
        baseGroups = c("Claro", "Oscuro", "Satélite"),
        overlayGroups = c("Clusters Climáticos", "Especies"),
        options = layersControlOptions(collapsed = FALSE) # Mantener desplegado
      ) %>%
      
      # Añadir escala gráfica
      addScaleBar(position = "bottomleft")
  })
  
  # --- Observador para Actualizar Especies en el Mapa ---
  observe({
    data_filtrada <- especies_filtradas_r()
    
    # Proxy para interactuar con el mapa existente sin redibujarlo
    map_proxy <- leafletProxy("mapa", session)
    
    # Limpiar marcadores y leyenda de especies anteriores
    map_proxy %>% clearGroup("Especies") %>% removeControl("species_legend")
    
    # Solo añadir puntos y leyenda si hay datos filtrados
    if (nrow(data_filtrada) > 0) {
      # Crear paleta solo con las especies presentes en los datos filtrados
      paleta_especies_filtradas <- colorFactor(palette = "Set2", domain = data_filtrada$especie)
      
      map_proxy %>%
        addCircleMarkers(data = data_filtrada,
                         radius = 5,
                         color = ~paleta_especies_filtradas(especie),
                         stroke = FALSE,
                         fillOpacity = 0.8,
                         popup = ~paste("<b>Especie:</b>", htmlEscape(especie), "<br>",
                                        "<b>Fecha:</b>", format(fecha, "%Y-%m-%d")),
                         group = "Especies",
                         layerId = ~paste0("sp_", row.names(data_filtrada))) %>% # ID único por punto prefijado
        # Añadir leyenda de especies (con layerId para poder borrarla)
        addLegend(position = "bottomleft", # Cambiar posición si solapa mucho con escala
                  pal = paleta_especies_filtradas,
                  values = data_filtrada$especie,
                  title = "Especies",
                  opacity = 1,
                  layerId = "species_legend",
                  group = "Especies") # Agrupar leyenda con su capa
      
      # Calcular límites y hacer zoom/pan (flyToBounds)
      tryCatch({
        # Asegurarse que hay más de un punto único para formar un bounding box válido
        unique_geoms <- unique(st_geometry(data_filtrada))
        if(length(unique_geoms) > 1) {
          bbox <- st_bbox(data_filtrada)
          # Añadir un pequeño padding al bbox
          padding_factor <- 0.05
          width <- bbox[["xmax"]] - bbox[["xmin"]]
          height <- bbox[["ymax"]] - bbox[["ymin"]]
          # Evitar error si width o height son 0 (todos los puntos son iguales)
          if (width == 0 && height == 0 && length(unique_geoms) == 1) {
            coords <- st_coordinates(data_filtrada[1,])
            map_proxy %>% flyTo(lng = coords[1,1], lat = coords[1,2], zoom = 10)
          } else {
            # Asegurar que el padding no cree un bbox inválido si w o h son muy pequeños
            padding_lon <- max(width * padding_factor, 0.01) # Mínimo padding
            padding_lat <- max(height * padding_factor, 0.01) # Mínimo padding
            map_proxy %>% flyToBounds(
              bbox[["xmin"]] - padding_lon,
              bbox[["ymin"]] - padding_lat,
              bbox[["xmax"]] + padding_lon,
              bbox[["ymax"]] + padding_lat
            )
          }
        } else if (nrow(data_filtrada) >= 1) {
          # Si solo hay un punto único (o varios puntos en la misma ubicación)
          coords <- st_coordinates(data_filtrada[1,])
          map_proxy %>% flyTo(lng = coords[1,1], lat = coords[1,2], zoom = 10) # Ajusta el zoom
        }
        
        
      }, error = function(e) {
        # Manejar error si no se puede calcular bbox o volar
        cat("Error calculando límites o flyToBounds:", e$message, "\n")
        showNotification(paste("Error al ajustar el zoom:", e$message), type = "warning")
      })
      
      
    } else {
      # Si no hay datos, mostrar una notificación
      showNotification("No se encontraron especies con los filtros seleccionados.", type = "message", duration = 5)
    }
  })
  
  # --- Observador para Resetear Filtros ---
  observeEvent(input$reset, {
    # Resetear los inputs a sus valores iniciales
    updatePickerInput(session, "especie_seleccionada", selected = initial_species)
    updateDateRangeInput(session, "fecha_rango", start = min_date, end = max_date)
    
  })
  
}

# --- Ejecutar la Aplicación ---
shinyApp(ui, server)