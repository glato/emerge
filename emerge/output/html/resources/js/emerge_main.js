
// Some JS code is derived/borrowed or heavily inspired from demos/examples by the following people:
// Mike Bostock - https://github.com/mbostock, https://bost.ocks.org/mike/
// Tom Roth - https://bl.ocks.org/puzzler10/4438752bb93f45dc5ad5214efaa12e4a
// Ma'moun othman/@mamounothman - https://stackoverflow.com/questions/61800343/d3-js-version-5-chart-to-pdf
// Sam Leach/@SamuelLeach - https://gist.github.com/samuelleach/5497403
// Pranav C Balan - https://stackoverflow.com/questions/41287778/get-all-possible-object-keys-from-a-list-of-objects-javascript-typescript
// If I missed someone or gave wrong credit, please contact me and I'll update this.

const activeNodeLabelColor = hexToRGB("#333333", 0.6)
const passiveNodeLabelColor = hexToRGB("#333333", 0.2)
const dmActiveNodeLabelColor = hexToRGB("#DDDDDD", 0.6)
const dmPassiveNodeLabelColor = hexToRGB("#DDDDDD", 0.2)

const activeEdgeColor = hexToRGB("#AAAAAA", 1.0);
const passiveEdgeColor = hexToRGB("#AAAAAA", 0.2);
const dmActiveEdgeColor = hexToRGB("#888888", 0.8)
const dmPassiveEdgeColor = hexToRGB("#888888", 0.2)

const toolTipMetricItemTextColor = hexToRGB("#333333", 0.7);
const toolTipMetricItemBoxColor = hexToRGB("#333333", 1.0);
const toolTipMetricItemBoxFillColor = hexToRGB("#f7f7f7", 1.0);

const activeSelectionColor = '#FF0000'
const directoryNodeColor = '#3b8cff'
const fileNodeColor = '#d1e3ff'
const defaultNodeColor = '#1f77b4'
const semanticHeaderYellow = '#f5bc42'
const contributorsPurple = '#ff00ff'
const changeCouplingColor = '#ff0000'

let metricNameMap = {
    "metric_ws_complexity_in_file" : "whitespace complexity",
    "metric_number_of_methods_in_file" : "number of methods (file)",
    "metric_number_of_methods_in_entity" : "number of methods (entity)",
    "metric_sloc_in_file" : "source lines of code (file)",
    "metric_sloc_in_entity" : "source lines of code (entity)",
    "metric_fan_in_dependency_graph" : "fan in (dependency graph)",
    "metric_fan_out_dependency_graph" : "fan out (dependency graph)",
    "metric_fan_in_inheritance_graph" : "fan in (inheritance graph)",
    "metric_fan_out_inheritance_graph" : "fan out (inheritance graph)",
    "metric_fan_in_complete_graph" : "fan in (complete graph)",
    "metric_fan_out_complete_graph" : "fan out (complete graph)",

    //"metric_file_result_dependency_graph_louvain_modularity_in_file" : null,

    "metric_git_code_churn" : "code churn (git)",
    "metric_git_ws_complexity" : "whitespace complexity (git)",
    "metric_git_sloc" : "source lines of code (git)",

    // "metric_git_contributors" : "contributors (git)",
    
    "metric_git_number_authors": "number of authors (git)",
    "metric_fan_in_complete_graph" : "fan in (complete graph)",
    "metric_fan_out_complete_graph" : "fan out (complete graph)"
}

/**
* * MARK: - Math constants
*/
const TWO_TIMES_PI = 2 * Math.PI
const ONE_THIRD_TWO_TIMES_PI = (1.0 / 3.0) * TWO_TIMES_PI

/**
* * MARK: - UI workarounds
*/
// workaround from https://stackoverflow.com/questions/6985507/one-time-page-refresh-after-first-page-load to fix strange safari full screen loading problems
let userAgent = navigator.userAgent.toLowerCase();
if (userAgent.includes('safari')) {
    window.onload = function() {
        if (!window.location.hash) {
            window.location = window.location + '#loaded';
            window.location.reload();
        }
    }
}

// Workaround to prevent buttons that trigger modals to stay focused after dismiss (https://stackoverflow.com/questions/30322918/bootstrap-modal-restores-button-focus-on-close)
$('body').on('hidden.bs.modal', '.modal', function() {
    $('#buttonShowOverallMetrics').blur();
    $('#buttonShowOverallStatistics').blur();
});

