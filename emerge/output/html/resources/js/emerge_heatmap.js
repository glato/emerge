function initHeatmapSwitches() {
    // normal heatmap
    $("#switchActivateHeatmap").on('change', function() {
        if ($(this).is(':checked')) {
            heatmapActive = true
            if ($("#switchMergeHeatmap").is(':checked')) {
                $("#switchMergeHeatmap").prop('checked', false);
                heatmapMerged = false
            }
            
            if ($("#switchChurnHeatmap").is(':checked')) {
                $("#switchChurnHeatmap").prop('checked', false);
                heatmapChurn = false
            }
            
            if ($("#switchHotspotHeatmap").is(':checked')) {
                $("#switchHotspotHeatmap").prop('checked', false);
                heatmapHotspot = false
            }
        } else {
            heatmapActive = false
        }
        
        simulationUpdate();
    });
    
    // hybrid/merged heatmap
    $("#switchMergeHeatmap").on('change', function() {
        if ($(this).is(':checked')) {
            heatmapMerged = true
            if ($("#switchActivateHeatmap").is(':checked')) {
                $("#switchActivateHeatmap").prop('checked', false);
                heatmapActive = false
            }
            
            if ($("#switchChurnHeatmap").is(':checked')) {
                $("#switchChurnHeatmap").prop('checked', false);
                heatmapChurn = false
            }
            
            if ($("#switchHotspotHeatmap").is(':checked')) {
                $("#switchHotspotHeatmap").prop('checked', false);
                heatmapHotspot = false
            }
        } else {
            heatmapMerged = false
        }
        
        simulationUpdate();
    });
    
    // churn heatmap
    $("#switchChurnHeatmap").on('change', function() {
        if ($(this).is(':checked')) {
            heatmapChurn = true
            if ($("#switchActivateHeatmap").is(':checked')) {
                $("#switchActivateHeatmap").prop('checked', false);
                heatmapActive = false
            }
            
            if ($("#switchMergeHeatmap").is(':checked')) {
                $("#switchMergeHeatmap").prop('checked', false);
                heatmapMerged = false
            }
            
            if ($("#switchHotspotHeatmap").is(':checked')) {
                $("#switchHotspotHeatmap").prop('checked', false);
                heatmapHotspot = false
            }
        } else {
            heatmapChurn = false
        }
        
        simulationUpdate();
    });
    
    // hotspot heatmap
    $("#switchHotspotHeatmap").on('change', function() {
        if ($(this).is(':checked')) {
            heatmapHotspot = true
            if ($("#switchActivateHeatmap").is(':checked')) {
                $("#switchActivateHeatmap").prop('checked', false);
                heatmapActive = false
            }
            
            if ($("#switchMergeHeatmap").is(':checked')) {
                $("#switchMergeHeatmap").prop('checked', false);
                heatmapMerged = false
            }
            
            if ($("#switchChurnHeatmap").is(':checked')) {
                $("#switchChurnHeatmap").prop('checked', false);
                heatmapChurn = false
            }
        } else {
            heatmapHotspot = false
        }
        
        simulationUpdate();
    });
    
}

/**
* * MARK: - Drawing a heatmap for normal / hybrid (merged) mode
*/

