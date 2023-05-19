/**
* * MARK: - Metric info badge tooltip descriptions
*/
const description_metric_sloc_in_file = '"Source lines of code (SLOC), also known as lines of code (LOC), is a software metric used to measure the size of a computer program by counting the number of lines in the text of the programs source code. SLOC is typically used to predict the amount of effort that will be required to develop a program, as well as to estimate programming productivity or maintainability once the software is produced." (Wikipedia)'
const description_metric_number_of_methods = 'A metric representing the total number of methods found per file or entity. This is similar to a weighted methods per class (WMC) metric with a uniform complexity/weight of 1.'
const description_metric_fan_in = '"Fan-in coupling (afferent coupling) the number of entities that depend on a given entity. It estimates in what extent the "external world" depends on the changes in a given entity" (gcc.gnu.org). This metric represents the number of dependencies FROM other files or entities.'
const description_metric_fan_out = '"Fan-out coupling (efferent coupling) the number of entities the given entity depends upon. It estimates in what extent the given entity depends on the changes in "external world" (gcc.gnu.org). This metric represents the number of dependencies TO other files or entities.'
const description_metric_louvain_modularity = '"The Louvain method for community detection is a method to extract communities from large networks" (Wikipedia). This metric seperates detected communities by a unique number/ node size.'

const description_metric_ws_complexity_in_file = 'A complexity metric that counts the whitespaces (e.g. space or tab) as an approximation of the complexity of code through indentation.'
const description_metric_git_ws_complexity = 'A complexity metric that counts the whitespaces (e.g. space or tab) as an approximation of the complexity of code through indentation - over a selected time period.'
const description_metric_git_code_churn = 'A git metric counts the sum of lines added + lines removed to a file.'
const description_metric_git_sloc = 'Source lines of code (SLOC) - over a given period of time.'
const description_metric_git_number_of_authors = 'A git metric that counts the sum of authors/contributors to a file - over a given period of time'

const description_heat_map_normal = '"A heat map (or <strong>heatmap</strong>) is a data visualization technique that shows magnitude of a phenomenon as color in two dimensions" (Wikipedia). The heatmap score is based on a weighted score from the fan-out and SLOC metric. Red color indicates a warning (hotspot), that given metric scores may be to high, while decreasing into blue color.'
const description_heat_map_hybrid = 'This is a visual (hybrid) <strong>combination</strong> of the normal graph visualization and a heatmap layer behind it'
const description_unselected_opacity = 'Set the opacity for all unselected nodes after selecting a few with <br><br><strong>shift + s</strong><br><br> and fading all others with <br><br><strong>shift + f</strong>'
const description_hover_coupling = 'Enable this to additionally highligh nodes that have a <strong>change coupling</strong> to the hoved node.'
const description_semantic_search = 'Enrich the search results by including semantic keywords (computed by <strong>tf-idf</strong>) which try to describe the content of a node more exactly'
const description_cluster_hulls = 'Hover over a cluster node color to get a highlighted preview of the concave hull of the appropriate cluster and display basic cluster statistics via tooltip. In addition to that you can also mark/select multiple cluster hulls that will then render permanently.'
const description_contributor_search = 'Enrich the search results by including substrings of <strong>contributor email addresses</strong> for each commit in the selected range.'

const description_heat_map_churn = 'This heatmap visualizes the <strong>code churn</strong> in files over the set period of time.'
const description_heat_map_hotspot = 'The hotspot heatmap tries to identify problematic files (that could be hard to maintain/error prone) as a product of <strong>code churn</strong>, <strong>complexity</strong> and <strong>fan-out</strong>.'


const wide_tooltip_template =
`
'<div class="tooltip wide-tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>'
`

const description_shortcuts_tooltip =
`
<b>shift + s</b> 👉 (de)select hovered nodes
<br>

<b>shift + r</b> 👉 resets selected nodes
<br>

<b>shift + e</b> 👉 selects all nodes linked to selected nodes
<br>

<b>shift + h</b> 👉 selects all nodes linked to hovered node
<br>

<b>shift + f</b> 👉 fade unselected nodes</span>
`
let description_project_info = ""
let description_graph_info = ""

function showDebugToast(message) {
    const toastDebug = document.getElementById('toastDebug')
    const toast = new bootstrap.Toast(toastDebug)
    const div = document.querySelector("#toastDebugMessage");
    div.innerHTML = message;
    toast.show()
}

