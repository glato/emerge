"""
Contains an implemetation of a TF/IDF metric to extract semantic keywords from source code.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import Dict, Any

import logging
import coloredlogs

from sklearn.feature_extraction.text import TfidfVectorizer

# interfaces for inputs
from emerge.analysis import Analysis
from emerge.abstractresult import AbstractResult
from emerge.log import Logger

# enums and interface/type of the given metric
from emerge.metrics.metrics import CodeMetric

LOGGER = Logger(logging.getLogger('metrics'))
coloredlogs.install(level='E', logger=LOGGER.logger(), fmt=Logger.log_format)

class TFIDFMetric(CodeMetric):
    """Provides a metric based on TF-IDF to extract semantic keywords from source code."""

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.result_tokens: Dict[str, Any] = {}

        # pylint: disable=line-too-long
        """The following language specific stopwords should be excluded from the TF-IDF calculation."""
        self.language_specific_stopwords = {
            "JAVA":       {'void', 'new', 'public', 'private', 'static', 'import', 'null', 'set', 'char'},
            "KOTLIN":     {'null', 'val', 'fun', 'throw', 'any', 'private', 'override', 'import', 'sealed', 'const', 'object', 'set', 'return', 'this'},
            "OBJC":       {'include', 'struct', 'const', 'new', 'self', 'bool', 'object', 'return'},
            "SWIFT":      {'func', 'let', 'var', 'weak', 'return', 'true', 'false', 'line', 'file', 'try', 'override', 'self', 'keypath', 'case', 'guard', 'some', 'void', 'nil', 'throws', 'private', 'struct', 'bool', 'static', 'inout', 'int', 'string'},
            "RUBY":       {'true', 'false', 'require', 'module', 'class', 'def' ,'end', 'if', 'unless', 'begin', 'break', 'self', 'nil', 'void', 'do', 'super', 'int', 'bytes'},
            "GROOVY":     {'true', 'false', 'null', 'throw', 'return', 'static', 'public', 'private', 'protected', 'super', 'final', 'char', 'string', 'synchronized'},
            "JAVASCRIPT": {'var', 'obj', 'const', 'key', 'newobj', 'string', 'export', 'id', 'true', 'false', 'return', 'require', 'function', 'exports', 'null'},
            "TYPESCRIPT": {'break', 'case', 'this', 'import'},
            "C":          {'return', 'int', 'static', 'void', 'case', 'break', 'const', 'struct', 'printf', 'fprintf', 'unsinged', 'extern', 'char', 'float', 'sizeof'},
            "CPP":        {'return', 'int', 'static', 'void', 'case', 'break', 'const', 'struct', 'printf', 'fprintf', 'unsinged', 'extern', 'char', 'float', 'sizeof', 'string', 'bool', 'virtual'},
            "PY":         {'return', 'self', 'import', 'enum', 'true', 'false', 'none'}
        }

        """The following natural language stopwords should be excluded from the TF-IDF calculation.
        """
        self.stopwords = {
            'and', 'the', 'to', 'of', 'or', 'then', 'do', 'def', 'end', 'with', 'without', 'if', 'a', 'else', 'in', 'where', 'is', 'by', 'for', 'or', 'license', 'all', 'from', 'that', 'an', 'get', 'set', 'as', 'when', 'up', 'ok', 'may', 'foo', 'bar', 'baz', 'at'
        }

    @property
    def pretty_metric_name(self) -> str:
        return 'tfidf metric'

    def calculate_from_results(self, results: Dict[str, AbstractResult]):
        self.read_tokens_from_results(results)
        self.calculate_tfidf()

    def read_tokens_from_results(self, results: Dict[str, AbstractResult]):
        """Read tokens from results, perform preprocessing and store them locally in self.result_tokens."""
        for _, result in results.items():
            tokens_as_string = ''
            
            for token in result.scanned_tokens:
                if token.isalpha() and (token.lower() not in self.stopwords) \
                and (token.lower() not in self.language_specific_stopwords[result.scanned_language.name]):
                    tokens_as_string += token.lower()
                    tokens_as_string += ' '

            self.result_tokens[result.unique_name] = tokens_as_string


    def calculate_tfidf(self):
        """this is where the actual calculation of TF-IDF takes place. This is done via scikit-learn and TfidfVectorizer.
        After calculating the semantic keywords for any source code file or entity, we sort them by TF-IDF score and
        store up to max_tokens in the local_data of this metric, to further be collected from the analysis.
        """

        tfidf = TfidfVectorizer()
        sorted_tfidf = {}
        
        tfidf.fit_transform(self.result_tokens.values())
        feature_names = tfidf.get_feature_names_out()

        for name, _ in self.result_tokens.items():

            if not name in sorted_tfidf:
                sorted_tfidf[name] = {}
            
            response = tfidf.transform([self.result_tokens[name]])
            
            for col in response.nonzero()[1]:
                sorted_tfidf[name][feature_names[col]] = response[0, col]

            ordered_tfidf_by_name = {k: v for k, v in sorted(sorted_tfidf[name].items(), key=lambda item: item[1], reverse=True)}

            tfidf_metric_token_dict = {}
            max_tokens = 5
            count_tokens = 0
            for key, value in ordered_tfidf_by_name.items():
                if count_tokens < max_tokens:
                    tfidf_metric_token_dict['tag_' + key] = value
                    count_tokens += 1

            if name in self.local_data:
                self.local_data[name].update(tfidf_metric_token_dict)
            else:
                self.local_data[name] = tfidf_metric_token_dict
