var selected_feature = false;
var selected_features = [];
var draw_controls = false;

function zoom_to_data_extent() {
    this.events.un({'loadend': zoom_to_data_extent});
    var data_extent = this.getDataExtent();
    if(data_extent) {
        this.map.zoomToExtent(this.getDataExtent());
    } else {
        $('#no_search_result').show().fadeOut(2500);
    }
}

function add_search(layer, property, value) {
    layer.filter = new OpenLayers.Filter.Comparison({
        type: OpenLayers.Filter.Comparison.LIKE,
        property: property,
        value: search_prefix + value + '*'
    });
    layer.events.on({'loadend': zoom_to_data_extent});
    if(layer.visibility) {
        layer.refresh({force: true});
    } else {
        layer.setVisibility(true);
    }
}

function remove_search(layer) {
    layer.filter = null;
    layer.setVisibility(false);
}

function wfs_save_success(response) {
    var map = response.object.layer.map;
    $.get(write_back_url)
    wfs_msg_handler('success');
    $('#save_changes').attr('disabled', 'disabled').removeClass('btn-success');
    map.baseLayer.redraw();
}

function wfs_save_fail(response) {
    var error_msg = response.response.error.exceptionReport.exceptions[0].texts[0]
    wfs_msg_handler('error', error_msg);
}

function wfs_msg_handler(status, response_msg) {
    var msg = SAVE_SUCCESSFULL_MSG;
    var alert_class = 'alert-success';
    if(status == 'error') {
        msg = SAVE_FAILED_MSG + '<br>' + response_msg;
        alert_class = 'alert-error';
    }
    $('#wfs_response_message').html(msg);
    $('#wfs_response').addClass(alert_class).show()
        .fadeOut(2500, function() {
            $('#wfs_response_message').empty();
            $('#wfs_response').removeClass(alert_class);
        });
}

function create_input_element(attribute) {
    return $('<div>').addClass('control-group')
        .append($('<label>').addClass('control-label')
            .attr('for', attribute).html(attribute + ': '))
        .append($('<div>').addClass('controls')
            .append($('<input>').addClass('input-medium')
                .attr('id', attribute)
                .attr('name', attribute)
                .attr('type', 'text')
                .attr('disabled', 'disabled')));
}

function create_attribute_input(read_only_layer) {
    $.each(wfs_sources, function(idx, source) {
        if(source.protocol.attribute_order) {
            source.attributes_input = [];
            source.input_rules = {}
            $.each(source.protocol.attribute_order, function(idx, attribute) {
                if(attribute != source.protocol.geometryName) {
                    source.attributes_input.push(create_input_element(attribute));
                    var type = source.protocol.attribute_types[attribute]
                    if(type == 'float' || type == 'double') {
                        source.input_rules[attribute] = {number: true};
                    }
                }
            });
        }
    });
    read_only_layer.attributes_input = [];
    read_only_layer.input_rules = {}
    $.each(read_only_schema, function(attribute, type) {
        read_only_layer.attributes_input.push(create_input_element(attribute));
        if(type == 'float' || type == 'double') {
            read_only_layer.input_rules[attribute] = {number: true};
        }
    });
}

function unselect_features() {
    if(selected_feature || selected_features.length) {
        if(draw_controls['edit'].feature) {
            draw_controls['edit'].unselectFeature(selected_feature);
        }
        $('#edit_feature').removeClass('btn-success');
        selected_feature = false;
        selected_features = [];
        draw_controls['select'].unselectAll();
    }
}

function update_feature_attributes(map) {
    $.each($('#feature_attributes input'), function(idx, input) {
        if(!$(input).val()) {
            selected_feature.attributes[input.id] = null;
        } else {
            selected_feature.attributes[input.id] = $(input).val();
        }
    });
    if(selected_feature.state != OpenLayers.State.INSERT) {
        selected_feature.state = OpenLayers.State.UPDATE;
    }
    selected_feature.layer.events.triggerEvent("afterfeaturemodified",
        {feature: selected_feature}
    );
    unselect_features()
}