function calculateHeatmapScore(node) {
    
    let totalScore = 0
    
    if (normalHeatmapIsActive() || mergedHeatmapIsActive() ) {
        
        let score = analysis_config['heatmap']['score']['base']
        let slocScore = 0
        let fanoutScore = 0
        
        if (analysis_config['heatmap']['metrics']['active']['sloc'] == true) {
            // add weighted sloc metric if present
            if ('metric_sloc_in_entity' in node) {
                slocScore = node.metric_sloc_in_entity * analysis_config['heatmap']['metrics']['weights']['sloc']
            }
            if ('metric_sloc_in_file' in node) {
                slocScore = node.metric_sloc_in_file * analysis_config['heatmap']['metrics']['weights']['sloc']
            }
        }
        
        if (analysis_config['heatmap']['metrics']['active']['fan_out'] == true) {
            // add weighted fan-out metric is present
            if ('metric_fan_out_dependency_graph' in node) {
                fanoutScore = node.metric_fan_out_dependency_graph * analysis_config['heatmap']['metrics']['weights']['fan_out']
            }
            if ('metric_fan_out_inheritance_graph' in node) {
                fanoutScore = node.metric_fan_out_inheritance_graph * analysis_config['heatmap']['metrics']['weights']['fan_out']
            }
            if ('metric_fan_out_complete_graph' in node) {
                fanoutScore = node.metric_fan_out_complete_graph * analysis_config['heatmap']['metrics']['weights']['fan_out']
            }
        }
        
        // limit the total score to the heatmap limit parameter, since the rendering seems to be buggy if this is exceeded
        totalScore = score + slocScore + fanoutScore
        if (totalScore > analysis_config['heatmap']['score']['limit']) {
            totalScore = analysis_config['heatmap']['score']['limit']
        }
        
    } else if (churnHeatmapIsActive()) {
        let score = analysis_config['churn_heatmap']['score']['base']
        let churnScore = 0
        
        if (node.hasOwnProperty('metric_git_code_churn')) {
            if (analysis_config['churn_heatmap']['metrics']['active']['churn'] == true) {
                churnScore = node.metric_git_code_churn * analysis_config['churn_heatmap']['metrics']['weights']['churn']
            }
            
            totalScore = score + churnScore
            if (totalScore > analysis_config['churn_heatmap']['score']['limit']) {
                totalScore = analysis_config['churn_heatmap']['score']['limit']
            }      
        }
        
    } else if (hotspotHeatmapIsActive()) {
        // approach: let's define a hotspot as a product of the following factors
        // 1. code churn over a given time period
        // 2. whitespace complexity over a given time period
        // 3. SLOC over a given time period
        // 4. connectivity based on dependencies inside the network (i.e. fan-in / fan-out)
        
        let score = analysis_config['hotspot_heatmap']['score']['base']
        let churnScore = 0
        let ws_complexity_score = 0
        let connectivity_score = 0
        let sloc_score = 0
        
        if (node.hasOwnProperty('metric_git_code_churn') && node.hasOwnProperty('metric_git_ws_complexity') ) {
            if (analysis_config['hotspot_heatmap']['metrics']['active']['churn'] == true && analysis_config['hotspot_heatmap']['metrics']['active']['ws_complexity'] == true) {
                
                churnScore = node.metric_git_code_churn * analysis_config['hotspot_heatmap']['metrics']['weights']['churn'] * 2.0
                ws_complexity_score = node.metric_git_code_churn * analysis_config['hotspot_heatmap']['metrics']['weights']['ws_complexity'] * 0.75
                
                if ('metric_fan_out_dependency_graph' in node) {
                    connectivity_score = node.metric_fan_out_dependency_graph * 1.5
                }

                totalScore = (churnScore + ws_complexity_score + connectivity_score )
                if (totalScore > analysis_config['hotspot_heatmap']['score']['limit'] * 1.25  ) {
                    totalScore = analysis_config['hotspot_heatmap']['score']['limit'] * 1.25
                }
            }
        }
        
    }
    
    return totalScore
}

function drawHeatMap(context) {
    
    if (normalHeatmapIsActive() || mergedHeatmapIsActive()) {
        heat.max(analysis_config['heatmap']['score']['limit']);
    }
    
    if (churnHeatmapIsActive()) {
        heat.max(analysis_config['churn_heatmap']['score']['limit']);
    }
    
    if (hotspotHeatmapIsActive()) {
        heat.max(analysis_config['hotspot_heatmap']['score']['limit']);
    }
    
    heat.clear();
    currentGraph.nodes.forEach(function(node, i) {
        heat.add([node.x, node.y, calculateHeatmapScore(node)])
    })
    
    heat.draw()
    
    // reset alpha from heatmap rendering
    context.globalAlpha = 1;  
}