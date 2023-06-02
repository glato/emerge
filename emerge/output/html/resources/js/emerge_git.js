let changeCouplingMapForDateRange = {}

function clickDateRangePickerCancel() {
    console.log("reset date range picker")
    if (includeGitMetrics) {
        initDateRangeUI()
        dateRangePickerFrom = commit_first_date
        dateRangePickerTo = commit_last_date
        initGitMetricsForDateRange()
        showToastDateRangeUpdate()
    }
}

function initGitMetricsForDateRange() {
    gitMetricsIndexFrom = commit_dates.indexOf( dateRangePickerFrom );
    gitMetricsIndexTo = commit_dates.lastIndexOf( dateRangePickerTo );
    // console.log("found first index: " + gitMetricsIndexFrom + " for `from` " + dateRangePickerFrom)
    // console.log("found last index: " + gitMetricsIndexTo + " for `to` " + dateRangePickerTo)
    changeCouplingMapForDateRange = calculateCouplingForDateRange()
    // console.log(changeCouplingMapForDateRange)
    // console.log(changeCouplingMapForDateRange)
    addGitMetricToFileNodes()
}

function nodeNamesHaveChangeCoupling(sourceName, targetName) {
    for (const [key, value] of Object.entries(changeCouplingMapForDateRange)) {
        if (sourceName.includes( key ) ) {
            for (const k of changeCouplingMapForDateRange[key]) {
                if (targetName.includes(k)) {
                    return true
                }
            }
        }
    }

    return false
}

function calculateCouplingForDateRange() {
    let totalChangeCouplingDict = {}
    
    for (let i = gitMetricsIndexFrom; i < gitMetricsIndexTo; i++) {
        let couplingLinks = commit_metrics[i].links
        
        if (couplingLinks.length > 0) {
            for (nextChangeCouplingDict of couplingLinks) {
                
                // source -> target
                if ( !(nextChangeCouplingDict.source in totalChangeCouplingDict) ) {
                    totalChangeCouplingDict[nextChangeCouplingDict.source] = new Set();
                    totalChangeCouplingDict[nextChangeCouplingDict.source].add(nextChangeCouplingDict.target)
                } else {
                    totalChangeCouplingDict[nextChangeCouplingDict.source].add(nextChangeCouplingDict.target)
                }
                
                // target -> source
                if ( !(nextChangeCouplingDict.target in totalChangeCouplingDict) ) {
                    totalChangeCouplingDict[nextChangeCouplingDict.target] = new Set();
                    totalChangeCouplingDict[nextChangeCouplingDict.target].add(nextChangeCouplingDict.source)
                } else {
                    totalChangeCouplingDict[nextChangeCouplingDict.target].add(nextChangeCouplingDict.source)
                } 
            }
        }
    }
    return totalChangeCouplingDict
}

function calculateFileChurnForDateRange() {
    let totalFileChurnDict = {}
    
    for (let i = gitMetricsIndexFrom; i < gitMetricsIndexTo; i++) {
        let nextChurnDict = commit_metrics[i].churn
        totalFileChurnDict = mergeDicts(totalFileChurnDict, nextChurnDict)
    }
    
    return totalFileChurnDict
}

function calculateSlocForDateRange() {
    let totalSlocDict = {}
    
    for (let i = gitMetricsIndexFrom; i < gitMetricsIndexTo; i++) {
        let nextSlocDict = commit_metrics[i].sloc
        totalSlocDict = mergeDictsToMostCurrentValues(totalSlocDict, nextSlocDict)
    }
    
    return totalSlocDict
}

function calculateWhiteSpaceComplexityForDateRange() {
    let totalWhiteSpaceComplexityDict = {}
    
    for (let i = gitMetricsIndexFrom; i < gitMetricsIndexTo; i++) {
        let nextWhiteSpaceComplexityDict = commit_metrics[i].ws_complexity
        totalWhiteSpaceComplexityDict = mergeDictsToMostCurrentValues(totalWhiteSpaceComplexityDict, nextWhiteSpaceComplexityDict)
    }
    
    return totalWhiteSpaceComplexityDict
}

function calculateAuthorsForDateRange() {
    let totalFileAuthorsDict = {}
    
    for (let i = gitMetricsIndexFrom; i < gitMetricsIndexTo; i++) {
        let nextFileAuthorsDict = commit_metrics[i].files_author_map
        totalFileAuthorsDict = mergeDicts(totalFileAuthorsDict, nextFileAuthorsDict)
    }
    return totalFileAuthorsDict
}

