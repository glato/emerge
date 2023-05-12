function edgeBetweenSearchTerms(sourceNode, targetNode) {
    let found = false
    searchTerms.forEach(element => {
        if ( (sourceNode.id.toLowerCase().includes(element)) && (targetNode.id.toLowerCase().includes(element)) ) {
            found = true
        }
    });
    return found
}

function searchTermsIncludedInNodeTags(sourceNode, targetNode) {
    let found = false
    searchTerms.forEach(element => {
        if ((stringIncludedInNodeTags(element, sourceNode) && stringIncludedInNodeTags(element, targetNode))) {
            found = true
        }
    });
    return found
}

function searchTermsIncludedInNodeContributors(sourceNode, targetNode) {
    let found = false
    searchTerms.forEach(element => {
        if ((stringIncludedInNodeContributors(element, sourceNode) && stringIncludedInNodeContributors(element, targetNode))) {
            console.log("edge found")
            found = true
        }
    });
    return found
}

function normalSearch(node) {
    let found = false
    searchTerms.forEach(element => {
        if (node.id.toLowerCase().includes(element)) {
            found = true
        }
    });
    return found
}

// the node is included in the current search OR if the search in included in one of the node's semantic tags 
function searchTermIncludedInNode(node) {
    let found = false
    searchTerms.forEach(element => {
        if (node.id.toLowerCase().includes(element)) {
            found = true
        }
    });
    return found
}

function searchTermIncludedInNodeTags(node) {
    let found = false
    searchTerms.forEach(element => {
        if ( stringIncludedInNodeTags(element, node) ) {
            found = true
        }
    });
    return found
}

function searchTermIncludedInNodeContributors(node) {
    let found = false
    searchTerms.forEach(element => {
        if ( stringIncludedInNodeContributors(element, node) ) {
            found = true
        }
    });
    return found
}
