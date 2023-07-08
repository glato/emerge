/**
* * MARK: - Drawing on canvas
*/
function drawEdges(context) {
    currentGraph.links.forEach(function(d) {
        
        context.beginPath();
        context.moveTo(d.source.x, d.source.y);
        context.lineTo(d.target.x, d.target.y);
        
        if (closeNode == null) { // not hovering over any node
            if (isSearching == false) { // not searching                     
                context.fillStyle = context.strokeStyle = nodeSourceColor = nodeColorByModularity(d.source, 0.7)
                
            } else { // node search is active
                
                if (addSemanticSearch == true) {
                    
                    // the edge is between two nodes that are included in the search OR the edge is between two nodes that includes the search in one of their semantic keywords
                    if ( edgeBetweenSearchTerms(d.source, d.target) || searchTermsIncludedInNodeTags(d.source, d.target) )
                    { 
                        context.strokeStyle = currentActiveEdgeColor
                        context.fillStyle = currentActiveEdgeColor
                    } else { // the edge is not connected to a node which is included in the search
                        context.fillStyle = context.strokeStyle = currentPassiveEdgeColor
                    }
                    
                    
                }  else { // normal search without semantic
                    // the edge is between two nodes that are included in the search
                    if (edgeBetweenSearchTerms(d.source, d.target))                            
                    { 
                        context.strokeStyle = currentActiveEdgeColor
                        context.fillStyle = currentActiveEdgeColor
                    } else { // the edge is not connected to a node which is included in the search
                        context.fillStyle = context.strokeStyle = currentPassiveEdgeColor
                    }
                }
                
                if (addContributorSearch == true ) {
                    // the edge is between two nodes that are included in the search OR the edge is between two nodes that includes the search in one of their semantic keywords
                    if ( searchTermsIncludedInNodeContributors(d.source, d.target) )
                    { 
                        context.strokeStyle = currentActiveEdgeColor
                        context.fillStyle = currentActiveEdgeColor
                    }
                }
                
            }
            
        } else {
            if ((d.target.id == closeNode.id) || (d.source.id == closeNode.id)) { // there is an edge that contains our hovered node
                context.strokeStyle = currentActiveEdgeColor
                context.fillStyle = currentActiveEdgeColor
                
            } else { // node is not included in the edge
                context.fillStyle = context.strokeStyle = nodeColorByModularity(d.source, 0.2)
            }   
        }
        
        // highlight edge if the corresponding nodes are selected
        if (d.source.id.toLowerCase() in selectedNodesMap && d.target.id.toLowerCase() in selectedNodesMap) {
            context.strokeStyle = activeSelectionColor
            context.fillStyle = currentActiveEdgeColor
            context.lineWidth = 2.0;
        } else {
            if (fadeUnselectedNodes == true || normalHeatmapIsActive() || churnHeatmapIsActive() || hotspotHeatmapIsActive()) { // also fade away non-relevant egdes
                context.fillStyle = context.strokeStyle = nodeColorByModularity(d.source, unselectedNodesOpacity)
            } 
            context.lineWidth = 1.0;
        }
        
        context.stroke();
        
        if (closeNode != null && ((d.target.id == closeNode.id) || (d.source.id == closeNode.id))) { // draw an arrow if there is an edge that contains our hovered node
            drawArrowhead(context, d.source, d.target, 5)
            
        } else if (isSearching && ( (searchTermIncludedInNode(d.target) ) && ( searchTermIncludedInNode(d.source)) )) { // draw an arrow if searching is enabled and there's an egde between searched nodes
            drawArrowhead(context, d.source, d.target, 5)
        }
        
        else if (d.source.id.toLowerCase() in selectedNodesMap && d.target.id.toLowerCase() in selectedNodesMap) {
            drawArrowhead(context, d.source, d.target, 5)
        }                    
        
    });
}

