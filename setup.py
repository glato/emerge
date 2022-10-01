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
    _re_searched = _version_re.search(f.read().decode('utf-8'))

    if _re_searched is None:
        raise RuntimeError('Cannot find version string')

    VERSION = str(ast.literal_eval(_re_searched.group(1)))

# This call to setup() does all the work
setup(
    name="emerge-viz",
    version=VERSION,
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
        "Programming Language :: Python :: 3.8",
    ],

    install_requires=[
        "wheel",
        "autopep8",
        "coloredlogs",
        "interrogate",
        "networkx",
        "sklearn",
        "numpy",
        "prettytable",
        "py",
        "pycodestyle",
        "pygraphviz",
        "pylint",
        "pyparsing",
        "python-louvain",
        "PyYAML",
        "tabulate",
    ],
    package_dir={
        "emerge": "emerge",
        "emerge/languages": "./emerge/languages",
        "emerge/metrics": "./emerge/metrics",
        "emerge/metrics/faninout": "./emerge/metrics/faninout",
        "emerge/metrics/modularity": "./emerge/metrics/modularity",
        "emerge/metrics/numberofmethods": "./emerge/metrics/numberofmethods",
        "emerge/metrics/sloc": "./emerge/metrics/sloc",
        "emerge/metrics/tfidf": ".emerge/metrics/tfidf"
    },
    packages=[
        'emerge',
        'emerge.languages',
        'emerge.metrics',
        'emerge.metrics.faninout',
        'emerge.metrics.modularity',
        'emerge.metrics.numberofmethods',
        'emerge.metrics.sloc',
        'emerge.metrics.tfidf'
    ],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "emerge = emerge.main:run"
        ]
    },
)
