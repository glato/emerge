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

- This project uses pylint and flake8 with the given `.pylintrc` and `.flake8` configurations.

- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) is used in this project, but (unfortunately) with type checking mode off, the basic mode is a point in the future roadmap
- Docstring coverage is measured with [interrogate](https://pypi.org/project/interrogate/) and is about 25% for the first public release