function drawNodes(context) {
    currentGraph.nodes.forEach(function(d, i) {
        
        context.beginPath();
        
        //render outer circle if node was selected
        if (d.id.toLowerCase() in selectedNodesMap) {
            
            context.arc(d.x, d.y, d.radius + 2.0, 0, TWO_TIMES_PI);
            context.fillStyle = '#FF0000' //activeSelectionColor
            drawNodeLabel(d.id, d.x + 14, d.y - 7)
            context.fill();
        }
        
        context.arc(d.x, d.y, d.radius, 0, TWO_TIMES_PI, true);
        
        if (fadeUnselectedNodes == true || normalHeatmapIsActive() || churnHeatmapIsActive() || hotspotHeatmapIsActive()) {
            context.strokeStyle = nodeStrokeStyle
            context.fillStyle = hexToRGB(nodeStrokeStyle, unselectedNodesOpacity)
            context.stroke();
            
            if (nodeLabelsEnabled) {
                context.fillStyle = currentPassiveNodeLabelColor;
                drawNodeLabel(d.id, d.x + 14, d.y - 7)
                context.fillStyle = nodeColorByModularity(d, unselectedNodesOpacity)
            }
            
        } else {
            
            if (closeNode == null) { // not hovering over any node
                if (isSearching == false) {
                    
                    context.fillStyle = nodeColorByModularity(d)
                    context.strokeStyle = nodeStrokeStyle;
                    context.stroke();
                    
                    if (nodeLabelsEnabled) {
                        context.fillStyle = currentActiveNodeLabelColor;
                        drawNodeLabel(d.id, d.x + 14, d.y - 7)
                        context.fillStyle = nodeColorByModularity(d)
                    }
                    
                } else { // searching for nodes
                    
                    // normal (non-semantic) search
                    if ( addSemanticSearch == false && normalSearch(d)) {
                        
                        context.fillStyle = nodeColorByModularity(d)
                        context.strokeStyle = nodeStrokeStyle;
                        context.stroke();
                        
                        context.fillStyle = currentActiveNodeLabelColor;
                        drawNodeLabel(d.id, d.x + 14, d.y - 7)
                        context.fillStyle = nodeColorByModularity(d)
                        
                        searchResults += 1
                        
                    } else if ( addSemanticSearch == true && (searchTermIncludedInNode(d) || searchTermIncludedInNodeTags(d)) )
                    // add semantic search
                    // the node is included in the current search OR if the search in included in one of the node's semantic tags 
                    // draw a highlight circle behind the found node due to semantic search
                    {
                        if ( searchTermIncludedInNodeTags(d) )
                        {
                            context.fillStyle = currentActiveNodeLabelColor;
                            drawNodeLabel(d.id, d.x + 14, d.y - 7)
                            
                            drawNodeHighlight(d, nodeColorByModularity(d, 1.0))
                            context.strokeStyle = nodeStrokeStyle;
                            context.stroke();
                            
                            drawNodeHighlight(d, semanticHeaderYellow, 2)
                            context.strokeStyle = nodeStrokeStyle;
                            context.stroke();
                            
                            searchResults += 1
                            
                        } else {
                            
                            context.fillStyle = nodeColorByModularity(d)
                            context.strokeStyle = nodeStrokeStyle;
                            context.stroke();
                            
                            context.fillStyle = currentActiveNodeLabelColor;
                            drawNodeLabel(d.id, d.x + 14, d.y - 7)
                            context.fillStyle = nodeColorByModularity(d)
                            
                            searchResults += 1
                        }
                        
                    } else {
                        context.fillStyle = nodeColorByModularity(d, 0.2)
                        context.strokeStyle = hexToRGB(nodeStrokeStyle, 0.2)
                        context.stroke();
                        
                        if (nodeLabelsEnabled) {
                            context.fillStyle = currentPassiveNodeLabelColor;
                            drawNodeLabel(d.id, d.x + 14, d.y - 7)
                            context.fillStyle = nodeColorByModularity(d, 0.2)
                        }
                    }
                }
                
                // contributors search
                if (addContributorSearch == true && searchTermIncludedInNodeContributors(d)) {
                    
                    context.fillStyle = currentActiveNodeLabelColor;
                    drawNodeLabel(d.id, d.x + 14, d.y - 7)
                    
                    drawNodeHighlight(d, nodeColorByModularity(d, 1.0))
                    context.strokeStyle = nodeStrokeStyle;
                    context.stroke();
                    
                    drawNodeHighlight(d, contributorsPurple, 2)
                    context.strokeStyle = nodeStrokeStyle;
                    context.stroke();
                    
                    searchResults += 1
                }
                
            } else { // hovering over a node
                if (isConnected(d, closeNode)) { // node is connected to hovered node
                    context.fillStyle = nodeColorByModularity(d)
                    context.strokeStyle = nodeStrokeStyle;
                    context.stroke();
                    
                    // show/highlight node label of every connected node from the hovered node
                    context.fillStyle = currentActiveNodeLabelColor;
                    drawNodeLabel(d.id, d.x + 14, d.y - 7)
                    context.fillStyle = nodeColorByModularity(d)
                    
                } else if ( hoverCoupling == true && nodeNamesHaveChangeCoupling(d.id, closeNode.id) ) {

                    context.fillStyle = currentActiveNodeLabelColor;
                    drawNodeLabel(d.id, d.x + 14, d.y - 7)
                    
                    drawNodeHighlight(d, nodeColorByModularity(d, 1.0))
                    context.strokeStyle = nodeStrokeStyle;
                    context.stroke();
                    
                    drawNodeHighlight(d, changeCouplingColor, 2)
                    context.strokeStyle = nodeStrokeStyle;
                    context.stroke();

                } else { // node is not connected
                    
                    if (d.id.toLowerCase() in selectedNodesMap) {
                        context.strokeStyle = nodeStrokeStyle
                        context.fillStyle = nodeColorByModularity(d)
                        context.stroke();
                    } else { 
                        context.strokeStyle = hexToRGB(nodeStrokeStyle, 0.2)
                        context.fillStyle = nodeColorByModularity(d, 0.2)
                        context.stroke();
                    }
                    
                    if (nodeLabelsEnabled) {
                        context.fillStyle = currentPassiveNodeLabelColor;
                        drawNodeLabel(d.id, d.x + 14, d.y - 7)
                        context.fillStyle = nodeColorByModularity(d, 0.2)
                    }
                }
            }
            
        } // else not fade away unselected nodes
        
        context.fill();
        
        if (i == currentGraph.nodes.length - 1) { // dont call this to often due to performance
            
            if (closeNode) {
                context.beginPath();
                drawNode(closeNode)
                
                if (closeNode.id.toLowerCase() in selectedNodesMap) {
                    context.fillStyle = activeSelectionColor
                } else {
                    context.fillStyle = nodeColorByModularity(closeNode)
                }
                
                context.fill();
                context.strokeStyle = "#000000";
                context.lineWidth = 1.0;
                context.stroke();
                
                drawNodeToolTip(closeNode.id, closeNode.x + 8, closeNode.y - 7, closeNode.metrics)
            }
        }
    });
}