function addGitMetricToFileNodes() {
    if (currentGraphType.includes('file_result_dependency_graph')) {
        let fileChurnMap = calculateFileChurnForDateRange()
        let whiteSpaceComplexityMap = calculateWhiteSpaceComplexityForDateRange()
        let slocMap = calculateSlocForDateRange()
        let authorsMap = calculateAuthorsForDateRange()

        // console.log(authorsMap)
        // console.log(whiteSpaceComplexityMap)
        // console.log("fileResultPrefix: " + fileResultPrefix)
        
        currentGraph.nodes.forEach(function(node, i) {
            
            // housekeeping git code churn
            delete node['metric_git_code_churn']
            if (node.hasOwnProperty('metrics')) {
                delete node.metrics['metric_git_code_churn']
            }
            
            // housekeeping git ws complexity
            delete node['metric_git_ws_complexity']
            if (node.hasOwnProperty('metrics')) {
                delete node.metrics['metric_git_ws_complexity']
            }
            
            // housekeeping git number of file authors
            delete node['metric_git_number_authors']
            if (node.hasOwnProperty('metrics')) {
                delete node.metrics['metric_git_number_authors']
            }
            delete node['metric_git_main_contrib']
            if (node.hasOwnProperty('metrics')) {
                delete node.metrics['metric_git_main_contrib']
            }
            
            // housekeeping file contributors
            delete node['metric_git_contributors']
            if (node.hasOwnProperty('metrics')) {
                delete node.metrics['metric_git_contributors']
            }
            
            // housekeeping git sloc
            delete node['metric_git_sloc']
            if (node.hasOwnProperty('metrics')) {
                delete node.metrics['metric_git_sloc']
            }
            
            if (!node.hasOwnProperty('metrics')) {
                node.metrics = {}
            }
            
            let nodeFileName = node.id.split("/").pop();

            let nodeSearchPath = ""
            if (fileResultPrefix === "") { 
                nodeSearchPath = node.id
            } else {
                nodeSearchPath = fileResultPrefix + "/" + node.id
            }
            
            // add git code churn
            for (const [key, value] of Object.entries(fileChurnMap)) {
                if (nodeSearchPath.includes(key)) {
                    node['metric_git_code_churn'] = value
                    node.metrics['metric_git_code_churn'] = value
                }
            }
            
            // add git whitespace complexity
            for (const [key, value] of Object.entries(whiteSpaceComplexityMap)) {
                if (nodeSearchPath.includes(key)) {
                    node['metric_git_ws_complexity'] = value
                    node.metrics['metric_git_ws_complexity'] = value
                }
            }
            
            // add git sloc
            for (const [key, value] of Object.entries(slocMap)) {
                if (nodeSearchPath.includes(key)) {
                    node['metric_git_sloc'] = value
                    node.metrics['metric_git_sloc'] = value
                }
            }
            
            // add git number authors
            for (const [key, value] of Object.entries(authorsMap)) {
                if (nodeSearchPath.includes(key)) {
                    node['metric_git_contributors'] = value
                    node.metrics['metric_git_contributors'] = value
                }
            }
            
            // add all git contributors to file
            for (const [key, value] of Object.entries(authorsMap)) {
                if (nodeSearchPath.includes(key)) {
                    node['metric_git_contributors'] = Object.keys(value)
                    node.metrics['metric_git_contributors'] = Object.keys(value)
                    node['metric_git_number_authors'] = Object.keys(value).length
                    node.metrics['metric_git_number_authors'] = Object.keys(value).length
                }
            }
            
        });
    }
}

function mainContributor(obj={}, asc=true) { 
    let biggestChurn = 0
    let authorBiggestChurn = ''
    
    for (let key in obj) {
        if (obj[key] > biggestChurn) {
            biggestChurn = obj[key]
            authorBiggestChurn = key
        }
    }
    
    return authorBiggestChurn
}

// daterangepicker for git date range
function initDateRangeUI() {
    $('input[name="daterange"]').daterangepicker({
        "startDate": commit_first_date,
        "endDate": commit_last_date,
        "minDate": commit_first_date,
        "maxDate": commit_last_date,
        
        // ranges: {
        //     'Last 3 days': [moment().subtract(2, 'days'), moment()],
        //     'Last 10 days': [moment().subtract(9, 'days'), moment()],
        //     'Last 30 days': [moment().subtract(29, 'days'), moment()],
        //     'Last 60 days': [moment().subtract(59, 'days'), moment()],
        //     'This month': [moment().startOf('month'), moment().endOf('month')],
        //     'Last month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        // },
        
        isInvalidDate: function(date) {
            if ( commit_dates.includes(date.format('DD/MM/YYYY')) ) {
                return false
            } else {
                return true
            }
        },
        
        "locale": {
            "format": "DD/MM/YYYY",
            "separator": " - ",
            "applyLabel": "Apply",
            "cancelLabel": "Cancel",
            "fromLabel": "From",
            "toLabel": "To",
            "customRangeLabel": "Custom",
            "weekLabel": "W",
            "daysOfWeek": [
                "Su",
                "Mo",
                "Tu",
                "We",
                "Th",
                "Fr",
                "Sa"
            ],
            "monthNames": [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December"
            ],
            "firstDay": 1
        },
        
        opens: 'left'
    }, function(start, end, label) {
        console.log("A new date selection was made: " + start.format('DD/MM/YYYY') + ' to ' + end.format('DD/MM/YYYY'));
        dateRangePickerFrom = start.format('DD/MM/YYYY')
        dateRangePickerTo = end.format('DD/MM/YYYY')
        
        // console.log(dateRangePickerFrom)
        // console.log(dateRangePickerTo)
        
        initGitMetricsForDateRange()
        showToastDateRangeUpdate()
    })
}

function showToastDateRangeUpdate() {
    const toastLiveExample = document.getElementById('toastDateRangeUpdated')
    const toast = new bootstrap.Toast(toastLiveExample)    
    toast.show()
}

