// based on https://copyprogramming.com/howto/javascript-dictionary-merge-best-methods-to-combine-key-value-pairs?utm_content=cmp-true
function mergeDicts(dict1, dict2) {
    const result = {};
    
    for (const key in dict1) {    
        if (dict2.hasOwnProperty(key)) {
            if ( Array.isArray(dict1[key]) && Array.isArray(dict2[key]) ) {
                result[key] = dict1[key].concat(dict2[key])
            } else if ( typeof dict1[key] === "object" && typeof dict2[key] === "object") {
                result[key] = Object.assign({}, dict1[key], dict2[key]);
            } else {
                result[key] = dict1[key] + dict2[key];
            }
        } else {
            result[key] = dict1[key];
        }
    }
    
    for (const key in dict2) {
        if (!dict1.hasOwnProperty(key)) {
            result[key] = dict2[key];
        }
    }
    return result;
}

function mergeDictsToMostCurrentValues(dict1, dict2) {
    const result = {};

    for (const key in dict1) {  

        if (dict2.hasOwnProperty(key)) {
            result[key] = dict2[key]
        } else {
            result[key] = dict1[key];
        }
    }

    for (const key in dict2) {
        if (!dict1.hasOwnProperty(key)) {
            result[key] = dict2[key];
        }
    }
    return result;
}