"""
Tree-sitter based extraction of Rust module / crate references from use, extern crate, and mod ...;.
"""

from __future__ import annotations

from typing import List

_rust_parser = None


def _get_parser():
    global _rust_parser
    if _rust_parser is None:
        import tree_sitter_rust as tsrust
        from tree_sitter import Language, Parser

        _rust_parser = Parser(Language(tsrust.language()))
    return _rust_parser


def _add_from_use_declaration(decl, out: List[str]) -> None:
    """Collect path strings from a use_declaration subtree."""
    for i in range(decl.child_count):
        ch = decl.children[i]
        if ch.type == "scoped_identifier":
            out.append(ch.text.decode("utf-8", errors="replace"))
        elif ch.type == "scoped_use_list":
            for j in range(ch.child_count):
                c2 = ch.children[j]
                if c2.type == "scoped_identifier":
                    out.append(c2.text.decode("utf-8", errors="replace"))
                    break
                if c2.type == "identifier":
                    out.append(c2.text.decode("utf-8", errors="replace"))
                    break
        elif ch.type == "use_wildcard":
            for j in range(ch.child_count):
                if ch.children[j].type == "scoped_identifier":
                    out.append(ch.children[j].text.decode("utf-8", errors="replace"))
        elif ch.type == "use_list":
            for j in range(ch.child_count):
                if ch.children[j].type == "scoped_identifier":
                    out.append(ch.children[j].text.decode("utf-8", errors="replace"))
        elif ch.type == "use_as_clause":
            c0 = ch.children[0]
            if c0.type == "scoped_identifier":
                out.append(c0.text.decode("utf-8", errors="replace"))
            elif c0.type == "identifier":
                out.append(c0.text.decode("utf-8", errors="replace"))


def extract_rust_module_dependencies(source: str) -> List[str]:
    """
    Parse Rust source and return dependency strings from:
    - use declarations (including groups, aliases, wildcards)
    - extern crate name
    - file-module declarations: mod name;  -> ./name (for path-style resolution in the parser)
    """
    parser = _get_parser()
    tree = parser.parse(source.encode("utf-8", errors="replace"))
    root = tree.root_node
    out: List[str] = []

    def visit(node):
        if node.type == "use_declaration":
            _add_from_use_declaration(node, out)
        elif node.type == "extern_crate_declaration":
            for i in range(node.child_count):
                ch = node.children[i]
                if ch.type == "identifier":
                    out.append(ch.text.decode("utf-8", errors="replace"))
                    break
        elif node.type == "mod_item":
            # mod foo;  (file-linked submodule), not mod foo { ... }
            if (
                node.child_count == 3
                and node.children[0].type == "mod"
                and node.children[1].type == "identifier"
                and node.children[2].type == ";"
            ):
                name = node.children[1].text.decode("utf-8", errors="replace")
                out.append(f"./{name}")

        for i in range(node.child_count):
            visit(node.children[i])

    visit(root)
    return out