// Copyright 2021 Observable, Inc.
// Released under the ISC license.
// https://observablehq.com/@d3/multi-line-chart
function LineChart(data, {
    x = ([x]) => x, // given d in data, returns the (temporal) x-value
    y = ([, y]) => y, // given d in data, returns the (quantitative) y-value
    z = () => 1, // given d in data, returns the (categorical) z-value
    title, // given d in data, returns the title text
    defined, // for gaps in data
    curve = d3.curveLinear, // method of interpolation between points
    marginTop = 20, // top margin, in pixels
    marginRight = 30, // right margin, in pixels
    marginBottom = 30, // bottom margin, in pixels
    marginLeft = 40, // left margin, in pixels
    width = 640, // outer width, in pixels
    height = 400, // outer height, in pixels
    xType = d3.scaleUtc, // type of x-scale
    xDomain, // [xmin, xmax]
    xRange = [marginLeft, width - marginRight], // [left, right]
    yType = d3.scaleLinear, // type of y-scale
    yDomain, // [ymin, ymax]
    yRange = [height - marginBottom, marginTop], // [bottom, top]
    yFormat, // a format specifier string for the y-axis
    yLabel, // a label for the y-axis
    zDomain, // array of z-values
    color = "currentColor", // stroke color of line, as a constant or a function of *z*
    strokeLinecap, // stroke line cap of line
    strokeLinejoin, // stroke line join of line
    strokeWidth = 1.0, // stroke width of line
    strokeOpacity, // stroke opacity of line
    mixBlendMode = "multiply", // blend mode of lines
    voronoi, // show a Voronoi overlay? (for debugging)
    id
} = {}) {
    // Compute values.
    
    let textColor = "#FFF"
    if (!darkMode) { textColor = "#333333"}
    
    const X = d3.map(data, x);
    const Y = d3.map(data, y);
    const Z = d3.map(data, z);
    const O = d3.map(data, d => d);
    if (defined === undefined) defined = (d, i) => !isNaN(X[i]) && !isNaN(Y[i])  ;
    const D = d3.map(data, defined);
    
    // Compute default domains, and unique the z-domain.
    if (xDomain === undefined) xDomain = d3.extent(X);
    if (yDomain === undefined) yDomain = [0, d3.max(Y, d => typeof d === "string" ? +d : d)];
    if (zDomain === undefined) zDomain = Z;
    zDomain = new d3.InternSet(zDomain);
    
    // Omit any data not present in the z-domain.
    const I = d3.range(X.length).filter(i => zDomain.has(Z[i]));
    
    // Construct scales and axes.
    const xScale = xType(xDomain, xRange);
    const yScale = yType(yDomain, yRange);
    const xAxis = d3.axisBottom(xScale).ticks(width / 80).tickSizeOuter(0);
    const yAxis = d3.axisLeft(yScale).ticks(height / 60, yFormat);
    
    // Compute titles.
    const T = title === undefined ? Z : title === null ? null : d3.map(data, title);
    
    // Construct a line generator.
    const line = d3.line()
    .defined(i => D[i])
    .curve(curve)
    .x(i => xScale(X[i]))
    .y(i => yScale(Y[i]));
    
    const svg = d3.create("svg")
    .attr("id", id)
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [0, 0, width, height])
    .attr("style", "max-width: 100%; height: auto; height: intrinsic;")
    .style("-webkit-tap-highlight-color", "transparent")
    .on("pointerenter", pointerentered)
    .on("pointermove", pointermoved)
    .on("pointerleave", pointerleft)
    .on("touchstart", event => event.preventDefault());
    
    // An optional Voronoi display (for fun).
    if (voronoi) svg.append("path")
    .attr("fill", "none")
    .attr("stroke", "#ccc")
    .attr("d", d3.Delaunay
    .from(I, i => xScale(X[i]), i => yScale(Y[i]))
    .voronoi([0, 0, width, height])
    .render());
    
    svg.append("g")
    .attr("transform", `translate(0,${height - marginBottom})`)
    .call(xAxis);
    
    svg.append("g")
    .attr("transform", `translate(${marginLeft},0)`)
    .call(yAxis)
    .call(g => g.select(".domain").remove())
    .call(voronoi ? () => {} : g => g.selectAll(".tick line").clone()
    .attr("x2", width - marginLeft - marginRight)
    .attr("stroke-opacity", 0.1))
    .call(g => g.append("text")
    .attr("x", -marginLeft)
    .attr("y", 10)
    .attr("fill", "currentColor")
    .attr("text-anchor", "start")
    .text(yLabel));
    
    const path = svg.append("g")
    .attr("fill", "none")
    .attr("stroke", typeof color === "string" ? color : null)
    .attr("stroke-linecap", strokeLinecap)
    .attr("stroke-linejoin", strokeLinejoin)
    .attr("stroke-width", strokeWidth)
    .attr("stroke-opacity", strokeOpacity)
    .selectAll("path")
    .data(d3.group(I, i => Z[i]))
    .join("path")
    //.style("mix-blend-mode", mixBlendMode)
    .attr("stroke", typeof color === "function" ? ([z]) => color(z) : null)
    .attr("d", ([, I]) => line(I));
    
    const dot = svg.append("g")
    .attr("display", "none")
    .attr("fill", "red");
    
    dot.append("circle")
    .attr("r", 2.5);
    
    dot.append("text")
    .attr("font-family", "sans-serif")
    .attr("font-size", 10)
    .attr("text-anchor", "middle")
    .attr("fill", textColor) 
    .attr("y", -8);
    
    function pointermoved(event) {
        let strokeColor = "#323232"
        if (!darkMode) { strokeColor = "#828282"}
        
        const [xm, ym] = d3.pointer(event);
        const i = d3.least(I, i => Math.hypot(xScale(X[i]) - xm, yScale(Y[i]) - ym)); // closest point
        path.style("stroke", ([z]) => Z[i] === z ? null : strokeColor).filter(([z]) => Z[i] === z).raise();
        dot.attr("transform", `translate(${xScale(X[i])},${yScale(Y[i])})`);
        if (T) dot.select("text").text(T[i]);
        svg.property("value", O[i]).dispatch("input", {bubbles: true});
    }
    
    function pointerentered() {
        path.style("mix-blend-mode", null).style("stroke", "lightyellow");
        dot.attr("display", null);
    }
    
    function pointerleft() {
        //path.style("mix-blend-mode", mixBlendMode).style("stroke", null);
        path.style("stroke", "lightsteelblue")
        dot.attr("display", "none");
        svg.node().value = null;
        svg.dispatch("input", {bubbles: true});
    }
    
    return Object.assign(svg.node(), {value: null});
}

