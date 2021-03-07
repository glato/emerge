"""
All abstract result classes.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from abc import ABC, abstractmethod
from typing import List


class AbstractResult(ABC):

    @property
    @abstractmethod
    def unique_name(self) -> str:
        ...

    @property
    @abstractmethod
    def analysis(self):
        ...


class AbstractFileResult(AbstractResult):

    @property
    @abstractmethod
    def scanned_tokens(self) -> List[str]:
        ...

    @property
    @abstractmethod
    def scanned_file_name(self) -> str:
        ...

    @property
    @abstractmethod
    def relative_file_path_to_analysis(self) -> str:
        ...

    @property
    @abstractmethod
    def absolute_dir_path(self) -> str:
        ...

    @property
    @abstractmethod
    def scanned_by(self) -> str:
        ...

    @property
    @abstractmethod
    def scanned_language(self) -> str:
        ...

    @property
    @abstractmethod
    def scanned_import_dependencies(self) -> List[str]:
        ...

    @property
    @abstractmethod
    def module_name(self) -> str:
        ...

    @property
    @abstractmethod
    def absolute_name(self) -> str:
        ...

    @classmethod
    @abstractmethod
    def create_file_result(cls, analysis, scanned_file_name, module_name, scanned_by, scanned_language, scanned_tokens):
        ...

    @abstractmethod
    def generate_entity_results_from_scopes(self, entity_keywords, entity_expression, comment_keywords) -> List:
        ...


class AbstractEntityResult(AbstractResult):

    @property
    @abstractmethod
    def scanned_tokens(self) -> List[str]:
        ...

    @property
    @abstractmethod
    def scanned_file_name(self) -> str:
        ...

    @property
    @abstractmethod
    def scanned_by(self) -> str:
        ...

    @property
    @abstractmethod
    def scanned_language(self) -> str:
        ...

    @property
    @abstractmethod
    def scanned_import_dependencies(self) -> List[str]:
        ...

    @property
    @abstractmethod
    def module_name(self) -> str:
        ...

    @property
    @abstractmethod
    def entity_name(self) -> str:
        ...

    @property
    @abstractmethod
    def scanned_inheritance_dependencies(self) -> List:
        ...
