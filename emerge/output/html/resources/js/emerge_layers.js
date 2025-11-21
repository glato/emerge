/**
 * Layer visualization and prominence control functionality for emerge
 */

// Global state for layer visualization
let activeLayers = {};
let layersInitialized = false;

/**
 * Initialize layer visualization controls and data
 */
function initializeLayerVisualization() {
    if (typeof visualization_layers === 'undefined' || !visualization_layers.enabled) {
        console.log('No layer visualization data available');
        return;
    }

    const layers = visualization_layers.layers || [];
    if (layers.length === 0) {
        console.log('No layers defined');
        return;
    }

    console.log(`Initializing layer visualization with ${layers.length} layers`);

    // Show the layer controls button
    const layerButton = document.getElementById('buttonToggleLayerControls');
    if (layerButton) {
        layerButton.style.display = 'block';
    }

    // Initialize all layers as active
    for (const layer of layers) {
        activeLayers[layer.name] = true;
    }

    // Create layer checkboxes
    createLayerCheckboxes();

    layersInitialized = true;
}

/**
 * Create checkboxes for each visualization layer
 */
function createLayerCheckboxes() {
    const container = document.getElementById('layerCheckboxes');
    if (!container) return;

    container.innerHTML = '';

    const layers = visualization_layers.layers || [];

    for (const layer of layers) {
        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'form-check form-switch';
        checkboxDiv.style.marginBottom = '5px';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input';
        checkbox.id = `layer_${layer.name.replace(/[^a-zA-Z0-9]/g, '_')}`;
        checkbox.checked = true;
        checkbox.setAttribute('data-layer-name', layer.name);
        checkbox.onclick = function() {
            toggleLayer(layer.name, this.checked);
        };

        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = checkbox.id;

        // Create color swatch and label
        const colorSwatch = `<span style="display:inline-block; width:12px; height:12px; background-color:${layer.color}; border:1px solid #000; margin-right:5px;"></span>`;
        const prominenceIcon = getProminenceIcon(layer.prominence);
        label.innerHTML = `<small>${colorSwatch}${prominenceIcon} ${layer.name} (${layer.node_count} nodes)</small>`;

        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        container.appendChild(checkboxDiv);
    }
}

/**
 * Get icon for prominence level
 */
function getProminenceIcon(prominence) {
    const icons = {
        'high': '★',
        'medium': '◆',
        'low': '○',
        'background': '·'
    };
    return icons[prominence] || '◆';
}

/**
 * Toggle visibility of layer controls
 */