function generateTimeSeriesChart() {
    
    let timeSeriesComplexityTotal = {}
    let timeSeriesSlocTotal = {}
    let timeSeriesChurnTotal = {}
    let timeSeriesComplexity = []
    let timeSeriesSloc = []
    let timeSeriesChurn = []
        
    for (let i = gitMetricsIndexFrom; i < gitMetricsIndexTo; i++) {
        
        // prepare complexity data for chart
        for (const [key, value] of Object.entries(commit_metrics[i].ws_complexity)) {
            
            let filter = true
            if (Object.keys(selectedNodesMap).length > 0) {
                for (const [selectedNode, v] of Object.entries(selectedNodesMap)) {
                    if (selectedNode.includes(key.toLowerCase())) {
                        filter = false
                    }
                }
            } else {
                filter = false
            }
            
            if (filter == true) {
                continue
            }
            
            for (const [file, complexity] of Object.entries(timeSeriesComplexityTotal)) {
                if (file !== key) {
                    timeSeriesComplexity.push(
                        {
                            'filepath' : file,
                            'wscomplexity' : complexity,
                            'date': commit_metrics[i].exact_date.replace(/_/g, "-")
                        }
                        )
                    }
                }
                
                timeSeriesComplexityTotal[key] = value
                
                let timeSeriesComplexityEntry = {
                    'filepath' : key,
                    'wscomplexity' : value,
                    'date': commit_metrics[i].exact_date.replace(/_/g, "-") // TODO ...
                }
                timeSeriesComplexity.push(timeSeriesComplexityEntry)
            }
            
            // prepare sloc data for chart
            for (const [key, value] of Object.entries(commit_metrics[i].sloc)) {
                
                let filter = true
                if (Object.keys(selectedNodesMap).length > 0) {
                    for (const [selectedNode, v] of Object.entries(selectedNodesMap)) {
                        if (selectedNode.includes(key.toLowerCase())) {
                            filter = false
                        }
                    }
                } else {
                    filter = false
                }
                
                if (filter == true) {
                    continue
                }
                
                for (const [file, sloc] of Object.entries(timeSeriesSlocTotal)) {
                    if (file !== key) {
                        timeSeriesSloc.push(
                            {
                                'filepath' : file,
                                'sloc' : sloc,
                                'date': commit_metrics[i].exact_date.replace(/_/g, "-")
                            }
                            )
                        }
                    }
                    
                    timeSeriesSlocTotal[key] = value
                    
                    let timeSeriesSlocEntry = {
                        'filepath' : key,
                        'sloc' : value,
                        'date': commit_metrics[i].exact_date.replace(/_/g, "-") // TODO ...
                    }
                    timeSeriesSloc.push(timeSeriesSlocEntry)
                }
                
                
                // prepare churn data for chart
                for (const [key, value] of Object.entries(commit_metrics[i].churn)) {
                    let filter = true
                    if (Object.keys(selectedNodesMap).length > 0) {
                        for (const [selectedNode, v] of Object.entries(selectedNodesMap)) {
                            if (selectedNode.includes(key.toLowerCase())) {
                                filter = false
                            }
                        }
                    } else {
                        filter = false
                    }
                    
                    if (filter == true) {
                        continue
                    }
                    
                    for (const [file, churn] of Object.entries(timeSeriesChurnTotal)) {
                        if (file !== key) {
                            timeSeriesChurn.push(
                                {
                                    'filepath' : file,
                                    'churn' : churn,
                                    'date': commit_metrics[i].exact_date.replace(/_/g, "-")
                                }
                                )
                            }
                        }
                        
                        timeSeriesChurnTotal[key] = value
                        
                        let timeSeriesChurnEntry = {
                            'filepath' : key,
                            'churn' : value,
                            'date': commit_metrics[i].exact_date.replace(/_/g, "-") // TODO ...
                        }
                        timeSeriesChurn.push(timeSeriesChurnEntry)
                    }
                }
                
                let complexityChart = LineChart(timeSeriesComplexity, {
                    x: d => Date.parse(d.date),
                    y: d => d.wscomplexity,
                    z: d => d.filepath,
                    yLabel: "Whitespace Complexity",
                    width: 1000,
                    height: 300,
                    color: "lightsteelblue",
                    voronoi: false,
                    id: "timeSeriesComplexityChart"
                })
                
                let slocChart = LineChart(timeSeriesSloc, {
                    x: d => Date.parse(d.date),
                    y: d => d.sloc,
                    z: d => d.filepath,
                    yLabel: "SLOC",
                    width: 1000,
                    height: 300,
                    color: "lightsteelblue",
                    voronoi: false,
                    id: "timeSeriesSlocChart"
                })
                
                let churnChart = LineChart(timeSeriesChurn, {
                    x: d => Date.parse(d.date),
                    y: d => d.churn,
                    z: d => d.filepath,
                    yLabel: "Code churn",
                    width: 1000,
                    height: 300,
                    color: "lightsteelblue",
                    voronoi: false,
                    id: "timeSeriesChurnChart"
                })
                
                document.getElementById("my_dataviz").appendChild(complexityChart);
                document.getElementById("time_series_sloc").appendChild(slocChart);
                document.getElementById("my_dataviz2").appendChild(churnChart);
            }
            
