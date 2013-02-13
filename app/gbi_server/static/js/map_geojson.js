function init_geojson(map) {
    map.addLayers(geojson_sources);
    for (source in geojson_sources) {
    	if (geojson_sources[source].read_only) {
    		map.zoomToExtent(geojson_sources[source].getDataExtent())
    		break;
    	}
    }
}