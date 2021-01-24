Roadmap
=======

The following fuzzy roadmap should show the direction in which this project is heading.

0.7.0 (Initial public release)
------------------------------

- File scan support for 8 languages (C, Groovy, Java, JavaScript, Kotlin, ObjC, Ruby, Swift)
- Basic entity scan/extraction for 4 languages (Groovy, Java, Kotlin, Swift)
- Basic implementation for 4 software metrics (SLOC, Number of Methods, Fan-In/Fan-Out, Modularity)
- Basic logging support with configurable log levels
- Configuration support based on YAML syntax to configure multiple/specific analyses
- Basic export of results/metrics for the following formats/outout
  - Code dependency, inheritance and complete graph (enriched with scan results/metrics)
    - GraphML (http://graphml.graphdrawing.org)
    - Graphviz DOT format (https://graphviz.org/doc/info/lang.html)
    - JavaScript format suited for a D3 force graph simulation (https://d3js.org)
    - Basic HTML/web application based on Bootstrap/D3 for interactive/exploratory analysis of graph/results/metrics with PDF export support
  - Export of scan results/metric and statistics as
    - Tabular console output
    - Tabular file output
    - JSON file output
- Basic unit test cases (tests directory in the project root) that covers some code of the language parsers, metrics and config, can be either included in the IDE as test cases or run directly from `run_tests.py`
- Example configuration templates for the currently supported languages
- Basic Visual Studio Code config (.vscode directory in the project root)
- Standalone python file `emerge.py` that can perform all the described functionality


0.7.1 - 1.x.0 (Further releases/ideas/unsorted)
-----------------------------------------------

- [ ] increase languages/parser precision for entity scan/extraction
- [ ] extend entity scan/extraction for further languages
- [ ] include framework import dependencies in swift
- [ ] write parser for further languages e.g. golang, rust, c++, python
- [ ] add more metrics for every language (e.g. McCabe, cognitive complexity (https://blog.sonarsource.com/cognitive-complexity-because-testability-understandability), depth of inheritance tree, ...)
- [x] implement a better web application export for D3 force graph simulation and interactive analysis
- [ ] implement a version/package that can easily be installed by using `pip`
- [ ] identify and fix more bugs 🐞
- [ ] add more/better unit tests
- [ ] increase docstring coverage to 80%
- [ ] any good ideas from contributors