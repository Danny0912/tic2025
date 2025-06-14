// -----------------------------------
// CONFIGURACIÓN
// -----------------------------------

var region = ee.FeatureCollection("FAO/GAUL/2015/level0")
  .filter(ee.Filter.inList("ADM0_NAME", ["Ecuador"]));

var numRandomPoints = 6000;
var seed = 42;

// -----------------------------------
// GENERAR PUNTOS ALEATORIOS
// -----------------------------------

var regionGeometry = region.geometry();

var randomPoints = ee.FeatureCollection.randomPoints({
  region: regionGeometry,
  points: numRandomPoints,
  seed: seed
});

// -----------------------------------
// VARIABLES CLIMÁTICAS Y TOPOGRÁFICAS
// -----------------------------------

var worldclim = ee.Image("WORLDCLIM/V1/BIO");
var elev = ee.Image("CGIAR/SRTM90_V4").rename("elev");
var terrain = ee.Terrain.products(elev);
var slope = terrain.select("slope");
var aspect = terrain.select("aspect");
var hillshade = terrain.select("hillshade");
var tri = elev.convolve(ee.Kernel.laplacian8(1)).rename("tri");
var cti = elev.multiply(slope.tan()).log().rename("cti");

var water = ee.Image("JRC/GSW1_3/GlobalSurfaceWater").select("occurrence").gt(50);
var watdist = water.fastDistanceTransform().sqrt().rename("watdist");

var landcover = ee.Image("ESA/WorldCover/v100/2020").select("Map").rename("landcover");

// -----------------------------------
// SELECCIÓN DE VARIABLES CLAVE
// -----------------------------------

var vars_selected = worldclim.select([
  "bio01", "bio02", "bio03", "bio04", "bio07",
  "bio12", "bio13", "bio14", "bio15", "bio18", "bio19"
]);

var allVars = vars_selected
  .addBands(slope.rename("slope"))
  .addBands(aspect.rename("aspect"))
  .addBands(hillshade.rename("hillshade"))
  .addBands(tri)
  .addBands(cti)
  .addBands(watdist)
  .addBands(landcover);

// -----------------------------------
// EXTRAER VALORES PARA PUNTOS
// -----------------------------------

var rbWithVars = allVars.reduceRegions({
  collection: randomPoints,
  reducer: ee.Reducer.first(),
  scale: 1000
});

// -----------------------------------
// AÑADIR COLUMNAS FALTANTES MANUALMENTE
// -----------------------------------

rbWithVars = rbWithVars.map(function(feat) {
  return feat.set({
    'especie': null,
    'fecha': null,
    'total_individuos': 0
  });
});

// -----------------------------------
// EXPORTACIÓN
// -----------------------------------

Export.table.toDrive({
  collection: rbWithVars,
  description: "ECOPAL_RB_uniforme_filtrado_vars",
  fileFormat: "CSV"
});

// -----------------------------------
// VISUALIZACIÓN
// -----------------------------------

Map.centerObject(region, 5);
Map.addLayer(region, {color: 'green'}, "Región ECOPAL");
Map.addLayer(randomPoints, {color: 'orange'}, "Puntos RB uniformes");