// cancel the node search by pressing the escape key
$(document).keyup(function(e) {
    if (e.key === "Escape") {
        cancelNodeSearch()
    }
});

function setDarkMode(mode) {
    if (mode == true) {
        darkMode = true
        currentActiveNodeLabelColor = dmActiveNodeLabelColor
        currentPassiveNodeLabelColor = dmPassiveNodeLabelColor
        currentActiveEdgeColor = dmActiveEdgeColor
        currentPassiveEdgeColor = dmPassiveEdgeColor
        simulationUpdate()
    } else {
        darkMode = false
        currentActiveNodeLabelColor = activeNodeLabelColor
        currentPassiveNodeLabelColor = passiveNodeLabelColor
        currentActiveEdgeColor = activeEdgeColor
        currentPassiveEdgeColor = passiveEdgeColor
        simulationUpdate()
    }
}

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

let heatmapMerged = false
let heatmapActive = false
let heatmapChurn = false
let heatmapHotspot = false

let selectedNodesMap = {}
var unselectedNodesOpacity = 0.20
let fadeUnselectedNodes = false
let currentActiveNodeLabelColor = activeNodeLabelColor
let currentPassiveNodeLabelColor = passiveNodeLabelColor

let currentActiveEdgeColor = activeEdgeColor
let currentPassiveEdgeColor = passiveEdgeColor

let dateRangePickerFrom = ""
let dateRangePickerTo = ""
let fileResultPrefix = ""
let fileResultPrefixFull = ""

let includeGitMetrics = false
let commit_dates = []
let commit_first_date = ""
let commit_last_date = ""

if (typeof commit_metrics !== 'undefined') {
    fileResultPrefix = commit_metrics[0].file_result_prefix // TODO: pass/extract as/from extra common git metrics dict
    fileResultPrefixFull = commit_metrics[0].file_result_prefix_full
    commit_dates = commit_metrics.map(x => x.date);
    commit_first_date = commit_dates[0]
    commit_last_date = commit_dates[commit_dates.length - 1]
    dateRangePickerFrom = commit_first_date
    dateRangePickerTo = commit_last_date
    includeGitMetrics = true
}

let gitMetricsIndexFrom = 0
let gitMetricsIndexTo = 0

let nodeColorMap = {}

const nodeStrokeStyle = "#333333";

let darkMode = false
let isSearching = false
let addSemanticSearch = false
let addContributorSearch = false

let hoverCoupling = false

let searchString = ""

let searchTerms = []
let searchResults = 0

const radius = 7;
const height = window.innerHeight * 2;
const graphWidth = window.innerWidth * 2;

const maxClusterHulls = 20
let selectedClusterHullIds = []
let hoveredClusterHullId = undefined

let nodeLabelsEnabled = false

let currentTranslation = {
    horizontal: 0,
    vertical: 0,
    lastDirection: ""
}

let activeMetrics
let currentMetricKeys

let currentGraphType
let closeNode;

function setDirection(direction) {
    currentTranslation.lastDirection = direction
}

function toggleNodeLabels() {
    nodeLabelsEnabled = !nodeLabelsEnabled
    simulationUpdate()
}

let zoom_handler = d3.zoom()
.on("zoom", zoomed);

let graphCanvas = d3.select('#graphDiv').append('canvas')
.attr('width', graphWidth + 'px')
.attr('height', height + 'px')
.attr('id', 'mainCanvas')
.node();

let graphData = {}
let currentGraph = ''

let clusterMap = {}
let clusterMetricsMap = {}

let statistics
let overall_metric_results

initAppConfig()
initHeatmapSwitches()

initHoverCouplingSwitch()

initSemanticSearchSwitch()
initContributorSearchSwitch()

setInitialDarkMode()
prepareGraphStructures()
initAppUI()

let context = graphCanvas.getContext('2d');

// nice fix from https://stackoverflow.com/questions/8696631/canvas-drawings-like-lines-are-blurry to remove blurry drawing
graphCanvas.style.height = (height / 2) + "px";
graphCanvas.style.width = (graphWidth / 2) + "px";
graphCanvas.getContext('2d').scale(2, 2);

