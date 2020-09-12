emerge
======

emerge is a code analysis tool that can be used to gather insights about source code structure, metrics, dependencies and complexity of software projects. It can scan the source code of a project, calculate metric results and statistics, map the source code to graph structures (e.g. a dependency graph) and further export the results in some file formats or even create an interactive graph web application for further exploration. emerge is mainly written in Python 3.

![](https://raw.githubusercontent.com/glato/emerge/assets/github-assets/02-emerge-github.png)
![](https://raw.githubusercontent.com/glato/emerge/assets/github-assets/03-emerge-github.png)
![](https://raw.githubusercontent.com/glato/emerge/assets/github-assets/05-emerge-github.png)

## Goals of this project

*emerge* (/ɪˈməːdʒ/)

> - to appear by coming out of something or out from behind something
> - to become known, especially as a result of examining something or asking questions about it

The main goal of this project is to create a free/ open source tool, that can easily be used by anyone with interest in software development, software architecture and software metrics to gather more insights about those topics. Further is should facilitate/ support getting a better understanding of a software project and its architecture.

## The following features are currently supported by emerge

- File scan support for the following languages: C, Groovy, Java, JavaScript, Kotlin, ObjC, Ruby, Swift
- Basic entity scan/extraction (e.g. classes) for the following languages: Groovy, Java, Kotlin, Swift
- Basic implementation of the following software metrics: SLOC, Number of Methods, Fan-In/Fan-Out, Modularity
- Logging support with configurable log levels
- Configuration support based on YAML syntax to configure multiple/specific analyses
- Export of scan results/ metrics/ statistics for the following formats/ outputs
  - Code dependency, inheritance and complete graph (enriched with scan results/metrics)
  - [GraphML](http://graphml.graphdrawing.org)
  - [Graphviz DOT format](https://graphviz.org/doc/info/lang.html)
  - JavaScript format suited for a [D3 force graph simulation](https://github.com/d3/d3-force)
  - Basic HTML/ web application based on [Bootstrap](https://getbootstrap.com) and [D3](https://d3js.org) for interactive, exploratory analysis and data visualization of graphs/ results/ metrics with PDF export support (the UI is basically oriented on [Gephi](https://gephi.org))
  - Tabular console output
  - Tabular file output
  - JSON file output

## How to install and use emerge

At this time there is no simple installation by using pip (tbd), so the following steps should guide you how to install this tool and get it running.

**1.** Clone this repository

```
git clone https://github.com/glato/emerge.git
```

**2.** (*macOS*) Create a Python 3 virtual environment (optionally within the project structure)

```
cd emerge
python3 -m venv venv
```

**2.** (*ubuntu*) Install required packages and create a Python 3 virtual environment (optionally within the project structure)

```
apt-get install python3-venv python3-dev graphviz graphviz-dev
cd emerge
python3 -m venv venv
```

**3.** Before using/working with the tool, activate the virtual environment

```
source venv/bin/activate
```

**4.** (*macOS*) Install all required dependencies for the project with pip

```
pip install -r freeze.lst
```

**4.** (*ubuntu*) Install the wheel package, after that install all required dependencies for the project with pip

```
pip install wheel
pip install -r freeze.lst
```

**5.** Running unit tests from the command line

```
python run_tests.py
```

**6.** Running EMERGE as a standalone tool

```
python emerge.py 
usage: emerge.py [-h] [-c YAMLCONFIG] [-v] [-d] [-s]

Welcome to emerge 0.7.0 (2020-08-28 12:12:07).

optional arguments:
  -h, --help            show this help message and exit
  -c YAMLCONFIG, --config YAMLCONFIG
                        set yaml config file
  -v, --verbose         set logging level to INFO
  -d, --debug           set logging level to DEBUG
  -s, --silent          run silently without any console output
```

**7.** Create a YAML configuration for your scan or copy/adjust a template example from the configs directory. The template examples in `emerge/configs` should be mostly self-documenting. For a quick run, it's enough to adjust `source_directory` and `directory` in `export`.

```yaml
---
project_name: c-example-project
loglevel: info
analyses:
- analysis_name: check_c_files
  source_directory: /Users/user1/emerge/project/source/github/linux-5.8.5/crypto
  only_permit_languages:
  - c
  only_permit_file_extensions:
  - .c
  - .h
  file_scan:
  - number_of_methods
  - source_lines_of_code
  - dependency_graph
  - louvain_modularity
  - fan_in_out
  export:
  - directory: /Users/user1/emerge/project/export
  - graphml
  - dot
  - json
  - tabular_file
  - tabular_console_overall
  - d3
```

**8.** Running EMERGE with a specific YAML configuration (e.g. a customized `emerge/config/c-template.yaml`)

```
python emerge.py -c configs/c-template.yaml
```

... which should produce a similar output:

```
2020-09-10 15:31:51   analysis I 👉 starting to analyze c-example-project
2020-09-10 15:31:51   analysis I ⏩ performing analysis 1/1: check_c_files
2020-09-10 15:31:51   analysis I 👉 starting token extraction for file results in check_c_files
2020-09-10 15:31:51   analysis I ⏩ starting scan at directory: .../github/linux-5.8.5/crypto
...
2020-09-10 15:31:57   analysis I ✅ scanning complete
2020-09-10 15:31:57   analysis I 👉 starting code metric calculation for analysis check_c_files
2020-09-10 15:31:57   analysis I ⏩ calculating metric results for: number of methods metric
2020-09-10 15:32:38   analysis I ⏩ calculating metric results for: source lines of code metric
2020-09-10 15:32:38   analysis I ✅ done calculating code metric results
2020-09-10 15:32:38   analysis I 👉 starting graph metric calculation for analysis check_c_files
2020-09-10 15:32:38   analysis I ⏩ calculating metric results for: louvain modularity metric
2020-09-10 15:32:42   analysis I ⏩ calculating metric results for: fan in out metric
2020-09-10 15:32:42   analysis I ✅ done calculating graph metric results
2020-09-10 15:32:42     emerge I ✅ successfully copied output to /Users/user1/emerge/project/export/force-graph-html
2020-09-10 15:32:43   analysis I 👉 the following statistics were collected in check_c_files
+-------------------------------------+-------------------+
|                      statistic name | value             |
+-------------------------------------+-------------------+
|                        parsing_hits | 1196              |
|                    scanning_runtime | 00:00:06 + 424 ms |
|                       scanned_files | 163               |
|                       skipped_files | 16                |
|              extracted_file_results | 163               |
|    number-of-methods-metric-runtime | 00:00:40 + 331 ms |
| source-lines-of-code-metric-runtime | 00:00:00 + 99 ms  |
|   louvain-modularity-metric-runtime | 00:00:04 + 229 ms |
|           fan-in-out-metric-runtime | 00:00:00 + 18 ms  |
+-------------------------------------+-------------------+
2020-09-10 15:32:43   analysis I 👉 the following overall metrics were collected in check_c_files
+----------------------------------------------+------------------------------+
|                                  metric name | value                        |
+----------------------------------------------+------------------------------+
|                avg-number-of-methods-in-file | 17.91                        |
|                             avg-sloc-in-file | 224.44                       |
|         louvain-communities-dependency-graph | 11                           |
|          louvain-modularity-dependency-graph | 0.44                         |
| louvain-biggest-communities-dependency-graph | 0.24, 0.19, 0.14, 0.13, 0.11 |
|                  avg-fan-in-dependency-graph | 3.53                         |
|                 avg-fan-out-dependency-graph | 3.53                         |
|                  max-fan-in-dependency-graph | 132                          |
|             max-fan-in-name-dependency-graph | linux/module.h               |
|                 max-fan-out-dependency-graph | 18                           |
|            max-fan-out-name-dependency-graph | testmgr.c                    |
+----------------------------------------------+------------------------------+
2020-09-10 15:32:43   analysis I ✅ calculated and collected metric data
2020-09-10 15:32:43     emerge I ✅ total runtime: 00:00:52 + 166 ms
```

A full YAML configuration that contains both file and entity scan has the following format:

```yaml
---
project_name: java_project_example
loglevel: info
analyses:
- analysis_name: check_java_files_and_classes
  source_directory: /Users/user1/emerge/project/source
  only_permit_languages:
  - java
  only_permit_file_extensions:
  - .java
  file_scan:
  - number_of_methods
  - source_lines_of_code
  - dependency_graph
  - fan_in_out
  - louvain_modularity
  entity_scan:
  - dependency_graph
  - source_lines_of_code
  - number_of_methods
  - fan_in_out
  - louvain_modularity
  export:
  - directory: /Users/user1/emerge/project/export
  - graphml
  - dot
  - json
  - tabular_file
  - tabular_console_overall
  - d3
```

The YAML configuration is basically defined at the following levels:

## project level

| key                | value/ description |
|--------------------|--------------------|
| `project_name`     | a project name for all analyses, scans and exports |
| `loglevel`         | set a loglevel: `error` (silent, only errors), `info` (includes `error`) gives you basic logs about control flow, `debug` (includes `info`) will produce a lot of debug logs |
| `analyses`         | an array of analyses that can be configured individually, thus a project can contain one to many analyses. |
|                    | |

## analysis level

| key                           | value/ description |
|-------------------------------|--------------------|
| `analysis_name`               | a specific analysis name |
| `source_directory`            | the source directory where the recursive file scan should start |
| `ignore_files_containing`     | exclude the following files from the scan |
| `only_permit_languages`       | possible values include: java, kotlin, objc, swift, ruby, groovy, javascript, c - explicitly prevents any other language from scanning besides the one you set here |
| `only_permit_file_extensions` | explicitly permit the following file extensions you set here, e.g. `.java` |
| `file_scan`                   | perform a file scan, contains the metrics that should be applied on every source file |
| `entity_scan`                 | perform an entity scan, contains the metrics that should be applied on every entity (e.g. on every class) |
| `export`                      | contains any export formats that should be create as output |
|                               | |

## file_scan metrics

| key                    | value/ description |
|------------------------|--------------------|
| `dependency_graph`     | create a dependency graph structure based on source files, additional metrics will be added to the graph nodes |
| `source_lines_of_code` | apply a source lines of code metric to every file, create an overall metric |
| `number_of_methods`    | apply a number of methods metric to every file, create an overall metric |
| `fan_in_out`           | apply a fan in/ fan out graph metric to every file, create an overall metric |
| `louvain_modularity`   | apply a louvain modularity metric to every file, create an overall metric |
|                        | |

## entity_scan metrics

| key                    | value/ description |
|------------------------|--------------------|
| `dependency_graph`     | create a dependency graph structure based on extracted entities from files, additional metrics will be added to the graph nodes |
| `inheritance_graph`    | create an inheritance graph structure based on extracted entities from files, additional metrics will be added to the graph nodes |
| `complete_graph`       | create a complete graph structure (union of dependency/ inheritance graph) based on extracted entities from files, additional metrics will be added to the graph nodes |
| `source_lines_of_code` | apply a source lines of code metric to every entity, create an overall metric |
| `number_of_methods`    | apply a number of methods metric to every entity, create an overall metric |
| `fan_in_out`           | apply a fan in/ fan out graph metric to every entity, create an overall metric |
| `louvain_modularity`   | apply a louvain modularity metric to every entity, create an overall metric |
|                        | |

## export configuration

| key                       | value/ description |
|---------------------------|--------------------|
| `directory`               | the output directory for all specified export formats |
| `graphml`                 | create a graphML file that contains the graph structure and metric results mapped to the nodes of the graph |
| `tabular_file`            | create a tabular formatted text file that contains every metric and statistic result |
| `tabular_console`         | print a tabular formatted output to console that contains every metric and statistic result |
| `tabular_console_overall` | print a tabular formatted output to console that contains only overall metric and statistic results |
| `json`                    | create a JSON file that contains every metric and statistic result |
| `dot`                     | create a DOT file that contains the graph structure and metric results mapped to the nodes of the graph |
| `d3`                      | create a Bootstrap/D3 web application in the subfolder `force-graph-html` for further visual and interactive/ exploratory analysis |
|                           | |

## The current version (0.7.0) supports the following scan types/ parsing keywords

| Parsing/Language | Groovy | Java  | Kotlin | Swift                   | Ruby    | JavaScript | ObjC    | Ruby    |
|------------------|--------|-------|--------|-------------------------|---------|------------|---------|---------|
| Files            | yes    | yes   | yes    | yes                     | yes     | yes        | yes     | yes     |
| Entity type      | class  | class | class  | class (wth. extensions) | no      | no         | no      | no      |
|                  |        |       |        |                         |         |            |         |         |

- Parsing of further entity types (e.g. structs, ...) is planned for further development.

## Further development

- *Disclaimer*: The current version (0.7.0) is not yet stable, probably still has some 🐞 and is probably not yet suited for productive usage.
- Everyone is invited to contribute to this project, wether the contribution is related with development, testing, bug reporting or any other support. I would appreciate any help 👍. See [Contributing](Contributing.md) and [Credits](Credits.md) for further details.