/**
* * MARK: - Connectivity checks 
*/
let linkedByIndex = {};

function isConnected(a, b) {
    return isConnectedAsTarget(a, b) || isConnectedAsSource(a, b) || a.id === b.id;
}

function isConnectedAsSource(a, b) {
    return linkedByIndex[`${a.id},${b.id}`];
}

function isConnectedAsTarget(a, b) {
    return linkedByIndex[`${b.id},${a.id}`];
}



function drawLink(d) {
    context.moveTo(d.source.x, d.source.y);
    context.lineTo(d.target.x, d.target.y);
}

function drawNode(d) {
    context.arc(d.x, d.y, d.radius, 0, TWO_TIMES_PI);
}

function drawNodeHighlight(node, color, radiusOffset) {
    context.arc(node.x, node.y, node.radius + radiusOffset, 0, TWO_TIMES_PI);
    context.fillStyle = color
    context.strokeStyle = color;
    context.stroke();
    context.fill();
}

function drawNodeLabel(text, xPos, yPos) {
    const fontSize = 8
    context.font = fontSize + 'px Helvetica';
    context.fillText(text, xPos, yPos);
}

function stringIncludedInNodeTags(string, node) {
    let propertyNames = Object.getOwnPropertyNames(node.metrics)
    let searchedTag = 'metric_tag_' + string
    let found = false
    
    let tagProperties = propertyNames.filter(function(property) {
        return property.startsWith('metric_tag_')
    })
    
    tagProperties.forEach(function(propertyName) {
        if (propertyName.toLowerCase().includes(string.toLowerCase())) {
            found = true
        }
    })
    
    return found
}