let div = d3.select("body").append("div")
.attr("class", "tooltip")
.style("opacity", 0);

let currentChargeForce = -500
let currentLinkDistance = 20
let simulation

let transform = d3.zoomIdentity;

// heatmap
var heat = simpleheat('mainCanvas');

// bring back d3 schemeCategory20 to live
const schemeCategory20 = "1f77b4aec7e8ff7f0effbb782ca02c98df8ad62728ff98969467bdc5b0d58c564bc49c94e377c2f7b6d27f7f7fc7c7c7bcbd22dbdb8d17becf9edae5"

function d3ColorExport(specifier) {
    let n = specifier.length / 6 | 0,
    colors = new Array(n),
    i = 0;
    while (i < n) colors[i] = "#" + specifier.slice(i * 6, ++i * 6);
    return colors;
}

// important to define the domain for the ordinal scale
const color = d3.scaleOrdinal(d3ColorExport(schemeCategory20))
.domain([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19])

function initModals() {
    const modal = document.getElementById('timeSeriesModal')
    modal.addEventListener('hidden.bs.modal', event => {
        d3.select("#timeSeriesComplexityChart").remove();
        d3.select("#timeSeriesChurnChart").remove();
        d3.select("#timeSeriesSlocChart").remove();
    })
    
    const chordModal = document.getElementById('changeCouplingModal')
    chordModal.addEventListener('hidden.bs.modal', event => {
        d3.select("#svg_change_coupling_chord_diagram").remove();
    })
}

function setInitialDarkMode() {
    if (document.body.getAttribute("data-theme") == "dark") {
        currentActiveNodeLabelColor = dmActiveNodeLabelColor
        currentPassiveNodeLabelColor = dmPassiveNodeLabelColor
        currentActiveEdgeColor = dmActiveEdgeColor
        currentPassiveEdgeColor = dmPassiveEdgeColor
        darkMode = true
    } else {
        currentActiveNodeLabelColor = activeNodeLabelColor
        currentPassiveNodeLabelColor = passiveNodeLabelColor
        currentActiveEdgeColor = activeEdgeColor
        currentPassiveEdgeColor = passiveEdgeColor
        darkMode = false
    }
}

/**
* * MARK: - Translations on canvas
*/
function translateCanvas(direction) {
    switch (direction) {
        case 'left':
        transform.x += 100
        simulationUpdate()
        break;
        
        case 'down':
        transform.y -= 100
        simulationUpdate()
        break;
        
        case 'right':
        transform.x -= 100
        simulationUpdate()
        break;
        
        case 'up':
        transform.y += 100
        simulationUpdate()
        break;
    }
}

/**
* * MARK: - Adjusting style 
*/

function unselectedOpacityChange(val) {
    unselectedNodesOpacity = val / 100.0
    simulationUpdate()
}

/**
* * MARK: - Zooming and scaling on canvas
*/
function zoomed(event) {
    transform = event.transform;
    simulationUpdate();
}

function zoomIn() {
    d3.select(graphCanvas)
    .call(zoom_handler.scaleBy, 2)
    .call(d3.zoom().scaleExtent([1 / 10, 8]).on("zoom", zoomed))
    simulationUpdate()
}

function zoomOut() {
    d3.select(graphCanvas)
    .call(zoom_handler.scaleBy, 0.5)
    .call(d3.zoom().scaleExtent([1 / 10, 8]).on("zoom", zoomed))
    simulationUpdate()
}

startWithGraph('file_result_dependency_graph')

zoomOut() // initialliy zoom out a bit