function toggleLayerControls() {
    const container = document.getElementById('layerControlsContainer');
    if (container) {
        container.style.display = container.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Toggle all layers on/off
 */
function toggleAllLayers(checked) {
    const layers = visualization_layers.layers || [];

    for (const layer of layers) {
        activeLayers[layer.name] = checked;

        // Update individual checkboxes
        const checkbox = document.querySelector(`[data-layer-name="${layer.name}"]`);
        if (checkbox) {
            checkbox.checked = checked;
        }
    }

    updateNodeProminence();
}

/**
 * Toggle a specific layer on/off
 */
function toggleLayer(layerName, active) {
    activeLayers[layerName] = active;

    // Update "all layers" checkbox
    const allLayersCheckbox = document.getElementById('toggleAllLayers');
    if (allLayersCheckbox) {
        const layers = visualization_layers.layers || [];
        const allActive = layers.every(layer => activeLayers[layer.name]);
        allLayersCheckbox.checked = allActive;
    }

    updateNodeProminence();
}

/**
 * Update node prominence and styling based on active layers
 */
function updateNodeProminence() {
    if (!layersInitialized || typeof node_layer_assignments === 'undefined') {
        return;
    }

    // Get the current graph
    const currentGraph = getCurrentGraph();
    if (!currentGraph || !currentGraph.nodes) {
        return;
    }

    // Update each node's prominence based on active layers
    currentGraph.nodes.forEach(node => {
        const nodeId = node.id;
        const nodeProminenceData = getNodeProminence(nodeId);

        if (!nodeProminenceData) {
            // Node not in any active layer - dim it
            node.layerOpacity = 0.2;
            node.layerRadiusMultiplier = 0.5;
            node.layerActive = false;
            node.prominence = 'background';
        } else {
            // Node in active layer(s) - apply prominence
            node.layerOpacity = nodeProminenceData.opacity;
            node.layerRadiusMultiplier = nodeProminenceData.radius_multiplier;
            node.layerActive = true;
            node.prominence = nodeProminenceData.prominence;
            node.layerColors = nodeProminenceData.colors;
        }
    });

    // Restart the simulation to apply new styling
    if (typeof simulation !== 'undefined' && simulation) {
        simulation.alpha(0.3).restart();
    }

    // Re-render the graph
    if (typeof renderGraph === 'function') {
        renderGraph();
    }
}

/**
 * Get prominence data for a specific node based on active layers
 */
function getNodeProminence(nodeId) {
    if (typeof node_layer_assignments === 'undefined' || !node_layer_assignments[nodeId]) {
        return null;
    }

    const nodeLayers = node_layer_assignments[nodeId];
    const layers = visualization_layers.layers || [];

    // Find which of this node's layers are active
    const activeNodeLayers = nodeLayers.filter(layerName => activeLayers[layerName]);

    if (activeNodeLayers.length === 0) {
        return null;
    }

    // Find the highest prominence among active layers
    let highestProminence = 'background';
    let highestLevel = 3;
    let colors = [];

    for (const layerName of activeNodeLayers) {
        const layer = layers.find(l => l.name === layerName);
        if (layer) {
            colors.push(layer.color);
            const level = prominenceToLevel(layer.prominence);
            if (level < highestLevel) {
                highestLevel = level;
                highestProminence = layer.prominence;
            }
        }
    }

    // Get prominence values from node_prominence if available
    let opacity = getProminenceOpacity(highestProminence);
    let radiusMultiplier = getProminenceRadiusMultiplier(highestProminence);

    if (typeof node_prominence !== 'undefined' && node_prominence[nodeId]) {
        opacity = node_prominence[nodeId].opacity;
        radiusMultiplier = node_prominence[nodeId].radius_multiplier;
    }

    return {
        prominence: highestProminence,
        opacity: opacity,
        radius_multiplier: radiusMultiplier,
        colors: colors
    };
}

/**
 * Convert prominence string to numeric level (lower = more prominent)
 */
function prominenceToLevel(prominence) {
    const levels = {
        'high': 0,
        'medium': 1,
        'low': 2,
        'background': 3
    };
    return levels[prominence] || 3;
}

/**
 * Get opacity value for prominence level
 */
function getProminenceOpacity(prominence) {
    const opacityMap = {
        'high': 1.0,
        'medium': 0.8,
        'low': 0.5,
        'background': 0.2
    };
    return opacityMap[prominence] || 0.5;
}

/**
 * Get radius multiplier for prominence level
 */
function getProminenceRadiusMultiplier(prominence) {
    const multiplierMap = {
        'high': 1.5,
        'medium': 1.0,
        'low': 0.75,
        'background': 0.5
    };
    return multiplierMap[prominence] || 1.0;
}

/**
 * Apply layer-based styling to node rendering
 * This function should be called from the main graph rendering code
 */
function applyLayerStyling(nodeSelection) {
    if (!layersInitialized) {
        return nodeSelection;
    }

    nodeSelection
        .style('opacity', d => {
            if (!layersInitialized) return 1.0;
            return d.layerOpacity !== undefined ? d.layerOpacity : 1.0;
        })
        .attr('r', d => {
            // Calculate base radius
            let baseRadius = 5; // default radius

            // Apply any existing radius calculations
            if (typeof calculateNodeRadius === 'function') {
                baseRadius = calculateNodeRadius(d);
            }

            // Apply layer radius multiplier
            if (layersInitialized && d.layerRadiusMultiplier !== undefined) {
                return baseRadius * d.layerRadiusMultiplier;
            }

            return baseRadius;
        })
        .style('stroke', d => {
            if (d.layerColors && d.layerColors.length > 1) {
                // Multiple colors - use second color as stroke for multi-layer nodes
                return d.layerColors[1];
            }
            return '#000';
        })
        .style('stroke-width', d => {
            if (d.layerColors && d.layerColors.length > 1) {
                return 3; // Thicker border for multi-layer nodes
            }
            return 1.5;
        });

    return nodeSelection;
}

/**
 * Check if layer visualization is active
 */
function isLayerVisualizationActive() {
    return layersInitialized;
}

/**
 * Get current graph based on selected graph type
 */
function getCurrentGraph() {
    // This should be implemented based on the current graph selection
    // For now, return file_result_dependency_graph as default
    if (typeof file_result_dependency_graph !== 'undefined') {
        return file_result_dependency_graph;
    }
    return null;
}

// Initialize layer visualization when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeLayerVisualization);
} else {
    initializeLayerVisualization();
}
