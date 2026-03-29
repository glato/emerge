"""
Tree-sitter based extraction of JavaScript module specifiers (import / require / import()).
"""

from __future__ import annotations

from typing import List, Optional

_js_parser = None


def _get_parser():
    global _js_parser
    if _js_parser is None:
        import tree_sitter_javascript as tsjs
        from tree_sitter import Language, Parser

        _js_parser = Parser(Language(tsjs.language()))
    return _js_parser


def _string_literal_value(node) -> str:
    raw = node.text.decode("utf-8", errors="replace")
    if len(raw) >= 2 and raw[0] in "\"'" and raw[-1] == raw[0]:
        return raw[1:-1]
    return raw


def _first_string_in_arguments(arguments_node) -> Optional[str]:
    for i in range(arguments_node.child_count):
        ch = arguments_node.children[i]
        if ch.type == "string":
            return _string_literal_value(ch)
    return None


def extract_javascript_module_specifiers(source: str) -> List[str]:
    """
    Parse JavaScript source and return module path strings from:
    - import ... from 'm' / import 'm'
    - require('m')
    - import('m') (dynamic import)
    Order follows a pre-order walk; duplicates are preserved (matches multiple statements).
    """
    parser = _get_parser()
    source_bytes = source.encode("utf-8", errors="replace")
    tree = parser.parse(source_bytes)
    root = tree.root_node
    out: List[str] = []

    def walk_import_statements(node):
        if node.type == "import_statement":
            for i in range(node.child_count):
                ch = node.children[i]
                if ch.type == "string":
                    out.append(_string_literal_value(ch))
        for i in range(node.child_count):
            walk_import_statements(node.children[i])

    def walk_call_expressions(node):
        if node.type == "call_expression" and node.child_count >= 2:
            callee = node.children[0]
            args_node = None
            for i in range(1, node.child_count):
                if node.children[i].type == "arguments":
                    args_node = node.children[i]
                    break
            if args_node is None:
                pass
            elif callee.type == "identifier" and callee.text == b"require":
                val = _first_string_in_arguments(args_node)
                if val is not None:
                    out.append(val)
            elif callee.type == "import":
                val = _first_string_in_arguments(args_node)
                if val is not None:
                    out.append(val)
        for i in range(node.child_count):
            walk_call_expressions(node.children[i])

    walk_import_statements(root)
    walk_call_expressions(root)
    return out