function edit_feature(map) {
    var write_layer = map.getLayersByName(write_layer_name)[0];
    if(selected_feature == draw_controls['edit'].feature) {
        draw_controls['edit'].unselectFeature(selected_feature);
        $('#edit_feature').removeClass('btn-success');
    } else {
        draw_controls['edit'].selectFeature(selected_feature);
        $('#edit_feature').addClass('btn-success')
    }
}

function delete_feature(map) {
    var write_layer = map.getLayersByName(write_layer_name)[0];
    var to_delete = selected_features;
    $.each(to_delete, function(idx, feature) {
        draw_controls['del'].deleteFeature(feature);
    });
}

function copy_feature(map) {
    var write_layer = map.getLayersByName(write_layer_name)[0];
    var new_features = [];
    $.each(selected_features, function(idx, feature) {
        var geometry = feature.geometry.clone();
        var new_feature = new OpenLayers.Feature.Vector(geometry);
        new_feature.state = OpenLayers.State.INSERT;
        $.each(feature.attributes, function(k, v) {
            new_feature.attributes[k] = v;
        });
        new_features.push(new_feature);
    });
    unselect_features();
    write_layer.addFeatures(new_features);
}

function save_changes(map) {
    unselect_features();
    var write_layer = map.getLayersByName(write_layer_name)[0];
    $.each(write_layer.strategies, function(idx, strategy) {
        if(strategy.CLASS_NAME == 'OpenLayers.Strategy.Save') {
            strategy.save();
            return false;
        }
    })
}

var DeleteFeature = OpenLayers.Class(OpenLayers.Control, {
    initialize: function(layer, options) {
        OpenLayers.Control.prototype.initialize.apply(this, [options]);
        this.layer = layer;
        this.handler = new OpenLayers.Handler.Feature(
            this, layer, {click: this.clickFeature}
        );
    },
    deleteFeature: function(feature) {
        unselect_features();
        if(feature.fid == undefined) {
            this.layer.destroyFeatures([feature]);
        } else {
            feature.state = OpenLayers.State.DELETE;
            this.layer.events.triggerEvent("afterfeaturemodified",
                {feature: feature}
            );
            feature.renderIntent = "select";
            this.layer.drawFeature(feature);
        }
    },
    setMap: function(map) {
        this.handler.setMap(map);
        OpenLayers.Control.prototype.setMap.apply(this, arguments);
    },
    setLayer: function(layer) {
        this.layer = layer;
    },
    CLASS_NAME: "OpenLayers.Control.DeleteFeature"
});

function init_draw_controls(map, layers, write_layer) {
    var panel = new OpenLayers.Control.Panel({
        'displayClass': 'customEditingToolbar',
        'allowDepress': true
    });

    var draw = new OpenLayers.Control.DrawFeature(
        write_layer, OpenLayers.Handler.Polygon,
        {
            title: "Draw Feature",
            displayClass: "olControlDrawFeaturePolygon",
            handlerOptions: {holeModifier: "altKey"}
        }
    );

    var edit = new OpenLayers.Control.ModifyFeature(write_layer, {
        standalone: true,
        mode: OpenLayers.Control.ModifyFeature.RESHAPE
    });
    edit.setMap(map)

    var del = new DeleteFeature(write_layer);

    var select = new OpenLayers.Control.SelectFeature(layers, {
        title: "Select Feature",
        displayClass: "olControlSelectFeature",
        multiple: true,
        onSelect: function (feature) {
            var target = $('#feature_attributes');
            target.empty().append(feature.layer.attributes_input);
            var validator = target.validate({
                rules: feature.layer.input_rules,
                showErrors: function(errorMap, errorList) {
                    if(this.numberOfInvalids() > 0) {
                        $('#edit_attributes_button').attr('disabled', 'disabled');
                    } else {
                        $('#edit_attributes_button').removeAttr('disabled');
                    }
                    this.defaultShowErrors();
                }
            });
            selected_feature = feature;
            selected_features.push(feature);
            if(feature.layer != write_layer) {
                $('#copy_feature').removeAttr('disabled');
            } else {
                $('#delete_feature').removeAttr('disabled');
                if(selected_features.length == 1) {
                    $('#edit_feature').removeAttr('disabled');
                } else {
                    $('#edit_feature').attr('disabled', 'disabled');
                }
            }
            $.each(feature.attributes, function(name, value) {
                $('#feature_attributes #'+name).val(value);
            });
            if(feature.layer.writable) {
                $('#feature_attributes input').removeAttr('disabled');
                $('#edit_attributes_button').removeAttr('disabled');
            }
        },
        onUnselect: function() {
            $('#feature_attributes input').val('');
            $('#feature_attributes').validate().resetForm();
            $('#feature_attributes').empty();
            unselect_features();
            $('#edit_attributes_button').attr('disabled', 'disabled');
            $('.feature_control').attr('disabled', 'disabled');
        }
    });
    select.events.on({
        deactivate: function(e) {
            unselect_features();
        }
    });

    panel.addControls([select, draw]);
    panel.defaultControl = select;
    draw_controls = {
        'select': select,
        'del': del,
        'edit': edit,
        'draw': draw,
        'panel': panel
    };
    return panel;
}

