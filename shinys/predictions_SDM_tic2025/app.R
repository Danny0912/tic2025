library(shiny)
library(leaflet)
library(dplyr)
library(readr)
library(shinythemes) # For professional themes
library(RColorBrewer) # For better color palettes

# Ensure 'predicciones_multiespecie_095.csv' is in the same directory as this app.R file
predicciones <- read_csv("predicciones_multiespecie_095.csv", show_col_types = FALSE)

# Identify species columns dynamically
# This approach is more robust and less prone to errors if column names change.
variables_no_especie <- c("x", "y", "slope", "aspect", "hillshade", "tri", "watdist", "landcover", grep("^bio", names(predicciones), value = TRUE))
nombres_especies <- sort(setdiff(names(predicciones), variables_no_especie)) # Sort for better UI

# --- User Interface (UI) ---
ui <- fluidPage(
  # Add a professional theme
  theme = shinytheme("flatly"), # "flatly" is clean and modern. "cosmo" or "lumen" are also good alternatives.
  
  # Custom CSS for enhanced aesthetics
  tags$head(
    tags$style(HTML("
      body {
        font-family: 'Open Sans', sans-serif; /* A clean, modern font */
        background-color: #f8f9fa; /* Light gray background */
      }
      .titlePanel-custom { /* Custom class for the main title div */
        background-color: #495057; /* Muted dark grey for a professional look */
        color: white;
        padding: 15px;
        margin-bottom: 25px; /* Increased margin for better spacing */
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Subtle shadow for depth */
      }
      .well { /* Styles for the sidebar panel */
        background-color: #ffffff; /* White background for sidebar */
        border: 1px solid #e2e6ea;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05); /* Subtle shadow */
        border-radius: 8px;
        padding: 20px;
      }
      .shiny-input-container {
        margin-bottom: 18px; /* Slightly more space between inputs */
      }
      .leaflet-container {
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Shadow for the map */
      }
      .legend-title {
        font-weight: bold;
        margin-bottom: 5px;
        font-size: 1.1em; /* Slightly larger legend title */
      }
      .legend-subtitle {
        font-weight: normal;
        font-size: 0.9em;
        color: #555;
      }
      h4 { /* Styling for secondary headers in sidebar/main panel */
        color: #495057; /* Matching the new title bar color */
        margin-bottom: 15px;
        border-bottom: 1px solid #dee2e6; /* Subtle line below headers */
        padding-bottom: 5px;
      }
      p {
        font-size: 0.95em; /* Slightly larger paragraph text */
        line-height: 1.6; /* Better line spacing */
        color: #495057; /* Darker gray for readability */
      }
    "))
  ),
  
  # Application title with improved styling
  div(class = "titlePanel-custom",
      h2("Deep Learning-Based Species Distribution Map: Aposematic Frogs of Ecuador", align = "center"),
      p("Explore the predicted probabilities of species occurrence across continental Ecuador.", align = "center")
  ),
  
  sidebarLayout(
    sidebarPanel(
      # Add a descriptive header for the sidebar
      h4("Visualization Settings"),
      selectInput(
        "especie",
        "Select a Species to Visualize:",
        choices = nombres_especies,
        selected = nombres_especies[1] # Pre-select the first species
      ),
      br(), # Add some vertical space
      p("Use the selector above to choose a species and view its predicted occurrence probability on the map."),
      p("This map shows the output of a study on the geographical distribution of aposematic frogs in Ecuador using deep learning and weighted pseudo-absences, developed within an academic research framework at Escuela Politécnica Nacional.")
    ),
    mainPanel(
      h4("Occurrence Probability Map"),
      leafletOutput("mapa", height = 650), # Increase map height for better visibility
      br(),
      p("This map displays the predicted probability of the selected species. More intense colors (blue) indicate a higher probability of occurrence."),
      p("For academic correspondence regarding this map or the underlying study, please contact danny.reina01@epn.edu.ec")
    )
  )
)

# --- Server Logic ---
server <- function(input, output, session) {
  
  # Reactive expression to filter data based on selected species
  data_filtered <- reactive({
    req(input$especie) # Ensure a species is selected before proceeding
    predicciones %>%
      select(x, y, species_prob = all_of(input$especie)) # Rename for clarity in leaflet
  })
  
  # Render the Leaflet map
  output$mapa <- renderLeaflet({
    datos <- data_filtered()
    
    # Create a more professional, sequential color palette
    # "GnBu" is a good option for a subtle, professional gradient from green to blue
    # Other professional palettes from RColorBrewer include "PuBu", "YlGnBu", "Blues", "Greens", "Purples"
    color_palette <- colorNumeric(
      palette = "GnBu", # Changed palette to Green-Blue for a more professional look
      domain = range(datos$species_prob, na.rm = TRUE) # Use the actual range of the selected species
    )
    
    leaflet(datos) %>%
      addProviderTiles(providers$CartoDB.Positron, # A cleaner, light base map
                       options = providerTileOptions(minZoom = 5, maxZoom = 12)) %>% # Limit zoom for better focus
      addCircleMarkers(
        lng = ~x,
        lat = ~y,
        radius = 4,
        color = ~color_palette(species_prob),
        stroke = FALSE, # No border for the circles
        fillOpacity = 0.7,
        label = ~paste("Probability:", round(species_prob, 3)),
        labelOptions = labelOptions(
          style = list("font-weight" = "normal", padding = "3px 8px"),
          textsize = "12px", direction = "auto"
        )
      ) %>%
      addLegend(
        position = "bottomright",
        pal = color_palette,
        values = datos$species_prob,
        title = HTML(paste0("<div class='legend-title'>Occurrence Probability</div>",
                            "<div class='legend-subtitle'>", input$especie, "</div>")), # Dynamic legend title including species name
        opacity = 1
      ) %>%
      # Add a simple control to reset view (useful for users)
      addEasyButton(
        easyButton(
          icon = "fa-globe", title = "Recenter Map to Ecuador", # Changed icon and title
          onClick = JS("function(btn, map){ map.setView([-1.831239, -78.183406], 6); }") # Approximate center of Ecuador, zoom level 6
        )
      )
  })
}

# Run the Shiny app
shinyApp(ui, server)