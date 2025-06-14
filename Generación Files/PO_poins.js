// 1. Cargar puntos de presencia
var presencias = ee.FeatureCollection("projects/ee-dannyreina2101091/assets/presencias_agrupadas_1km");

// 2. Región ECOPAL
var region = ee.FeatureCollection("FAO/GAUL/2015/level0")
  .filter(ee.Filter.inList("ADM0_NAME", ["Ecuador", "Peru", "Colombia", "Panama"]));
var presencias_filtradas = presencias.filterBounds(region);
Map.centerObject(region, 5);

// 3. Capas climáticas y topográficas
var worldclim = ee.Image("WORLDCLIM/V1/BIO");  // bio01 - bio19
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

// 4. Stack completo
var stack = worldclim
  .addBands(elev)
  .addBands(slope.rename("slope"))
  .addBands(aspect.rename("aspect"))
  .addBands(hillshade.rename("hillshade"))
  .addBands(tri)
  .addBands(cti)
  .addBands(watdist)
  .addBands(landcover);

// 5. Usar reduceRegions en vez de sampleRegions
var sampled = stack.reduceRegions({
  collection: presencias_filtradas,
  reducer: ee.Reducer.first(),  // para tomar el valor en el píxel central
  scale: 1000
});

// 6. Exportar (conservará todas las filas, con null donde falte)
Export.table.toDrive({
  collection: sampled,
  description: "ECOPAL_presencias_variables_completas_con_nulls",
  fileFormat: "CSV"
});
