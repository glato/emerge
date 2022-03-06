import pathlib

# borrowed from https://stackoverflow.com/questions/6786555/automatic-version-number-both-in-setup-py-setuptools-and-source-code
import re
import ast

from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

_version_re = re.compile(r'__version__\s+=\s+(.*)')
with open('emerge/appear.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

# This call to setup() does all the work
setup(
    name="emerge-viz",
    version=version,
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
        "attrs==19.3.0",
        "click==7.1.2",
        "colorama==0.4.3",
        "coloredlogs==10.0",
        "decorator==4.4.2",
        "humanfriendly==4.18",
        "isort==4.3.21",
        "lazy-object-proxy==1.4.3",
        "networkx==2.4",
        "sklearn",
        "numpy",
        "prettytable==0.7.2",
        "py==1.10.0",
        "pygraphviz==1.6",
        "pyparsing==2.4.7",
        "python-louvain==0.15",
        "PyYAML==5.4",
        "six==1.13.0",
        "tabulate==0.8.9",
        "toml==0.10.1",
        "wrapt==1.11.2"
    ],
    package_dir={
        "emerge": "emerge",
        "emerge/languages": "./emerge/languages",
        "emerge/metrics": "./emerge/metrics",
        "emerge/metrics/faninout": "./emerge/metrics/faninout",
        "emerge/metrics/modularity": "./emerge/metrics/modularity",
        "emerge/metrics/numberofmethods": "./emerge/metrics/numberofmethods",
        "emerge/metrics/sloc": "./emerge/metrics/sloc"
    },
    packages=['emerge', 'emerge.languages', 'emerge.metrics', 'emerge.metrics.faninout', 'emerge.metrics.modularity', 'emerge.metrics.numberofmethods', 'emerge.metrics.sloc'],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "emerge = emerge.main:run"
        ]
    },
)