/**
* * MARK: - Called on startup an d every time you change a graph
*/
function startWithGraph(graphType, chargeForce = currentChargeForce, linkDistance = currentLinkDistance) {
    
    activeMetrics = []
    currentMetricKeys = []
    
    currentGraphType = graphType
    
    currentLinkDistance = linkDistance
    currentChargeForce = chargeForce
    currentLinkDistance = linkDistance
    
    resetSimulationData()
    
    currentGraph = JSON.parse(JSON.stringify(graphData[graphType]['graph']))
    statistics = graphData[graphType]['statistics']
    overall_metric_results = graphData[graphType]['overall_metric_results']
    clusterMetricsMap = graphData[graphType]['cluster_metrics_map']
    
    addGitMetricToFileNodes()
    
    createStatistics();
    createOverallMetricResults();
    
    currentGraph.nodes.forEach(function(d, i) {
        d.radius = radius
        
        if (!d.hasOwnProperty('metrics')) {
            d.metrics = {}
        }
        
        for (let key in d) {
            
            if (key.includes('metric_')) {
                d.metrics[key] = d[key]
                if (!currentMetricKeys.includes(key)) {
                    // do not include tag/tfidf metrics in the 'apply metrics' dropDown menu
                    if (!key.includes('metric_tag')) {
                        currentMetricKeys.push(key)
                    }                            
                }
            }
        }
    });
    
    setupGraphClustersById();
    
    createClusterHullMenu();
    createMetricsMenuEntries();
    
    updateAppUI()
    
    initNodeColorMap();
    
    enableSearchInput();
    enableNodeSelection();
    
    addToolTipsToMetricEntries();
    addTooltipToHoverCoupling();
    addTooltipToContributorSearch();
    addToolTipsToHeatMap();
    addToolTipToShortcuts();
    addTooltipUnselectedOpacity();
    addTooltipSemanticSearch();
    addTooltipClusterHulls();
    
    currentGraph.links.forEach((d) => {
        linkedByIndex[`${d.source},${d.target}`] = true;
    });
    
    simulation = d3.forceSimulation()
    .force("center", d3.forceCenter(graphWidth / 4, height / 4))
    .force("x", d3.forceX(graphWidth / 2).strength(0.1))
    .force("y", d3.forceY(height / 2).strength(0.1))
    .force("charge", d3.forceManyBody().strength(currentChargeForce))
    .force("link", d3.forceLink()
    .strength(1)
    .distance(currentLinkDistance)
    .id(function(d) {
        return d.id;
    }))
    .alphaTarget(0)
    .alphaDecay(0.05)
    
    addGraphTypeSelectionToMenu()
    
    addTooltipProjectInfo();
    addTooltipGraphInfo();
    
    d3.select(graphCanvas)
    .call(d3.drag().subject(dragsubject).on("start", dragstarted).on("drag", dragged).on("end", dragended))
    .call(d3.zoom().scaleExtent([1 / 10, 8]).on("zoom", zoomed))
    
    function dragsubject(event) {
        
        let i,
        x = transform.invertX(event.x),
        y = transform.invertY(event.y),
        dx,
        dy;
        
        for (i = currentGraph.nodes.length - 1; i >= 0; --i) {
            node = currentGraph.nodes[i];
            dx = x - node.x;
            dy = y - node.y;
            
            if (dx * dx + dy * dy < radius * radius) {
                
                node.x = transform.applyX(node.x);
                node.y = transform.applyY(node.y);
                
                return node;
            }
        }
    }
    
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = transform.invertX(event.x);
        event.subject.fy = transform.invertY(event.y);
    }
    
    function dragged(event) {
        event.subject.fx = transform.invertX(event.x);
        event.subject.fy = transform.invertY(event.y);
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    
    d3.select("canvas").on("mousemove", (event) => {
        let p = d3.pointer(event);
        let invX = transform.invertX(p[0])
        let invY = transform.invertY(p[1])
        
        let foundNode = simulation.find(transform.invertX(p[0]), transform.invertY(p[1]));
        
        // check within a close area if hovered point is nearby of foundNode
        if ((Math.abs(foundNode.x - invX) < radius) && (Math.abs(foundNode.y - invY) < radius)) {
            closeNode = simulation.find(transform.invertX(p[0]), transform.invertY(p[1]));
        } else {
            closeNode = null
        }
        
        simulationUpdate();
    })
    
    simulation.nodes(currentGraph.nodes)
    .on("tick", simulationUpdate);
    
    simulation.force("link")
    .links(currentGraph.links);
}

// Based on https://bl.ocks.org/jodyphelan/5dc989637045a0f48418101423378fbd
function simulationUpdate() {
    
    context.save();
    
    context.clearRect(0, 0, graphWidth, height);
    context.translate(transform.x, transform.y);
    context.scale(transform.k, transform.k);
    
    // draw heatmap
    if (mergedHeatmapIsActive() || normalHeatmapIsActive() || churnHeatmapIsActive() || hotspotHeatmapIsActive()) {
        drawHeatMap(context)
    }
    
    // this is pretty cpu hungry
    drawHulls(context)
    
    // draw edges
    drawEdges(context)
    
    // Draw nodes
    drawNodes(context)
    
    context.restore();
}

