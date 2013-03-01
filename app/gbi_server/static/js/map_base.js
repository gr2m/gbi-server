var ro_symbolizer = {
    "Polygon": {
        strokeWidth: 1,
        strokeOpacity: 0.5,
        strokeColor: "#D6311E",
        fillColor: "#D6311E",
        fillOpacity: 0.5
    }
};

var rw_symbolizer = {
    "Polygon": {
        strokeWidth: 1,
        strokeOpacity: 0.5,
        strokeColor: "blue",
        fillColor: "blue",
        fillOpacity: 0.4
    }
};

var select_symbolizer = {
    strokeColor: "black",
    strokeWidth: 2,
    strokeOpacity: 1
};

var ro_style = new OpenLayers.Style();
ro_style.addRules([
    new OpenLayers.Rule({symbolizer: ro_symbolizer})
]);
var ro_style_map = new OpenLayers.StyleMap({
    "default": ro_style,
    "select": select_symbolizer
});
var rw_style = new OpenLayers.Style();
rw_style.addRules([
    new OpenLayers.Rule({symbolizer: rw_symbolizer})
]);
var rw_style_map = new OpenLayers.StyleMap({
    "default": rw_style,
    "select": select_symbolizer
});

function tileUrl(bounds) {
    var tileInfo = this.getTileInfo(bounds.getCenterLonLat());
    return this.url + this.layer + '/' + this.matrixSet + '-' + this.matrix.identifier + '-'
        + tileInfo.col + '-'
        + tileInfo.row + '/tile';
}

OpenLayers.Tile.Image.prototype.onImageError = function() {
        var img = this.imgDiv;
        if (img.src != null) {
            this.imageReloadAttempts++;
            if (this.imageReloadAttempts <= OpenLayers.IMAGE_RELOAD_ATTEMPTS) {
                this.setImgSrc(this.layer.getURL(this.bounds));
            } else {
                OpenLayers.Element.addClass(img, 'olImageLoadError');
                this.events.triggerEvent('loaderror');
                img.src = openlayers_blank_image;
                this.onImageLoad();
            }
        }
}
function init_map() {
    OpenLayers.ImgPath = openlayers_image_path;

    var extent = new OpenLayers.Bounds(-20037508.34, -20037508.34,
                                         20037508.34, 20037508.34);
    var numZoomLevels = zoom_levels;

    var options = {
        projection: new OpenLayers.Projection('EPSG:3857'),
        units: 'm',
        maxResolution: 156543.0339,
        maxExtent: new OpenLayers.Bounds(-20037508.34, -20037508.34,
                                         20037508.34, 20037508.34),
        numZoomLevels: numZoomLevels,
        controls: [],
        theme: openlayers_theme_url,
        restrictedExtent: extent
    };

    var map = new OpenLayers.Map('map', options );

    $.each(sources, function(index, layer) {
        map.addLayer(layer);
    });
    map.addLayer(basic);

    if (!has_visible_baselayer) {
       map.setBaseLayer(basic);
    }

    map.addControl(
        new OpenLayers.Control.TouchNavigation({
            dragPanOptions: {
                enableKinetic: true
            }
        })
    );
    var layerswitcher = new OpenLayers.Control.LayerSwitcher({
        roundedCorner: true
    });
    map.addControl(layerswitcher)
    layerswitcher.maximizeControl();

    map.addControl(new OpenLayers.Control.PanZoomBar());
    map.addControl(new OpenLayers.Control.Navigation());
    map.zoomToMaxExtent();
    return map;
}