function addToolTipsToMetricEntries() {
    $('#badge_metric_sloc_in_file').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_sloc_in_file').attr('data-bs-title', description_metric_sloc_in_file)
    $('#badge_metric_sloc_in_file').attr('data-bs-html', 'true')
    $('#badge_metric_sloc_in_file').attr('data-bs-placement', 'bottom')
    
    $('#badge_metric_sloc_in_entity').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_sloc_in_entity').attr('data-bs-title', description_metric_sloc_in_file)
    $('#badge_metric_sloc_in_entity').attr('data-bs-html', 'true')
    $('#badge_metric_sloc_in_entity').attr('data-bs-placement', 'bottom')
    
    $('#badge_metric_number_of_methods_in_file').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_number_of_methods_in_file').attr('data-bs-title', description_metric_number_of_methods)
    $('#badge_metric_number_of_methods_in_file').attr('data-bs-html', 'true')
    $('#badge_metric_number_of_methods_in_file').attr('data-bs-placement', 'bottom')
    
    $('#badge_metric_number_of_methods_in_entity').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_number_of_methods_in_entity').attr('data-bs-title', description_metric_number_of_methods)
    $('#badge_metric_number_of_methods_in_entity').attr('data-bs-html', 'true')
    $('#badge_metric_number_of_methods_in_entity').attr('data-bs-placement', 'bottom')
    
    $('#badge_metric_ws_complexity_in_file').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_ws_complexity_in_file').attr('data-bs-title', description_metric_ws_complexity_in_file)
    $('#badge_metric_ws_complexity_in_file').attr('data-bs-html', 'true')
    $('#badge_metric_ws_complexity_in_file').attr('data-bs-placement', 'bottom')

    $('#badge_metric_git_code_churn').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_git_code_churn').attr('data-bs-title', description_metric_git_code_churn)
    $('#badge_metric_git_code_churn').attr('data-bs-html', 'true')
    $('#badge_metric_git_code_churn').attr('data-bs-placement', 'bottom')

    $('#badge_metric_git_ws_complexity').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_git_ws_complexity').attr('data-bs-title', description_metric_git_ws_complexity)
    $('#badge_metric_git_ws_complexity').attr('data-bs-html', 'true')
    $('#badge_metric_git_ws_complexity').attr('data-bs-placement', 'bottom')

    $('#badge_metric_git_sloc').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_git_sloc').attr('data-bs-title', description_metric_git_sloc)
    $('#badge_metric_git_sloc').attr('data-bs-html', 'true')
    $('#badge_metric_git_sloc').attr('data-bs-placement', 'bottom')

    $('#badge_metric_git_number_authors').attr('data-bs-toggle', 'tooltip')
    $('#badge_metric_git_number_authors').attr('data-bs-title', description_metric_git_number_of_authors)
    $('#badge_metric_git_number_authors').attr('data-bs-html', 'true')
    $('#badge_metric_git_number_authors').attr('data-bs-placement', 'bottom')

    // TODO
    $('#badge_metric_fan_in_dependency_graph').attr('title', description_metric_fan_in)
    // $('#badge_metric_fan_in_dependency_graph').tooltip();
    $('#badge_metric_fan_in_complete_graph').attr('title', description_metric_fan_in)
    // $('#badge_metric_fan_in_complete_graph').tooltip();
    $('#badge_metric_fan_in_inheritance_graph').attr('title', description_metric_fan_in)
    // $('#badge_metric_fan_in_inheritance_graph').tooltip();
    
    $('#badge_metric_fan_out_dependency_graph').attr('title', description_metric_fan_out)
    // $('#badge_metric_fan_out_dependency_graph').tooltip();
    $('#badge_metric_fan_out_complete_graph').attr('title', description_metric_fan_out)
    // $('#badge_metric_fan_out_complete_graph').tooltip();
    $('#badge_metric_fan_out_inheritance_graph').attr('title', description_metric_fan_out)
    // $('#badge_metric_fan_out_inheritance_graph').tooltip();
    
    $('#badge_metric_file_result_dependency_graph_louvain_modularity_file').attr('title', description_metric_louvain_modularity)
    // $('#badge_metric_file_result_dependency_graph_louvain_modularity_file').tooltip();
    
    $('#badge_metric_entity_result_dependency_graph_louvain_modularity_in_entity').attr('title', description_metric_louvain_modularity)
    // $('#badge_metric_entity_result_dependency_graph_louvain_modularity_in_entity').tooltip();
    
    $('#badge_metric_entity_result_inheritance_graph_louvain_modularity_in_entity').attr('title', description_metric_louvain_modularity)
    // $('#badge_metric_entity_result_inheritance_graph_louvain_modularity_in_entity').tooltip();
    
    $('#badge_metric_entity_result_complete_graph_louvain_modularity_in_entity').attr('title', description_metric_louvain_modularity)
    // $('#badge_metric_entity_result_complete_graph_louvain_modularity_in_entity').tooltip();
    
    $('#badge_metric_entity_result_complete_graph_louvain_modularity_in_entity').attr('title', description_metric_louvain_modularity)
    // $('#badge_metric_entity_result_complete_graph_louvain_modularity_in_entity').tooltip();
    
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}

