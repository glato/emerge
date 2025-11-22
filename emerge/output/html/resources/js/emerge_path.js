/**
 * Path analysis and visualization functionality for emerge
 */

// Global state for path analysis
let activePaths = {};
let pathsInitialized = false;

/**
 * Initialize path analysis controls and data
 */
function initializePathAnalysis() {
    if (typeof entry_point_paths === 'undefined' || Object.keys(entry_point_paths).length === 0) {
        console.log('No entry point paths data available');
        return;
    }

    console.log(`Initializing path analysis with ${Object.keys(entry_point_paths).length} paths`);

    // Show the path controls button
    const pathButton = document.getElementById('buttonTogglePathControls');
    if (pathButton) {
        pathButton.style.display = 'block';
    }

    // Initialize all paths as active
    for (const pathId in entry_point_paths) {
        activePaths[pathId] = true;
    }

    // Create path checkboxes
    createPathCheckboxes();

    pathsInitialized = true;

    // Apply initial path colors to nodes
    updateNodeColors();
}

/**
 * Create checkboxes for each entry point path
 */
function createPathCheckboxes() {
    const container = document.getElementById('pathCheckboxes');
    if (!container) return;

    container.innerHTML = '';

    for (const pathId in entry_point_paths) {
        const pathData = entry_point_paths[pathId];

        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'form-check form-switch';
        checkboxDiv.style.marginBottom = '5px';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input';
        checkbox.id = `path_${pathId.replace(/[^a-zA-Z0-9]/g, '_')}`;
        checkbox.checked = true;
        checkbox.setAttribute('data-path-id', pathId);
        checkbox.onclick = function() {
            togglePath(pathId, this.checked);
        };

        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = checkbox.id;
        label.innerHTML = `<small><span style="display:inline-block; width:12px; height:12px; background-color:${pathData.color}; border:1px solid #000; margin-right:5px;"></span>${pathData.label} (${pathData.node_count} nodes)</small>`;

        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        container.appendChild(checkboxDiv);
    }
}

/**
 * Toggle visibility of path controls
 */
function togglePathControls() {
    const container = document.getElementById('pathControlsContainer');
    if (container) {
        container.style.display = container.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Toggle all paths on/off
 */
function toggleAllPaths(checked) {
    for (const pathId in entry_point_paths) {
        activePaths[pathId] = checked;

        // Update individual checkboxes
        const checkbox = document.querySelector(`[data-path-id="${pathId}"]`);
        if (checkbox) {
            checkbox.checked = checked;
        }
    }

    updateNodeColors();
}

/**
 * Toggle a specific path on/off
 */
function togglePath(pathId, active) {
    activePaths[pathId] = active;

    // Update "all paths" checkbox
    const allPathsCheckbox = document.getElementById('toggleAllPaths');
    if (allPathsCheckbox) {
        const allActive = Object.values(activePaths).every(v => v);
        allPathsCheckbox.checked = allActive;
    }

    updateNodeColors();
}

/**
 * Update node colors based on active paths
 */
function updateNodeColors() {
    if (!pathsInitialized || typeof node_path_colors === 'undefined') {
        return;
    }

    // Get the current graph
    const currentGraph = getCurrentGraph();
    if (!currentGraph || !currentGraph.nodes) {
        return;
    }

    // Update each node's color based on active paths
    currentGraph.nodes.forEach(node => {
        const nodeId = node.id;
        const nodeColors = getNodeColors(nodeId);

        if (nodeColors.length === 0) {
            // Node not in any active path - use default/dimmed color
            node.pathColor = null;
            node.pathHighlighted = false;
        } else if (nodeColors.length === 1) {
            // Node in exactly one active path
            node.pathColor = nodeColors[0];
            node.pathHighlighted = true;
        } else {
            // Node in multiple active paths - create gradient or use mixed color
            node.pathColor = createMixedColor(nodeColors);
            node.pathHighlighted = true;
            node.multiPath = true;
        }
    });

    // Restart the simulation to apply new colors
    if (typeof simulation !== 'undefined' && simulation) {
        simulation.alpha(0.3).restart();
    }

    // Re-render the graph
    if (typeof renderGraph === 'function') {
        renderGraph();
    }
}

/**
 * Get colors for a specific node based on active paths
 */
function getNodeColors(nodeId) {
    if (typeof node_path_colors === 'undefined' || !node_path_colors[nodeId]) {
        return [];
    }

    const colors = [];
    const nodePathColors = node_path_colors[nodeId];

    // Check which of this node's paths are active
    for (const pathId in entry_point_paths) {
        if (activePaths[pathId] && nodePathColors.includes(entry_point_paths[pathId].color)) {
            colors.push(entry_point_paths[pathId].color);
        }
    }

    return colors;
}

/**
 * Create a mixed color for nodes in multiple paths
 * For overlapping paths, create a gradient or pattern
 */
function createMixedColor(colors) {
    if (colors.length === 0) return '#999999';
    if (colors.length === 1) return colors[0];

    // Create a gradient ID for D3
    // This will be handled by the graph rendering function
    return colors;
}

/**
 * Apply path coloring to node rendering
 * This function should be called from the main graph rendering code
 */
function applyPathColoring(nodeSelection) {
    if (!pathsInitialized) {
        return nodeSelection;
    }

    nodeSelection
        .style('fill', d => {
            if (d.pathHighlighted && d.pathColor) {
                if (Array.isArray(d.pathColor)) {
                    // Multiple colors - use first color with border
                    return d.pathColor[0];
                }
                return d.pathColor;
            }
            // Not highlighted - use default color or dimmed
            return d.originalColor || '#999999';
        })
        .style('opacity', d => {
            if (!pathsInitialized) return 1.0;
            return d.pathHighlighted ? 1.0 : 0.3;
        })
        .style('stroke', d => {
            if (d.multiPath && Array.isArray(d.pathColor) && d.pathColor.length > 1) {
                // Use second color as stroke for multi-path nodes
                return d.pathColor[1];
            }
            return '#000';
        })
        .style('stroke-width', d => {
            if (d.multiPath && Array.isArray(d.pathColor)) {
                return 3; // Thicker border for multi-path nodes
            }
            return 1.5;
        });

    return nodeSelection;
}

/**
 * Get current graph based on selected graph type
 */
function getCurrentGraph() {
    // Return the actual currentGraph that's being rendered
    if (typeof currentGraph !== 'undefined' && currentGraph) {
        return currentGraph;
    }
    // Fallback to file_result_dependency_graph
    if (typeof file_result_dependency_graph !== 'undefined') {
        return file_result_dependency_graph;
    }
    return null;
}

// Initialize path analysis when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePathAnalysis);
} else {
    initializePathAnalysis();
}