/**
* * MARK: - Handling of data structures
*/
function prepareGraphStructures() {
    if (typeof file_result_dependency_graph !== 'undefined') {
        graphData['file_result_dependency_graph'] = {}
        graphData['file_result_dependency_graph']['graph'] = file_result_dependency_graph
        graphData['file_result_dependency_graph']['statistics'] = file_result_dependency_graph_statistics
        graphData['file_result_dependency_graph']['overall_metric_results'] =
        file_result_dependency_graph_overall_metric_results
        graphData['file_result_dependency_graph']['cluster_metrics_map'] = file_result_dependency_graph_cluster_metrics_map
        currentGraphType = 'file_result_dependency_graph'
    }

    if (typeof entity_result_dependency_graph !== 'undefined') {
        graphData['entity_result_dependency_graph'] = {}
        graphData['entity_result_dependency_graph']['graph'] = entity_result_dependency_graph
        graphData['entity_result_dependency_graph']['statistics'] = entity_result_dependency_graph_statistics
        graphData['entity_result_dependency_graph']['overall_metric_results'] =
        entity_result_dependency_graph_overall_metric_results
        graphData['entity_result_dependency_graph']['cluster_metrics_map'] = entity_result_dependency_graph_cluster_metrics_map
        currentGraphType = 'entity_result_dependency_graph'
    }
    
    if (typeof entity_result_inheritance_graph !== 'undefined') {
        graphData['entity_result_inheritance_graph'] = {}
        graphData['entity_result_inheritance_graph']['graph'] = entity_result_inheritance_graph
        graphData['entity_result_inheritance_graph']['statistics'] = entity_result_inheritance_graph_statistics
        graphData['entity_result_inheritance_graph']['overall_metric_results'] =
        entity_result_inheritance_graph_overall_metric_results
        graphData['entity_result_inheritance_graph']['cluster_metrics_map'] = entity_result_inheritance_graph_cluster_metrics_map
    }
    
    if (typeof entity_result_complete_graph !== 'undefined') {
        graphData['entity_result_complete_graph'] = {}
        graphData['entity_result_complete_graph']['graph'] = entity_result_complete_graph
        graphData['entity_result_complete_graph']['statistics'] = entity_result_complete_graph_statistics
        graphData['entity_result_complete_graph']['overall_metric_results'] =
        entity_result_complete_graph_overall_metric_results
        graphData['entity_result_complete_graph']['cluster_metrics_map'] = entity_result_complete_graph_cluster_metrics_map
    }
    
    if (typeof filesystem_graph !== 'undefined') {
        graphData['filesystem_graph'] = {}
        graphData['filesystem_graph']['graph'] = filesystem_graph
        graphData['filesystem_graph']['statistics'] = filesystem_graph_statistics
        graphData['filesystem_graph']['overall_metric_results'] = filesystem_graph_overall_metric_results
        graphData['filesystem_graph']['cluster_metrics_map'] = filesystem_graph_cluster_metrics_map
    }
}

function resetSimulationData() {
    if (simulation !== undefined) {
        simulation.stop()
    }
    
    metricKeys = nodesData = linksData = []
    simulation = undefined
}