function init_wfs(map) {
    var geojson_format = new OpenLayers.Format.GeoJSON();
    var read_only_layer = new OpenLayers.Layer.Vector(read_only_layer_name, {
        projection: new OpenLayers.Projection("EPSG:3857"),
        styleMap: ro_style_map,
        writable: false,
        visibility: false
    });
    read_only_layer.addFeatures(geojson_format.read(featurecollection))

    map.addLayer(read_only_layer);
    map.addLayers(wfs_sources);

    var write_layer = map.getLayersByName(write_layer_name)[0];
    write_layer.setVisibility(true);
    write_layer.events.on({
        loadend: function(e) {
            write_layer.events.on({
                beforefeatureadded: function(e) {
                    unselect_features();
                },
                featureadded: function(e) {
                    draw_controls['select'].select(e.feature);
                    $('#save_changes').removeAttr('disabled').addClass('btn-success');
                },
                afterfeaturemodified: function(e) {
                    if(e.modified || (e.feature && (e.feature.state == OpenLayers.State.DELETE || e.feature.state == OpenLayers.State.UPDATE || e.feature.state == OpenLayers.State.INSERT))) {
                        $('#save_changes').removeAttr('disabled').addClass('btn-success');
                    }
                }
            });
        }
    });

    map.addControl(init_draw_controls(map, [read_only_layer].concat(wfs_sources), write_layer));

    create_attribute_input(read_only_layer);
    $('#edit_attributes_button')
        .click(function() {
            update_feature_attributes(map);
        })
        .attr('disabled', 'disabled');
    $('#edit_feature')
        .click(function() {
            edit_feature(map);
        })
        .attr('disabled', 'disabled');
    $('#delete_feature')
        .click(function() {
            delete_feature(map);
        })
        .attr('disabled', 'disabled');
    $('#copy_feature')
        .click(function() {
            copy_feature(map);
        })
        .attr('disabled', 'disabled');
    $('#save_changes')
        .click(function() {
            save_changes(map);
        })
        .attr('disabled', 'disabled')
        .removeClass('btn-success');

    $('#add_search')
        .click(function() {
            var value = $('#search_value').val().replace(/-/g, '').replace(/\//g, '');
            var layer = map.getLayersByName(search_layer_name)[0];
            add_search(layer, search_property, value);
            $('#remove_search').removeAttr('disabled');
        });
    $('#remove_search')
        .click(function() {
            var layer = map.getLayersByName(search_layer_name)[0];
            remove_search(layer);
            $('#remove_search').attr('disabled', 'disabled');
        }).attr('disabled', 'disabled');
    $('#search_value')
        .keyup(function(e) {
            if($('#search_value').val().replace(/-/g, '').replace(/\//g, '').length < search_min_length) {
                $('#add_search').attr('disabled', 'disabled');
            } else {
                $('#add_search').removeAttr('disabled');
            }
            var code = (e.keyCode ? e.keyCode : e.which);
            if(code == 13 && !$('#add_search').attr('disabled')) {
                $('#add_search').click();
            }
        })
        .keyup();
}
