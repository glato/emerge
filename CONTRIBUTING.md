Contributing to emerge
======================

Everyone is invited to contribute to this project, wether the contribution is related with development, testing, bug reporting or any other support.

## Getting started

Clone/fork this repository
```
https://github.com/glato/emerge.git
```

and get it running as a standalone tool (see [README](README.md) for a step by step howto) or for development in your favorite IDE ([VS Code](https://code.visualstudio.com) or [PyCharm](https://www.jetbrains.com/pycharm/)), then feel free to start contributing by using pull requests. I'd appreciate any contributions/support and help 👍.

## The following code style/convention/tooling details currently exist for this project.

- The code style in this project is based on the [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide for python code, with a minimal customization of those rules for pylint.

- This project uses [pylint](https://pypi.org/project/pylint/) with the following rule modification
```
pylint --msg-template "{path}:{line}:{column}:{category}:{symbol} - {msg}" --disable=all --enable=F,E,unneeded-not,invalid-name,unidiomatic-typecheck,too-many-lines,multiple-imports,comparison-with-itself,cyclic-import,too-many-ancestors,too-many-branches,too-many-statements,too-many-nested-blocks,consider-using-join,bad-classmethod-argument,unused-argument,protected-access,abstract-method,unreachable,duplicate-key,unnecessary-semicolon,global-variable-not-assigned,unused-variable,binary-op-exception,bad-format-string,anomalous-backslash-in-string,bad-open-mode emerge 
```

- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) is used in this project, but (unfortunately) with type checking mode off, the basic mode is a point in the future roadmap
- Docstring coverage is measured with [interrogate](https://pypi.org/project/interrogate/) and is about 25% for the first public release