// based on https://bocoup.com/blog/smoothly-animate-thousands-of-points-with-html5-canvas-and-d3 / Peter Beshai
// basically animates the increase/decrease of the node radius based on chosen metrics
function animateRadiusWithMetric(metricName) {
    
    let addedMetric = true
    if (activeMetrics.includes(metricName)) {
        removeItemAll(activeMetrics, metricName)
        addedMetric = false
    } else {
        activeMetrics.push(metricName)
        addedMetric = true
    }
    
    // console.log(metricName)
    const duration = 250;
    const ease = d3.easeCubic;
    
    timer = d3.timer((elapsed) => {
        // compute how far through the animation we are (0 to 1)
        const t = Math.min(1, ease(elapsed / duration));
        
        // update point positions (interpolate between source and target)
        currentGraph.nodes.forEach(node => {
            if (metricName in node.metrics) {
                // this resets all nodes back to the default radius
                let newRadius = 0
                
                // now interpolate for every x between f(0) and f(1): f(x) = f(0) * (1-x) + f(1) * x
                if (addedMetric) {                            
                    newRadius = node.radius * (1 - t) + (node.radius + (node.metrics[metricName] * analysis_config['metrics']['radius_multiplication'][metricName] )) * t;
                    
                    if (newRadius > node.radius) {
                        node.radius = newRadius
                    }
                    
                } else {
                    newRadius = node.radius * (1 - t) + (node.radius - (node.metrics[metricName] * analysis_config['metrics']['radius_multiplication'][metricName] )) * t;
                    if (newRadius > radius) {
                        node.radius = newRadius
                    } else {
                        node.radius = radius
                    }
                }
            }
        });
        
        // if this animation is over
        if (t === 1) {
            // always make sure that node sizes return to default if no metric is active
            if (activeMetrics.length == 0) {
                currentGraph.nodes.forEach(node => {
                    node.radius = radius
                })
            }
            
            // stop this timer since we are done animating.
            timer.stop();
        }
        
        // update what is drawn on screen
        simulationUpdate();
    });
}

/**
* * MARK: - Create/update the HTML/Bootstrap UI
*/

function cancelNodeSearch() {
    $('#inputNodeSearch').val('')
    $('#inputNodeSearchLabel').text('Search inactive')
    searchString = ""
    
    searchTerms = []
    
    isSearching = false
    simulationUpdate()
}

// setup keyboard shortcut keys for node selection
// shift + 's' key: select/unselect node
// shift + 'e' key: expand selected nodes level deeper
// shift + 'h' key: expand hovered nodes level deeper
// shift + 'r' key: reset current selection
// shift + 'f' key: fade unselected nodes
function enableNodeSelection() {
    let keySelectUnselect = 'S'
    let keyExpandSelection = 'E'
    let keyExpandHoveredNode = 'H'
    let keyResetCurrentSelection = 'R'
    let keyFadeUnselectedNodes = 'F'
    
    d3.select('body')
    .on("keydown", function(event) { 
        
        if (event.key == keySelectUnselect) {
            if (closeNode != null) {
                if (closeNode.id.toLowerCase() in selectedNodesMap) {
                    delete selectedNodesMap[closeNode.id.toLowerCase()]
                } else {
                    selectedNodesMap[closeNode.id.toLowerCase()] = true
                }
                simulationUpdate()
            }
        }
        
        if (event.key == keyExpandSelection) {
            if (selectedNodesMap.length != 0) {
                let newSelectedNodesMap = {...selectedNodesMap}
                currentGraph.links.forEach(function(d) {
                    if (d.source.id.toLowerCase() in selectedNodesMap || d.target.id.toLowerCase() in selectedNodesMap) {
                        newSelectedNodesMap[d.source.id.toLowerCase()] = true
                        newSelectedNodesMap[d.target.id.toLowerCase()] = true
                    }
                })
                selectedNodesMap = newSelectedNodesMap
                simulationUpdate()
            }
        }
        
        if (event.key == keyExpandHoveredNode) {
            if (closeNode != null) {
                selectedNodesMap[closeNode.id.toLowerCase()] = true
                let newSelectedNodesMap = {...selectedNodesMap}
                currentGraph.links.forEach(function(d) {
                    if (d.source.id == closeNode.id || d.target.id == closeNode.id) {
                        newSelectedNodesMap[d.source.id.toLowerCase()] = true
                        newSelectedNodesMap[d.target.id.toLowerCase()] = true
                    }
                })
                selectedNodesMap = newSelectedNodesMap
                simulationUpdate()
            }
        }
        
        if (event.key == keyResetCurrentSelection) {
            selectedNodesMap = {}
            simulationUpdate()
        }
        
        if (event.key == keyFadeUnselectedNodes) {
            fadeUnselectedNodes = !fadeUnselectedNodes
            if (fadeUnselectedNodes == true) {
                $("#li-unselected-opacity").removeClass('d-none');
                $("#unselected-opacity").removeClass('d-none');
                $('#fadeUnselectedNodesLabelText').html('<b>f fading unselected nodes</b>')
                
            } else {
                $("#li-unselected-opacity").addClass('d-none');
                $("#unselected-opacity").addClass('d-none');
                $('#fadeUnselectedNodesLabelText').html('<b>f</b> fade unselected nodes')
            }
            simulationUpdate()
        }
    });
}