function generateChangeCouplingChart() {

        let flows = []
        let locations = []
        let locationId = 0

        let locationColorMap = {}

        for (let i = gitMetricsIndexFrom; i < gitMetricsIndexTo; i++) {

        // prepare change coupling data for chart
        if (commit_metrics[i].links.length > 0) {
            
            for (link of commit_metrics[i].links) {
                
                const matchingSourceKey = link.source
                const matchingTargetKey = link.target
 
                let filter = true
                if (Object.keys(selectedNodesMap).length > 0) {
                    for (const [selectedNode, v] of Object.entries(selectedNodesMap)) {
                        if ( selectedNode.includes(matchingSourceKey.toLowerCase()) || selectedNode.includes(matchingTargetKey.toLowerCase()) ) {
                            filter = false
                        }
                    }
                } else {
                    filter = false
                }

                if (filter == true) {
                    continue
                }

                if ( !(locations.find(e => e.name === matchingSourceKey)) ) {
                    
                    if ( !(matchingSourceKey in locationColorMap) ) {
                        let randomColor = "#000000".replace(/0/g,function(){return (~~(Math.random()*16)).toString(16);});
                        locationColorMap[matchingSourceKey] = randomColor
                    }
                    
                    let location = {
                        'id': locationId,
                        'name': matchingSourceKey,
                        'color': locationColorMap[matchingSourceKey]
                    }
                    locations.push(location)
                    
                    let flow = {
                        'from' : locationId,
                        'to' : locationId,
                        'quantity': 0
                        
                    }
                    flows.push(flow)
                    locationId += 1
                }
                
                if ( !(locations.find(e => e.name === matchingTargetKey)) ) {
                    
                    if ( !(matchingTargetKey in locationColorMap) ) {
                        
                        // find the corresponding node color
                        for (const [key, value] of Object.entries(nodeColorMap)) {
                            if (key.includes(matchingTargetKey)) {
                                locationColorMap[matchingTargetKey] = value
                            }
                        }

                        // if (matchingTargetKey in nodeColorMap) {
                        //     locationColorMap[matchingTargetKey] = nodeColorMap[matchingTargetKey]
                        // } else {
                        //     console.log("should not happen")
                        //     locationColorMap[matchingTargetKey] = '#FFFFFF' // "#000000".replace(/0/g,function(){return (~~(Math.random()*16)).toString(16);});
                        // }
                    }
                    
                    let location = {
                        'id': locationId,
                        'name': matchingTargetKey,
                        'color': locationColorMap[matchingTargetKey]
                    }
                    
                    locations.push(location)
                    let flow = {
                        'from' : locationId,
                        'to' : locationId,
                        'quantity': 0
                        
                    }
                    flows.push(flow)
                    locationId += 1
                }
                
                const iSource = locations.findIndex(e => e.name === matchingSourceKey);
                const iTarget = locations.findIndex(e => e.name === matchingTargetKey);
                
                if (iSource > -1 && iTarget > -1) {
                    let flow = {
                        'from' : locations[iSource].id,
                        'to' : locations[iTarget].id,
                        'quantity': 15
                    }
                    flows.push(flow)
                }                            
                
            }
            
        }
    
    }

    for (let n = 0; n < locationId; n++) {
        for (let m = 0; m < locationId; m++) {
            if ( !(flows.find(e => e.from === n && e.to === m )) ) {
                let flow = {
                    'from' : n,
                    'to' : m,
                    'quantity': 0
                }
                flows.push(flow)
            }
        }
    }

    // Borrowed from this great blog entry:
    // https://blog.noser.com/d3-js-chord-diagramm-teil-2-benutzerdefinierte-sortierung-und-kurvenformen/

    var matrix = [];

    //Map list of data to matrix
    flows.forEach(function (flow) {
        
        //Initialize sub-array if not yet exists
        if (!matrix[flow.to]) {
            matrix[flow.to] = [];
        }
        
        matrix[flow.to][flow.from] = flow.quantity;
    });

/*//////////////////////////////////////////////////////////
/////////////// Initiate Chord Diagram /////////////////////
//////////////////////////////////////////////////////////*/
let size = 900;
let dr = 40; //radial translation for group names
let dx = 20; //horizontal translation for group names
let margin = { top: 0, right: 50, bottom: 50, left: 50 };
let chordWidth = (size + 200) - margin.left - margin.right;
let chordHeight = size - margin.top - margin.bottom;
let innerRadius = Math.min(chordWidth, chordHeight) * .39;
let outerRadius = innerRadius * 1.08;

let root = d3.select("#change_coupling_chord_diagram");

//Generate tooltip already, but keep it invisible for now.
var toolTip = root.append("div")
.classed("tooltip", true)
.style("opacity", 0)
.style("position", "absolute")
.style("text-align", "center")
.style("padding", "6px")
.style("font", "10px sans-serif")
.style("color", "black")
.style("background", "silver")
.style("border", "1px solid gray")
.style("border-radius", "8px")
.style("pointer-events", "none");

var focusedChordGroupIndex = null;

/*Initiate the SVG*/
//D3.js v3!
var svg = root.append("svg:svg")
.attr("width", chordWidth + margin.left + margin.right)
.attr("height", chordHeight + margin.top + margin.bottom)
.attr("id", "svg_change_coupling_chord_diagram");

var container = svg.append("g")
.attr("transform", "translate(" + 
(margin.left + chordWidth / 2) + "," + 
(margin.top + chordHeight / 2) + ")");

var chord = customChordLayout()
.padding(0.04)
.sortSubgroups(d3.descending) /*sort the chords inside an arc from high to low*/
.sortChords(d3.ascending) /*which chord should be shown on top when chords cross. Now the largest chord is at the top*/
.matrix(matrix);

/*//////////////////////////////////////////////////////////
////////////////// Draw outer Arcs /////////////////////////
//////////////////////////////////////////////////////////*/
var arc = d3.arc()
.innerRadius(innerRadius)
.outerRadius(outerRadius);

var g = container.selectAll("g.group")
.data(chord.groups)
.enter()
.append("svg:g")
.attr("class", function (d) { return "group group-" + locations[d.index].id; });

g.append("svg:path")
.attr("d", arc)
.style("fill", function (d) { 
    return locations[d.index].color; 
})
.style("stroke", function (d) { 
    return d3.rgb(locations[d.index].color).brighter(); 
})
.on("click", function (event, d) { highlightChords(d.index) }) // .on("click", function (d) { highlightChords(d.index) })
.on("mouseover", function(event, i) { 
    showArcToolTip(event, i);
})
.on("mouseout", function(d) { hideToolTip() });

/*//////////////////////////////////////////////////////////
//////////////// Initiate inner chords /////////////////////
//////////////////////////////////////////////////////////*/
var chords = container.selectAll("path.chord")
.data(chord.chords)
.enter()
.append("svg:path")
.attr("class", function (d) {
    return "chord chord-source-" + d.source.index + " chord-target-" + d.target.index;
})
.attr("d", customChordPathGenerator().radius(innerRadius))
//Change the fill to reference the unique gradient ID
//of the source-target combination
.style("fill", function (d) {
    return "url(#chordGradient-" + d.source.index + "-" + d.target.index + ")";
})
.style("stroke", function (d) {
    return "url(#chordGradient-" + d.source.index + "-" + d.target.index + ")";
})
.style("fill-opacity", "0.7")
.on("mouseover", function(event, i) { 
    if (focusedChordGroupIndex === null || 
        i.source.index === focusedChordGroupIndex || 
        i.target.index === focusedChordGroupIndex) {
            if (focusedChordGroupIndex === null) {
                d3.selectAll(".chord")
                .style("fill-opacity", 0.2)
                .style("stroke-opacity", 0.2);
                d3.select(this).style("fill-opacity", 1);
            }
            else {
                d3.selectAll(".chord.chord-source-" + focusedChordGroupIndex + ", " + 
                ".chord.chord-target-" + focusedChordGroupIndex)
                .style("fill-opacity", 0.2)
                .style("stroke-opacity", 0.2);
                d3.select(this).style("fill-opacity", 1);
            }
            
            showChordToolTip(event, i);
        }
    })
    .on("mouseout", function(d) { 
        if (focusedChordGroupIndex === null) {
            d3.selectAll(".chord")
            .style("fill-opacity", 0.7)
            .style("stroke-opacity", 1);
        }
        else {
            d3.selectAll(".chord.chord-source-" + focusedChordGroupIndex + ", " +
            ".chord.chord-target-" + focusedChordGroupIndex)
            .style("fill-opacity", 0.7)
            .style("stroke-opacity", 1);
        }
        
        hideToolTip();
    });
    
    //Cf https://www.visualcinnamon.com/2016/06/orientation-gradient-d3-chord-diagram
    //Create a gradient definition for each chord
    var grads = svg.append("defs").selectAll("linearGradient")
    .data(chord.chords)
    .enter().append("linearGradient")
    //Create a unique gradient id per chord: e.g. "chordGradient-0-4"
    .attr("id", function (d) {
        return "chordGradient-" + d.source.index + "-" + d.target.index;
    })
    //Instead of the object bounding box, use the entire SVG for setting locations
    //in pixel locations instead of percentages (which is more typical)
    .attr("gradientUnits", "userSpaceOnUse")
    //The full mathematical formula to find the x and y locations
    .attr("x1", function (d, i) {
        return innerRadius * Math.cos((d.source.endAngle - d.source.startAngle) / 2 +
        d.source.startAngle - Math.PI / 2);
    })
    .attr("y1", function (d, i) {
        return innerRadius * Math.sin((d.source.endAngle - d.source.startAngle) / 2 +
        d.source.startAngle - Math.PI / 2);
    })
    .attr("x2", function (d, i) {
        return innerRadius * Math.cos((d.target.endAngle - d.target.startAngle) / 2 +
        d.target.startAngle - Math.PI / 2);
    })
    .attr("y2", function (d, i) {
        return innerRadius * Math.sin((d.target.endAngle - d.target.startAngle) / 2 +
        d.target.startAngle - Math.PI / 2);
    });
    
    //Set the starting color (at 0%)
    grads.append("stop")
    .attr("offset", "0%")
    .attr("stop-color", function (d) { return locations[d.source.index].color; });
    
    //Set the ending color (at 100%)
    grads.append("stop")
    .attr("offset", "100%")
    .attr("stop-color", function (d) { return locations[d.target.index].color; });
    
    
    /*//////////////////////////////////////////////////////////
    ////////////////// Initiate Ticks //////////////////////////
    //////////////////////////////////////////////////////////*/
    var ticks = g.append("svg:g")
    .selectAll("g.ticks")
    .data(groupTicks)
    .enter().append("svg:g")
    .attr("transform", function (d) {
        return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
        + "translate(" + outerRadius + 40 + ",0)";
    });
    
    /*Append the tick around the arcs*/
    ticks.append("svg:line")
    .attr("x1", 1)
    .attr("y1", 0)
    .attr("x2", 6)
    .attr("y2", 0)
    .attr("class", "ticks")
    .style("stroke", "#FFF")
    .style("stroke-width", "1.5px");
    
    let labelColor = "#FFF"
    if (!darkMode) { labelColor = "#333333"}
    
    /*Add the labels for the ticks*/
    ticks.append("svg:text")
    .attr("class", "tickLabels")
    .attr("x", 12)
    .attr("dy", ".35em")
    .style("font-size", "10px")
    .style("font-family", "sans-serif")
    .attr("fill", labelColor)
    .attr("transform", function (d) { 
        return d.angle > Math.PI ? "rotate(180)translate(-25)" : null; 
    })
    .style("text-anchor", function (d) { 
        return d.angle > Math.PI ? "end" : null; 
    })
    //.text(function (d) { return d.label; });
    
    /*//////////////////////////////////////////////////////////
    ////////////////// Initiate Names //////////////////////////
    //////////////////////////////////////////////////////////*/
    g.append("svg:text")
    .each(function (d) { d.angle = (d.startAngle + d.endAngle) / 2; })
    .attr("dy", ".35em")
    .attr("class", "titles")
    .style("font-size", "10px")
    .style("font-family", "sans-serif")
    .attr("fill", labelColor)
    .attr("text-anchor", function (d) { 
        return d.angle > Math.PI ? "end" : null; 
    })
    .attr("transform", function (d) {
        var r = outerRadius + dr;
        var angle = d.angle + ((3 *Math.PI) / 2);
        var x = r * Math.cos(angle);
        var y = r * Math.sin(angle);
        
        if (d.angle > Math.PI) {
            x -= dx;
        }
        else {
            x += dx;
        }
        
        return "translate(" + x + ", " + y + ")";
    })
    .text(function (d, i) {
        if (locations[i].name.includes("/")) {
            return locations[i].name.substring(locations[i].name.lastIndexOf('/') + 1)
        } else {
            return locations[i].name
        }        
    });
    
    /*Lines from labels to arcs*/
    /*part in radial direction*/
    this.g.append("line")
    .attr("x1", function (d) { 
        return outerRadius * Math.cos(d.angle + ((3 * Math.PI) / 2)); 
    })
    .attr("y1", function (d) { 
        return outerRadius * Math.sin(d.angle + ((3 * Math.PI) / 2)); 
    })
    .attr("x2", function (d) { 
        return (outerRadius + dr) * Math.cos(d.angle + ((3 * Math.PI) / 2)); 
    })
    .attr("y2", function (d) { 
        return (outerRadius + dr) * Math.sin(d.angle + ((3 * Math.PI) / 2)); 
    })
    .style("stroke", "#FFF")
    .style("stroke-width", "0.5px");
    
    /*horizontal part*/
    this.g.append("line")
    .attr("x1", function (d) { 
        return (outerRadius + dr) * Math.cos(d.angle + ((3 * Math.PI) / 2)); 
    })
    .attr("y1", function (d) { 
        return (outerRadius + dr) * Math.sin(d.angle + ((3 * Math.PI) / 2)); 
    })
    .attr("x2", function (d) {
        var x = (outerRadius + dr) * Math.cos(d.angle + ((3 * Math.PI) / 2));
        if (d.angle > Math.PI) {
            x -= dx - 5;
        }
        else {
            x += dx - 5;
        }
        return x;
    })
    .attr("y2", function (d) { 
        return (outerRadius + dr) * Math.sin(d.angle + ((3 * Math.PI) / 2)); 
    })
    .style("stroke", "#FFF")
    .style("stroke-width", "0.5px");
    
    /*//////////////////////////////////////////////////////////
    ////////////////// Extra Functions /////////////////////////
    //////////////////////////////////////////////////////////*/
    
    /*Returns an array of tick angles and labels, given a group*/
    function groupTicks(d) {
        var anglePerPerson = (d.endAngle - d.startAngle) / d.value;
        return d3.range(0, d.value, 100).map(function (v, i) {
            return {
                angle: v * anglePerPerson + d.startAngle,
                label: i % 5 ? null : v //Each 5th tick has a label
            };
        });
    };
    
    //Hides all chords except the chords connecting to the subgroup / 
    //location of the given index.
    function highlightChords(index) {
        //If this subgroup is already highlighted, toggle all chords back on.
        if (focusedChordGroupIndex === index) {
            showAllChords();
            return;
        }
        
        hideAllChords();
        
        //Show only the ones with source or target == index
        d3.selectAll(".chord-source-" + index + ", .chord-target-" + index)
        .transition().duration(500)
        .style("fill-opacity", "0.7")
        .style("stroke-opacity", "1");
        
        focusedChordGroupIndex = index;
    };
    
    function showAllChords() {
        svg.selectAll("path.chord")
        .transition().duration(500)
        .style("fill-opacity", "0.7")
        .style("stroke-opacity", "1");
        
        focusedChordGroupIndex = null;
    };
    
    function hideAllChords() {
        svg.selectAll("path.chord")
        .transition().duration(500)
        .style("fill-opacity", "0")
        .style("stroke-opacity", "0");
    };
    
    function showChordToolTip(event, chord) {
        var prompt = "";
        
        // if (chord.source.index !== chord.target.index) {
        //     prompt += chord.source.value + " Kunden gingen von " + 
        //     locations[chord.target.index].name + " nach " + 
        //     locations[chord.source.index].name + ".";
        //     prompt += "<br>";
        //     prompt += chord.target.value + " Kunden gingen von " + 
        //     locations[chord.source.index].name + " nach " + 
        //     locations[chord.target.index].name + ".";
        // }
        // else {
        //     prompt += chord.source.value + " Kunden blieben in " + 
        //     locations[chord.source.index].name + ".";
        // }
        
        prompt += locations[chord.target.index].name + "<br>" + "... changed together with ... " + "<br>" + locations[chord.source.index].name + ".";
        
        const[x, y] = d3.pointer(event);    
        
        toolTip
        .style("opacity", 1)
        .style("font-size", "10px")
        .html(prompt)
        .style("left", x - toolTip.node().getBoundingClientRect().width / 32  + "px") // .style("left", d3.event.pageX - toolTip.node().getBoundingClientRect().width / 2 + "px")
        .style("top", y + 300 + "px"); // .style("top", (d3.event.pageY - 50) + "px");
    };
    
    function showArcToolTip(event, arc) {
        const[x, y] = d3.pointer(event);
        // console.log(locations)
        // console.log(arc)
        
        var prompt = locations[arc.index].name + "."; //Math.round(arc.value) 
        
        toolTip
        .style("opacity", 1)
        .html(prompt)
        .style("left", x + toolTip.node().getBoundingClientRect().width  + "px")
        .style("top", y + 300 + "px");
    };
    
    function hideToolTip() {
        toolTip.style("opacity", 0);
    };
    
    ////////////////////////////////////////////////////////////
    //////////// Custom Chord Layout Function //////////////////
    /////// Places the Chords in the visually best order ///////
    ///////////////// to reduce overlap ////////////////////////
    ////////////////////////////////////////////////////////////
    //////// Slightly adjusted by Nadieh Bremer ////////////////
    //////////////// VisualCinnamon.com ////////////////////////
    ////////////////////////////////////////////////////////////
    ////// Original from the d3.layout.chord() function ////////
    ///////////////// from the d3.js library ///////////////////
    //////////////// Created by Mike Bostock ///////////////////
    ////////////////////////////////////////////////////////////
    function customChordLayout() {
        var ε = 1e-6, ε2 = ε * ε, π = Math.PI, τ = 2 * π, τε = τ - ε, halfπ = π / 2, d3_radians = π / 180, d3_degrees = 180 / π;
        var chord = {}, chords, groups, matrix, n, padding = 0, sortGroups, sortSubgroups, sortChords;
        function relayout() {
            var subgroups = {}, groupSums = [], groupIndex = d3.range(n), subgroupIndex = [], k, x, x0, i, j;
            var numSeq;
            chords = [];
            groups = [];
            k = 0, i = -1;
            
            while (++i < n) {
                x = 0, j = -1, numSeq = [];
                while (++j < n) {
                    x += matrix[i][j];
                }
                groupSums.push(x);
                //////////////////////////////////////
                ////////////// New part //////////////
                //////////////////////////////////////
                for (var m = 0; m < n; m++) {
                    numSeq[m] = (n + (i - 1) - m) % n;
                }
                subgroupIndex.push(numSeq);
                //////////////////////////////////////
                //////////  End new part /////////////
                //////////////////////////////////////
                k += x;
            }//while
            
            k = (τ - padding * n) / k;
            x = 0, i = -1;
            while (++i < n) {
                x0 = x, j = -1;
                while (++j < n) {
                    var di = groupIndex[i], dj = subgroupIndex[di][j], v = matrix[di][dj], a0 = x, a1 = x += v * k;
                    subgroups[di + "-" + dj] = {
                        index: di,
                        subindex: dj,
                        startAngle: a0,
                        endAngle: a1,
                        value: v
                    };
                }//while
                
                groups[di] = {
                    index: di,
                    startAngle: x0,
                    endAngle: x,
                    value: (x - x0) / k
                };
                x += padding;
            }//while
            
            i = -1;
            while (++i < n) {
                j = i - 1;
                while (++j < n) {
                    var source = subgroups[i + "-" + j], target = subgroups[j + "-" + i];
                    if (source.value || target.value) {
                        chords.push(source.value < target.value ? {
                            source: target,
                            target: source
                        } : {
                            source: source,
                            target: target
                        });
                    }//if
                }//while
            }//while
            if (sortChords) resort();
        }//function relayout
        
        function resort() {
            chords.sort(function (a, b) {
                return sortChords((a.source.value + a.target.value) / 2, (b.source.value + b.target.value) / 2);
            });
        }
        chord.matrix = function (x) {
            if (!arguments.length) return matrix;
            n = (matrix = x) && matrix.length;
            chords = groups = null;
            return chord;
        };
        chord.padding = function (x) {
            if (!arguments.length) return padding;
            padding = x;
            chords = groups = null;
            return chord;
        };
        chord.sortGroups = function (x) {
            if (!arguments.length) return sortGroups;
            sortGroups = x;
            chords = groups = null;
            return chord;
        };
        chord.sortSubgroups = function (x) {
            if (!arguments.length) return sortSubgroups;
            sortSubgroups = x;
            chords = null;
            return chord;
        };
        chord.sortChords = function (x) {
            if (!arguments.length) return sortChords;
            sortChords = x;
            if (chords) resort();
            return chord;
        };
        chord.chords = function () {
            if (!chords) relayout();
            return chords;
        };
        chord.groups = function () {
            if (!groups) relayout();
            return groups;
        };
        return chord;
    };
    
    ////////////////////////////////////////////////////////////
    //////////// Custom Chord Path Generator ///////////////////
    ///////// Uses cubic bezier curves with quadratic //////////
    /////// spread of control points to minimise overlap ///////
    ////////////////// of adjacent chords. /////////////////////
    ////////////////////////////////////////////////////////////
    /////// Original from the d3.svg.chord() function //////////
    ///////////////// from the d3.js library ///////////////////
    //////////////// Created by Mike Bostock ///////////////////
    ////////////////////////////////////////////////////////////
    function customChordPathGenerator() {
        var source = function(d) { return d.source; };
        var target = function(d) { return d.target; };
        var radius = function(d) { return d.radius; };
        var startAngle = function(d) { return d.startAngle; };
        var endAngle = function(d) { return d.endAngle; };
        
        function chord(d, i) {
            var s = subgroup(this, source, d, i),
            t = subgroup(this, target, d, i);
            
            var path = "M" + s.p0
            + arc(s.r, s.p1, s.a1 - s.a0) + (equals(s, t)
            ? curve(s.r, s.p1, s.a1, s.r, s.p0, s.a0)
            : curve(s.r, s.p1, s.a1, t.r, t.p0, t.a0)
            + arc(t.r, t.p1, t.a1 - t.a0)
            + curve(t.r, t.p1, t.a1, s.r, s.p0, s.a0))
            + "Z";
            
            return path;
        }
        
        function subgroup(self, f, d, i) {
            var subgroup = f.call(self, d, i),
            r = radius.call(self, subgroup, i),
            a0 = startAngle.call(self, subgroup, i) - (Math.PI / 2),
            a1 = endAngle.call(self, subgroup, i) - (Math.PI / 2);
            
            return {
                r: r,
                a0: a0,
                a1: a1,
                p0: [r * Math.cos(a0), r * Math.sin(a0)],
                p1: [r * Math.cos(a1), r * Math.sin(a1)]
            };
        }
        
        function equals(a, b) {
            return a.a0 == b.a0 && a.a1 == b.a1;
        }
        
        function arc(r, p, a) {
            return "A" + r + "," + r + " 0 " + +(a > Math.PI) + ",1 " + p;
        }
        
        function curve(r0, p0, a0, r1, p1, a1) {
            var deltaAngle = Math.abs(mod((a1 - a0 + Math.PI), (2 * Math.PI)) - Math.PI);
            var radialControlPointScale = Math.pow((Math.PI - deltaAngle) / Math.PI, 2) * 0.9;
            var controlPoint1 = [p0[0] * radialControlPointScale, p0[1] * radialControlPointScale];
            var controlPoint2 = [p1[0] * radialControlPointScale, p1[1] * radialControlPointScale];
            var cubicBezierSvg = "C " + controlPoint1[0] + " " + controlPoint1[1] + ", " + 
            controlPoint2[0] + " " + controlPoint2[1] + ", " + 
            p1[0] + " " + p1[1];
            return cubicBezierSvg;
        }
        
        function mod(a, n) {
            return (a % n + n) % n;
        }
        
        chord.radius = function(v) {
            if (!arguments.length) return radius;
            radius = typeof v === "function" ? v : function() { return v; };
            return chord;
        };
        
        chord.source = function(v) {
            if (!arguments.length) return source;
            source = typeof v === "function" ? v : function() { return v; };
            return chord;
        };
        
        chord.target = function(v) {
            if (!arguments.length) return target;
            target = typeof v === "function" ? v : function() { return v; };
            return chord;
        };
        
        chord.startAngle = function(v) {
            if (!arguments.length) return startAngle;
            startAngle = typeof v === "function" ? v : function() { return v; };
            return chord;
        };
        
        chord.endAngle = function(v) {
            if (!arguments.length) return endAngle;
            endAngle = typeof v === "function" ? v : function() { return v; };
            return chord;
        };
        
        return chord;
    }
    
}