import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="emerge-dependency-visualizer",
    version="0.20.25",
    description="Visualize source code structure and dependencies in an interactive d3 application",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/glato/emerge",
    author="Grzegorz Lato",
    author_email="grzegorz.lato@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=[
        "astroid==2.5.0",
        "attrs==19.3.0",
        "autopep8==1.5.4",
        "click==7.1.2",
        "colorama==0.4.3",
        "coloredlogs==10.0",
        "decorator==4.4.2",
        "humanfriendly==4.18",
        "interrogate==1.2.0",
        "isort==4.3.21",
        "lazy-object-proxy==1.4.3",
        "networkx==2.4",
        "numpy",
        "prettytable==0.7.2",
        "py==1.10.0",
        "pycodestyle==2.6.0",
        "pygraphviz==1.6",
        "pylint==2.7.1",
        "pyparsing==2.4.7",
        "python-louvain==0.15",
        "PyYAML==5.4",
        "rope==0.16.0",
        "six==1.13.0",
        "tabulate==0.8.7",
        "toml==0.10.1",
        "wrapt==1.11.2"
    ],
    package_dir={
        "": ".",
        "emerge": "./emerge",
        "core": "./emerge/core",
        "languages": "./emerge/core/languages",
        "metrics": "./emerge/core/metrics",
        "faninout": "./emerge/core/metrics/faninout",
        "modulaity": "./emerge/core/metrics/modularity",
        "numberofmethods": "./emerge/core/metrics/numberofmethods",
        "sloc": "./emerge/core/metrics/sloc"
    },
    packages=['', 'emerge', 'core', 'languages', 'metrics', 'faninout', 'modulaity', 'numberofmethods', 'sloc'],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "emerge = emerge.emerge:run"
        ]
    },
)