function enableSearchInput() {
    $('#inputNodeSearchLabel').text('Search inactive')
    $('#inputNodeSearch').on('keyup change', function() {
        searchString = $(this).val().toLowerCase()
        
        searchTerms = searchString.split(" ")
        searchTerms = searchTerms.filter(Boolean);
        // console.log(searchTerms)
        
        searchResults = 0
        if (searchString.length > 0 && searchTerms.length > 0) {
            isSearching = true
            simulationUpdate()
            $('#inputNodeSearchLabel').text(searchResults + ' nodes found')
            
        } else {
            isSearching = false
            simulationUpdate()
            $('#inputNodeSearchLabel').text('Search inactive')
        }
    })
    
    $('#inputNodeSearchCancel').on('click', function() {
        cancelNodeSearch()
    })
}

function createStatistics() {
    // create statistics table
    statistics_html = ""
    for (let key in statistics) {
        if (statistics.hasOwnProperty(key)) {
            statistics_html += "<tr>"
            
            statistics_html += "<td>"
            statistics_html += key
            statistics_html += "</td>"
            
            statistics_html += "<td>"
            statistics_html += statistics[key]
            statistics_html += "</td>"
            
            statistics_html += "</tr>"
        }
    }
    d3.select("#tbody-statistics").html(statistics_html)
}

function createOverallMetricResults() {
    // create metrics table
    metrics_html = ""
    for (let key in overall_metric_results) {
        if (overall_metric_results.hasOwnProperty(key)) {
            metrics_html += "<tr>"
            
            metrics_html += "<td>"
            metrics_html += key
            metrics_html += "</td>"
            
            metrics_html += "<td>"
            
            let valueString = String(overall_metric_results[key])
            if (valueString.length > 30) {
                valueString = valueString.substring(0, 32) + '...';
            }
            
            metrics_html += String(valueString)
            metrics_html += "</td>"
            
            metrics_html += "</tr>"
        }
    }
    d3.select("#tbody-metrics").html(metrics_html)
}

function createMetricsMenuEntries() {
    // create apply metrics menu entries
    applyMetricHtml = ""

    console.log(currentMetricKeys)
    
    for (let key in currentMetricKeys) {

        if ( Object.keys(metricNameMap).includes(currentMetricKeys[key]) ) {
            
            applyMetricHtml += '<li> &nbsp; <input data-value="'
            applyMetricHtml += currentMetricKeys[key]
            applyMetricHtml += '" type="checkbox" onclick="animateRadiusWithMetric(\''
            applyMetricHtml += currentMetricKeys[key]
            applyMetricHtml += '\');"/>&nbsp; <span id="'
            applyMetricHtml += '" style="font-size:10px;">'
            
            let visibleMetricName = metricNameMap[currentMetricKeys[key]]
            
            applyMetricHtml += visibleMetricName
            applyMetricHtml += '</span> <small><span id="'
            applyMetricHtml += 'badge_' + currentMetricKeys[key]
            applyMetricHtml += '" data-bs-toggle="tooltip" data-bs-placement="bottom" title="" class="badge badge-primary badge-pill text-bg-primary"> ?</span> </small> &nbsp;</li>'
        }
    }
    
    d3.select("#dropdown-apply-metric").html(applyMetricHtml)
}

function getAnalysisName() {
    let analysisName = analysis_config['analysis_name']
    if (analysisName.length > 24) {
        analysisName = analysisName.slice(0, 24) + '...'
    }
    return analysisName
}

function addGraphTypeSelectionToMenu() {
    graphSelectHtml = ""
    for (let key in graphData) {
        graphSelectHtml += '<button class="dropdown-item btn-sm" style="font-size: 10px;" type="button" onclick="startWithGraph(\''
        graphSelectHtml += key
        graphSelectHtml += '\');">'
        graphSelectHtml += key.replace(/_/gi, " ")
        graphSelectHtml += "</button>"
    }
    
    d3.select("#dropdown-graph").html(graphSelectHtml)
    d3.select("#selectedGraph").text(currentGraphType.replace(/_/gi, " ").slice(0, 20) + '...')
}

