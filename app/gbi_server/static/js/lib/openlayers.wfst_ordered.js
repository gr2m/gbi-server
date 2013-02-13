/**
 * @requires OpenLayers/Protocol/WFS/v1_1_0.js
 */

/**
 * Class: OpenLayers.Protocol.WFS.v1_1_0_ordered
 * Get attribute order by calling WFSDescribeFeatureType
 *
 * Inherits from:
 * - <OpenLayers.Protocol.WFS.v1_0_0>
 */

OpenLayers.Protocol.WFS.v1_1_0_ordered = OpenLayers.Class(OpenLayers.Protocol.WFS.v1_1_0, {

    version: "1.1.0",

    attribute_order: false,

    initialize: function(options) {
        this.get_attribute_order(options.schema)
        this.formatOptions = OpenLayers.Util.extend({
            attribute_order: this.attribute_order
        }, this.formatOptions);
        OpenLayers.Protocol.WFS.v1_1_0.prototype.initialize.apply(this, arguments);
    },

    /**
     * Method: get_attribute_order
     * Load attribute order for INSERT by calling WFSDescribeFeatureType
     *
     * Parameters:
     * url - {String} URL of WFS server
     */
    get_attribute_order: function(url) {
        var response = OpenLayers.Request.GET({
            url: url,
            async: false
        });
        var feature_type_parser = new OpenLayers.Format.WFSDescribeFeatureType();
        try {
            var properties = feature_type_parser.read(response.responseText).featureTypes[0].properties;
        } catch(e) {
            var properties = false;
        }
        if(properties) {
            var attribute_order = [];
            var attribute_types = {};
            for(var idx in properties) {
                attribute_order.push(properties[idx].name);
                attribute_types[properties[idx].name] = properties[idx].type;
            }
            this.attribute_order = attribute_order;
            this.attribute_types = attribute_types;
        }

    },

    CLASS_NAME: "OpenLayers.Protocol.WFS.v1_1_0_ordered"
});

OpenLayers.Protocol.WFS.v1_1_0_ordered_get = OpenLayers.Class(OpenLayers.Protocol.WFS.v1_1_0_ordered, {

    read: function(options) {
        OpenLayers.Protocol.prototype.read.apply(this, arguments);
        options = OpenLayers.Util.extend({}, options);
        OpenLayers.Util.applyDefaults(options, this.options || {});
        var response = new OpenLayers.Protocol.Response({requestType: "read"});
        if(options.additional_feature_ns) {
            this.format.setNamespace('feature', options.additional_feature_ns);
        }
        response.priv = OpenLayers.Request.GET({
            url: options.url + '&request=getfeature&service=wfs&version='+this.format.version+'&srsName='+options.srsName+'&typename='+options.typename,
            callback: this.createCallback(this.handleRead, response, options),
            params: options.params
        })
        return response
    },
    CLASS_NAME: "OpenLayers.Protocol.WFS.v1_1_0_ordered_get"
});


/**
 * @requires OpenLayers/Format/WFST/v1_1_0.js
 */
OpenLayers.Format.WFST.v1_1_0_ordered_get = OpenLayers.Format.WFST.v1_1_0_ordered = OpenLayers.Class(
    OpenLayers.Format.WFST.v1_1_0, {

        version: "1.1.0",

        attribute_order: false,

        initialize: function(options) {
            //replace version by original wfst version number
            options.version = this.version
            OpenLayers.Format.WFST.v1_1_0.prototype.initialize.apply(this, [options]);
        },
        readers: {
            "wfs": OpenLayers.Format.WFST.v1_1_0.prototype.readers["wfs"],
            "gml": OpenLayers.Format.WFST.v1_1_0.prototype.readers["gml"],
            "feature": OpenLayers.Format.WFST.v1_1_0.prototype.readers["feature"],
            "ogc": OpenLayers.Format.WFST.v1_1_0.prototype.readers["ogc"],
            "ows": OpenLayers.Format.WFST.v1_1_0.prototype.readers["ows"]
        },
        writers: {
            "wfs": OpenLayers.Format.WFST.v1_1_0.prototype.writers["wfs"],
            "gml": OpenLayers.Format.WFST.v1_1_0.prototype.writers["gml"],
            "feature": OpenLayers.Util.applyDefaults({
                "_typeName": function(feature) {
                    if(this.attribute_order) {
                        var node = this.createElementNSPlus("feature:" + this.featureType, {
                            attributes: {fid: feature.fid}
                        });
                        for(var idx in this.attribute_order) {
                            var prop = this.attribute_order[idx]
                            if(prop == this.geometryName) {
                                this.writeNode("feature:_geometry", feature.geometry, node);
                            } else {
                                var value = feature.attributes[prop];
                                if(value != null) {
                                    this.writeNode(
                                        "feature:_attribute",
                                        {name: prop, value: value}, node
                                    );
                                }
                            }
                        }
                        return node;
                    } else {
                        return OpenLayers.Format.WFST.v1_1_0.prototype.writers["feature"]["_typeName"].call(this, feature);
                    }
                }
            }, OpenLayers.Format.WFST.v1_1_0.prototype.writers["feature"]),
            "ogc": OpenLayers.Format.WFST.v1_1_0.prototype.writers["ogc"],
            "ows": OpenLayers.Format.WFST.v1_1_0.prototype.writers["ows"]
        },

        CLASS_NAME: "OpenLayers.Format.WFST.v1_1_0_ordered"
});