function addTooltipToHoverCoupling() {
    const badgeHoverCouplingTooltip = new bootstrap.Tooltip(document.getElementById('badge_hover_coupling'), {});
    badgeHoverCouplingTooltip._config.title = description_hover_coupling
}

function addTooltipToContributorSearch() {
    const badgeContributorsSearchTooltip = new bootstrap.Tooltip(document.getElementById('badge_contributors_search'), {});
    badgeContributorsSearchTooltip._config.title = description_contributor_search
}

function addToolTipsToHeatMap() {
    const badgeHeatmapNormalTooltip = new bootstrap.Tooltip(document.getElementById('badge_heat_map_normal'), {});
    badgeHeatmapNormalTooltip._config.title = description_heat_map_normal
    
    const badgeHeatmapHybridTooltip = new bootstrap.Tooltip(document.getElementById('badge_heat_map_hybrid'), {});
    badgeHeatmapHybridTooltip._config.title = description_heat_map_hybrid

    const badgeHeatmapChurnTooltip = new bootstrap.Tooltip(document.getElementById('badge_heat_map_churn'), {});
    badgeHeatmapChurnTooltip._config.title = description_heat_map_churn
    
    const badgeHeatmapHotspotTooltip = new bootstrap.Tooltip(document.getElementById('badge_heat_map_hotspot'), {});
    badgeHeatmapHotspotTooltip._config.title = description_heat_map_hotspot
}

function addToolTipToShortcuts() {
    const badgeShortcutsTooltip = new bootstrap.Tooltip(document.getElementById('badge_shortcuts'), {});
    badgeShortcutsTooltip._config.template = wide_tooltip_template
    badgeShortcutsTooltip._config.title = description_shortcuts_tooltip
}

function addTooltipUnselectedOpacity() {
    const badgeUnselectedOpacityTooltip = new bootstrap.Tooltip(document.getElementById('badge_unselected_opacity'), {});
    badgeUnselectedOpacityTooltip._config.title = description_unselected_opacity
}

function addTooltipSemanticSearch() {
    const badgeSemanticSearchTooltip = new bootstrap.Tooltip(document.getElementById('badge_semantic_search'), {});
    badgeSemanticSearchTooltip._config.title = description_semantic_search
}

function addTooltipClusterHulls() {
    const badgeBadgeClusterHullsTooltip = new bootstrap.Tooltip(document.getElementById('badge_cluster_hulls'), {});
    badgeBadgeClusterHullsTooltip._config.title = description_cluster_hulls
}

function addTooltipProjectInfo() {
    let configProjectName = analysis_config['project_name']
    let analysisName = getAnalysisName()
    let configAnalysisDateTime = analysis_config['analysis_date']
    
    description_project_info = "<strong>Project:</strong> " + configProjectName + "<br>" + "<strong>Analysis:</strong> " + analysisName + "<br>" + "<strong>Date:</strong> " + configAnalysisDateTime          
    const badgeProjectInfoTooltip = new bootstrap.Tooltip(document.getElementById('badge_project_info'), {});
    badgeProjectInfoTooltip._config.title = description_project_info
}

function addTooltipGraphInfo() {
    description_graph_info = "<strong>Graph nodes:</strong> " + currentGraph.nodes.length + "<br>" + "<strong>Graph edges:</strong> " + currentGraph.links.length + "<br>" + "<strong>Charge force:</strong> " + currentChargeForce
    const badgeGraphInfoTooltip = new bootstrap.Tooltip(document.getElementById('badge_graph_info'), {});
    badgeGraphInfoTooltip._config.title = description_graph_info
}