function stringIncludedInNodeContributors(string, node) {
    let found = false
    if (node.hasOwnProperty('metrics')) {
        let metrics = node['metrics']
        if ('metric_git_contributors' in metrics) {
            const contributors = metrics['metric_git_contributors']
            contributors.forEach(function(name) {
                if (name.toLowerCase().includes(string.toLowerCase())) {
                    found = true
                }
            })
        }
    }
    
    return found
}

function drawNodeToolTip(text, xPos, yPos, nodeMetrics) {
    
    // $('#overallStatisticsModal').modal('show');

    // Calculate scale factor to maintain fixed size when d3 canvas zoom changes.
    const zoomTransform = d3.zoomTransform(context.canvas);
    const scaleFactor = 1 / zoomTransform.k;

    // Scale linewidth and font so they're unchanged when zooming:
    context.lineWidth = scaleFactor;
    const scaledFontSize = 14 * scaleFactor;
    context.font = scaledFontSize + 'px Helvetica';

    // Extract code metrics and semantic keywords from `nodeMetrics` object:
    const codeMetricLabels = formatCodeMetricLabels(nodeMetrics);
    const semanticKeywords = formatSemanticKeywords(nodeMetrics);

    // Set the text box width based on the maximum text width:
    const allTextLabels = [text, ...codeMetricLabels, ...semanticKeywords];
    const textBoxWidth = Math.max(...allTextLabels.map(text => context.measureText(text).width));
    
    // Offset text from left edge of box:
    const xTextOffset = 5 * scaleFactor;
    const xText = xPos + xTextOffset;
    // Offset text from bottom edge of box:
    const yTextOffset = 5 * scaleFactor;
    // yCurrent represents the bottom edge of the box, which changes for each box:
    let yCurrent = yPos;

    // Define dimensions of each box/row containing metrics/labels/tags:
    const boxWidth = textBoxWidth + 2 * xTextOffset;
    const boxHeight = scaledFontSize * 1.286;
    const boxDefaults = { x: xPos, width: boxWidth, height: boxHeight };

    // Draw the header/title with node label:
    drawBox(context,
        { y: yCurrent - boxHeight, ...boxDefaults },
        { strokeColor: hexToRGB("#333333", 1.0), fillColor: hexToRGB("#0069d9", 1.0) },
    );
    context.fillStyle = hexToRGB("#FFFFFF", 0.8);
    context.fillText(text, xText, yCurrent - yTextOffset);
    
    // Draw boxes/rows for all metric labels
    for (metricLabel of codeMetricLabels) {
        // Shift `yCurrent` (bottom edge of the box) by the boxHeight:
        yCurrent += boxHeight;
        
        // Draw box with current metric label:
        drawBox(context,
            { y: yCurrent - boxHeight, ...boxDefaults },
            { strokeColor: toolTipMetricItemBoxColor, fillColor: toolTipMetricItemBoxFillColor },
        );
        context.fillStyle = toolTipMetricItemTextColor;
        context.fillText(metricLabel, xText, yCurrent - yTextOffset);
    }
    
    // Draw boxes/rows for tfidf semantic keywords section:
    if (semanticKeywords.length) {
        // Shift `yCurrent` (bottom edge of the box) by the boxHeight:
        yCurrent += boxHeight;
        
        // Draw the header/title for the tfidf semantic keywords section:
        drawBox(context,
            { y: yCurrent - boxHeight, ...boxDefaults },
            { strokeColor: hexToRGB("#333333", 1.0), fillColor: hexToRGB("#f5bc42", 1.0) },
        );
        context.fillStyle = hexToRGB("#333333", 0.8);
        context.fillText('Semantic keywords', xText, yCurrent - yTextOffset);
        
        // Draw boxes/rows for all tfidf semantic keywords:
        for (keyword of semanticKeywords) {
            
            // Shift `yCurrent` (bottom edge of the box) by the boxHeight:
            yCurrent += boxHeight;
            
            // Draw box with current tfidf semantic keyword:
            drawBox(context,
                { y: yCurrent - boxHeight, ...boxDefaults },
                { strokeColor: toolTipMetricItemBoxColor, fillColor: toolTipMetricItemBoxFillColor },
            );
            context.fillStyle = toolTipMetricItemTextColor;
            context.fillText(keyword, xText, yCurrent - yTextOffset);
        }
    }
}


