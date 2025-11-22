/**
 * Edge filtering and visualization functionality for emerge
 */

// Global state for edge filtering
let activeEdgeTypes = {
    'IMPORT': true,
    'INHERITANCE': true,
    'ASSOCIATION': true,
    'COMPOSITION': true,
    'AGGREGATION': true,
    'UNKNOWN': true
};
let edgeControlsInitialized = false;

/**
 * Initialize edge controls and data
 */
function initializeEdgeControls() {
    if (typeof edge_types === 'undefined' || Object.keys(edge_types).length === 0) {
        console.log('No edge type data available');
        return;
    }

    console.log(`Initializing edge controls with ${Object.keys(edge_types).length} edges`);

    // Show the edge controls button
    const edgeButton = document.getElementById('buttonToggleEdgeControls');
    if (edgeButton) {
        edgeButton.style.display = 'block';
    }

    edgeControlsInitialized = true;
}

/**
 * Toggle visibility of edge controls
 */
function toggleEdgeControls() {
    const container = document.getElementById('edgeControlsContainer');
    if (container) {
        container.style.display = container.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Toggle all edge types on/off
 */
function toggleAllEdgeTypes(checked) {
    // Update all edge type checkboxes
    const checkboxes = document.querySelectorAll('.edge-type-filter');
    checkboxes.forEach(checkbox => {
        checkbox.checked = checked;
        const edgeType = checkbox.getAttribute('data-edge-type');
        activeEdgeTypes[edgeType] = checked;
    });

    // Trigger visualization update
    updateEdgeFilters();
}

/**
 * Update edge filters based on checkbox states
 */
function updateEdgeFilters() {
    // Update activeEdgeTypes based on checkboxes
    const checkboxes = document.querySelectorAll('.edge-type-filter');
    checkboxes.forEach(checkbox => {
        const edgeType = checkbox.getAttribute('data-edge-type');
        activeEdgeTypes[edgeType] = checkbox.checked;
    });

    // Update "all edge types" checkbox
    const allEdgeTypesCheckbox = document.getElementById('toggleAllEdgeTypes');
    if (allEdgeTypesCheckbox) {
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        allEdgeTypesCheckbox.checked = allChecked;
    }

    // Trigger re-render if using canvas rendering
    if (typeof renderGraph === 'function') {
        renderGraph();
    }
}

/**
 * Check if an edge type should be rendered
 */
function isEdgeTypeActive(edgeType) {
    if (!edgeControlsInitialized) {
        return true; // Show all edges by default
    }
    return activeEdgeTypes[edgeType] !== false;
}

/**
 * Check if edge controls are initialized
 */
function areEdgeControlsActive() {
    return edgeControlsInitialized;
}

// Initialize edge controls when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEdgeControls);
} else {
    initializeEdgeControls();
}