function increaseCurrentChargeForce() {
    if (currentChargeForce < -50) {
        currentChargeForce += 50
        d3.select("#chargeForce").text(currentChargeForce)
        simulation.force("charge", d3.forceManyBody().strength(currentChargeForce))
        simulation.alpha(1).restart();
    }
}

function decreaseCurrentChargeForce() {
    currentChargeForce -= 50
    d3.select("#chargeForce").text(currentChargeForce)
    simulation.force("charge", d3.forceManyBody().strength(currentChargeForce))
    simulation.alpha(1).restart();
}

/**
* * MARK: - heatmap
*/

function normalHeatmapIsActive() { return heatmapActive }
function mergedHeatmapIsActive() { return heatmapMerged }
function churnHeatmapIsActive() { return heatmapChurn }
function hotspotHeatmapIsActive() { return heatmapHotspot }

function initHoverCouplingSwitch() {
    $("#switchHoverCoupling").on('change', function() {
        hoverCoupling = $(this).is(':checked');
        simulationUpdate();
    })
}

function initSemanticSearchSwitch() {
    $("#switchAddSemanticSearch").on('change', function() {
        addSemanticSearch = $(this).is(':checked');
        searchResults = 0
        simulationUpdate();
        $('#inputNodeSearchLabel').text(searchResults + ' nodes found')                
    })
}

function initContributorSearchSwitch() {
    $("#switchAddContributorSearch").on('change', function() {
        addContributorSearch = $(this).is(':checked');
        searchResults = 0
        simulationUpdate();
        $('#inputNodeSearchLabel').text(searchResults + ' nodes found')                
    })
}

function initAppConfig() {
    $('#configEmergeVersion').text('Emerge ' + analysis_config['emerge_version'])
}

function updateAppUI() {
    if (fadeUnselectedNodes == true) {
        $("#li-unselected-opacity").removeClass('d-none');
        $("#unselected-opacity").removeClass('d-none');
    } else {
        $("#li-unselected-opacity").addClass('d-none');
        $("#unselected-opacity").addClass('d-none');
    }
    
    // currently only show git functionality for file dependency graphs
    if (currentGraphType.includes('file_result_dependency_graph') && includeGitMetrics) {
        $("#formSwitchChurnHeatmap").removeClass('d-none');
        $("#formSwitchHotspotHeatmap").removeClass('d-none');
        $("#button_complexity_churn").removeClass('d-none');
        $("#button_change_coupling").removeClass('d-none');
        $("#container_git_settings").removeClass('d-none');
        $("#formSwitchHoverCoupling").removeClass('d-none');
        $("#formSwitchAddContributorSearch").removeClass('d-none')
    } else {
        $("#formSwitchChurnHeatmap").addClass('d-none');
        $("#formSwitchHotspotHeatmap").addClass('d-none');
        $("#button_complexity_churn").addClass('d-none');
        $("#button_change_coupling").addClass('d-none');
        $("#container_git_settings").addClass('d-none');
        $("#formSwitchHoverCoupling").addClass('d-none');
        $("#formSwitchAddContributorSearch").addClass('d-none');
    }
}

function initAppUI() {
    updateAppUI()
    if (includeGitMetrics) {
        initGitMetricsForDateRange()
        initDateRangeUI()
    }

    initModals()
}

/**
* * MARK: - Helper functions
*/

// borrowed from https://stackoverflow.com/questions/5767325/how-can-i-remove-a-specific-item-from-an-array
function removeItemAll(arr, value) {
    let i = 0;
    while (i < arr.length) {
        if (arr[i] === value) {
            arr.splice(i, 1);
        } else {
            ++i;
        }
    }
    return arr;
}

//https://stackoverflow.com/questions/21646738/convert-hex-to-rgba
function hexToRGB(hex, alpha) {
    let r = parseInt(hex.slice(1, 3), 16),
    g = parseInt(hex.slice(3, 5), 16),
    b = parseInt(hex.slice(5, 7), 16);
    
    if (alpha) {
        return "rgba(" + r + ", " + g + ", " + b + ", " + alpha + ")";
    } else {
        return "rgb(" + r + ", " + g + ", " + b + ")";
    }
}