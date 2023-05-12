/**
* * MARK: - Rendering concave hulls of clusters.
*/
function setupGraphClustersById() {
    clusterMap = {}
    currentGraph.nodes.forEach(function(node, i) {
        let nodeClusterId = 0
        
        if (node.hasOwnProperty('metric_file_result_dependency_graph_louvain_modularity_in_file')) {
            nodeClusterId = node.metric_file_result_dependency_graph_louvain_modularity_in_file
        } else if (node.hasOwnProperty('metric_entity_result_dependency_graph_louvain_modularity_in_entity')) {
            nodeClusterId = node.metric_entity_result_dependency_graph_louvain_modularity_in_entity
        } else if (node.hasOwnProperty('metric_entity_result_inheritance_graph_louvain_modularity_in_entity')) {
            nodeClusterId = node.metric_entity_result_inheritance_graph_louvain_modularity_in_entity
        } else if (node.hasOwnProperty('metric_entity_result_complete_graph_louvain_modularity_in_entity')) {
            nodeClusterId = node.metric_entity_result_complete_graph_louvain_modularity_in_entity
        }
        
        nodeClusterId = nodeClusterId.toString()
        
        if (nodeClusterId in clusterMap) {
            clusterMap[nodeClusterId].push(node)
        } else {
            clusterMap[nodeClusterId] = []
            clusterMap[nodeClusterId].push(node)
        }
    })
    
    // console.log(clusterMap)
}

function onMouseOverHullMenuNode(clusterId) {
    if (!selectedClusterHullIds.includes(clusterId)) {
        addHighlightToSVGCircle(clusterId)
    }
    hoveredClusterHullId = clusterId
    simulationUpdate()
}

function onMouseOutHullMenuNode(clusterId) {
    if (!selectedClusterHullIds.includes(clusterId)) {
        removeHighlightFromSVGCircle(clusterId)
    }
    hoveredClusterHullId = undefined
    simulationUpdate()
}

function addHighlightToSVGCircle(clusterId) {
    let hullNodeSVG = $("#clusterHullNodeSVGCircle-" + clusterId)
    hullNodeSVG.attr('stroke', 'yellow')
    hullNodeSVG.attr('stroke-width', '2')
}

function removeHighlightFromSVGCircle(clusterId) {
    let hullNodeSVG = $("#clusterHullNodeSVGCircle-" + clusterId)
    hullNodeSVG.attr('stroke', 'black')
    hullNodeSVG.attr('stroke-width', '1')
}

function onClickHullMenuNode(clusterId) {
    if (selectedClusterHullIds.includes(clusterId)) {
        removeItemAll(selectedClusterHullIds, clusterId)
        removeHighlightFromSVGCircle(clusterId)
    } else {
        selectedClusterHullIds.push(clusterId)
        addHighlightToSVGCircle(clusterId)
    }
    simulationUpdate()
}

function createClusterHullMenu() {
    // check if there is at least one cluster
    if ("0" in clusterMap) {
        // build menu
        let clusterMenuHtml = "<div id=\"clusterHullContainer\"> \
        <div class=\"row\">"
        
        clusterMenuHtml += "<div class=\"svg-column\">"
        
        // insert SVG circles
        let iteration = 0
        Object.keys(clusterMap).forEach(function(key) {
            
            if (iteration < maxClusterHulls) {
                let firstNode = clusterMap[key][0]
                let color = nodeColorByModularity(firstNode)
                
                let svgElement = "<svg onmouseover=\"onMouseOverHullMenuNode(" + key + ")\" onmouseout=\"onMouseOutHullMenuNode(" + key + ")\" onclick=\"onClickHullMenuNode(" + key + ")\" height=\"16px\" width=\"16px\" viewBox=\"0 0 18 18\"><circle id=\"clusterHullNodeSVGCircle-" + key + "\" cx=\"5\" cy=\"10\" r=\"4\" \
                stroke=\"black\" stroke-width=\"1\" fill=\""
                svgElement += color
                svgElement += "\" /></svg>"
                clusterMenuHtml += svgElement
            }
            iteration += 1
        });
        
        // finish menu and append to div
        clusterMenuHtml += "</div></div></div>"
        d3.select("#clusterHullMenu").html(clusterMenuHtml)
        
        // add tooltips to cluster hull nodes
        iteration = 0
        Object.keys(clusterMap).forEach(function(clusterId) {
            if (iteration < maxClusterHulls) {
                let clusterToolTipDescription = "<u>Cluster metrics</u><br>"
                let clusterMetrics = clusterMetricsMap[clusterId]
                
                // TODO: check why clusterMetrics can be undefined
                if (clusterMetrics !== undefined) {
                    // add all cluster metrics that we can find
                    Object.keys(clusterMetrics).forEach(function(clusterMetric) {
                        let metricPrettyName = clusterMetric.replace(/_/gi, " ").replace(/metric/gi, "")
                        clusterToolTipDescription += metricPrettyName + ": " + "<b>" + clusterMetrics[clusterMetric] + "</b>" + "<br>"
                    })
                    
                    $('#' + 'clusterHullNodeSVGCircle-' + clusterId).attr('data-bs-toggle', 'tooltip')
                    $('#' + 'clusterHullNodeSVGCircle-' + clusterId).attr('data-bs-title', clusterToolTipDescription)
                    $('#' + 'clusterHullNodeSVGCircle-' + clusterId).attr('data-bs-html', 'true')
                    $('#' + 'clusterHullNodeSVGCircle-' + clusterId).attr('data-bs-placement', 'bottom')
                    
                }
            }
        })
    }
    
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}

function getPointArrayForClusterId(id) {
    let pointArray = []
    let clusterId = id.toString()
    
    if (clusterId in clusterMap) {
        clusterMap[clusterId].forEach(function(node, i) {
            pointArray.push([node.x, node.y])
        })
    }
    return pointArray
}

// calculate hull
function getHullFromPointArray(pointArray) {
    let hullArray = hull(pointArray, 60)
    return hullArray
}

// draw a single cluster hull as a polygon 
function drawHull(context, clusterId) {
    let pointArray = getPointArrayForClusterId(clusterId)
    let hullArray = getHullFromPointArray(pointArray)
    let firstNodeInCluster = clusterMap[clusterId][0]
    context.fillStyle = nodeColorByModularity(firstNodeInCluster, 0.2)
    
    context.beginPath();
    
    let firstPoint = hullArray[0]
    context.moveTo(firstPoint[0], firstPoint[1]);
    
    hullArray.forEach(function(arrayElement, i) {
        context.lineTo(arrayElement[0], arrayElement[1]);
    })
    
    context.closePath();
    context.fill();
}

// draw all required cluster hulls (selected/hovered nodes from the menu)
function drawHulls(context) {
    
    // draw a hull if someone hovers ofer a hull menu cluster node 
    if (hoveredClusterHullId !== undefined) {
        drawHull(context, hoveredClusterHullId)
    }
    
    // draw every hull was was selected by a mouse click before 
    selectedClusterHullIds.forEach(clusterId => {
        drawHull(context, clusterId)
    })
}