function drawBox(context, {x, y, width, height}, {strokeColor, fillColor}) {
    // Interesting bug: on Safari it seems to cause random lags if you do fillStyle/fillRect BEFORE strokeStyle/strokeRect
    context.strokeStyle = strokeColor;
    context.strokeRect(x, y, width, height);
    
    context.fillStyle = fillColor
    context.fillRect(x, y, width, height);
}

function formatCodeMetricLabels(nodeMetrics) {
    return Object.entries(nodeMetrics)
        .filter(([key, _]) => !key.startsWith("metric_tag"))
        .map(([key, value]) => key.replace('metric_', '').replace(/_/gi, " ") + ": " + value);
}

function formatSemanticKeywords(nodeMetrics) {
    return Object.keys(nodeMetrics)
        .filter(key => key.startsWith("metric_tag"))
        .map(key => key.replace('metric_tag', '').replace(/_/gi, ""));
}

// borrowed from Scott Johnson / https://gist.github.com/jwir3/d797037d2e1bf78a9b04838d73436197 with minor adjustments
function drawArrowhead(context, from, to, radius) {
    const x_center = 0.5 * (from.x + to.x)
    const y_center = 0.5 * (from.y + to.y)
    
    let angle;
    let x;
    let y;
    
    context.beginPath();
    
    angle = Math.atan2(to.y - from.y, to.x - from.x)
    x = radius * Math.cos(angle) + x_center;
    y = radius * Math.sin(angle) + y_center;
    
    context.moveTo(x, y);
    
    angle += ONE_THIRD_TWO_TIMES_PI
    x = radius * Math.cos(angle) + x_center;
    y = radius * Math.sin(angle) + y_center;
    
    context.lineTo(x, y);
    
    angle += ONE_THIRD_TWO_TIMES_PI
    x = radius * Math.cos(angle) + x_center;
    y = radius * Math.sin(angle) + y_center;
    
    context.lineTo(x, y);
    context.closePath();
    context.fill();
}

function initNodeColorMap() {
    currentGraph.nodes.forEach(function(node, i) {
        nodeColorMap[node.id] = hexToRGB(color(node.metric_file_result_dependency_graph_louvain_modularity_in_file), 1.0)
    })
}

function nodeColorByModularity(node, alpha = 1.0) {
    if (currentGraphType.includes('file_result') || currentGraphType.includes('filesystem')) {
        if ('metric_file_result_dependency_graph_louvain_modularity_in_file' in node) {
            return hexToRGB(color(node.metric_file_result_dependency_graph_louvain_modularity_in_file), alpha)
        } else if ('directory' in node) {
            if (node.directory == true) {
                return hexToRGB(directoryNodeColor)
            }
        }
    } else {
        if (currentGraphType.includes('entity_result_dependency_graph')) {
            if ('metric_entity_result_dependency_graph_louvain_modularity_in_entity' in node) {
                return hexToRGB(color(node.metric_entity_result_dependency_graph_louvain_modularity_in_entity), alpha)
            }
        }
        if (currentGraphType.includes('entity_result_inheritance_graph')) {
            if ('metric_entity_result_inheritance_graph_louvain_modularity_in_entity' in node) {
                return hexToRGB(color(node.metric_entity_result_inheritance_graph_louvain_modularity_in_entity), alpha)
            }
        }
        
        if (currentGraphType.includes('entity_result_complete_graph')) {
            if ('metric_entity_result_complete_graph_louvain_modularity_in_entity' in node) {
                return hexToRGB(color(node.metric_entity_result_complete_graph_louvain_modularity_in_entity), alpha)
            }
        }
    }
    
    return hexToRGB(defaultNodeColor) 
}

