#!/usr/bin/env python3
"""Generate a compact API index for an EASIFEM library checkout.

Usage:
    gen_api_index.py --repo ../classes [--out api-index] [--module FEDOF]

Reads src/modules/<M>/src/*.F90 and writes, under <out>/<repo>/:

    <M>.md       types, then Binding | Specific | Summary | Arguments
    INDEX.md     one line per module
    COVERAGE.md  documentation gaps, grouped by module

With --module only <M>.md is written, so that INDEX.md and COVERAGE.md
of an earlier full run are not replaced by a one-module view.

Known limits: files in subdirectories of src/ are not read, and code that
comes from #include files or macro expansion is not seen. Both branches of
an #ifdef are read; the first definition of a name wins.
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

FLAGS = re.IGNORECASE

RE_MODULE = re.compile(r"^MODULE\s+(\w+)$", FLAGS)
RE_END_MODULE = re.compile(r"^END\s*(?:SUB)?MODULE\b", FLAGS)
RE_CONTAINS = re.compile(r"^CONTAINS$", FLAGS)
RE_TYPE_ATTR = re.compile(r"^TYPE\s*(,.*?)?::\s*(\w+)", FLAGS)
RE_TYPE_OLD = re.compile(r"^TYPE\s+(?!IS\b)(\w+)$", FLAGS)
RE_END_TYPE = re.compile(r"^END\s*TYPE\b", FLAGS)
RE_EXTENDS = re.compile(r"EXTENDS\s*\(\s*(\w+)\s*\)", FLAGS)
RE_ABSTRACT = re.compile(r"\bABSTRACT\b", FLAGS)
RE_IFACE = re.compile(r"^(ABSTRACT\s+)?INTERFACE\b\s*(.*)$", FLAGS)
RE_END_IFACE = re.compile(r"^END\s*INTERFACE\b", FLAGS)
RE_END_PROC = re.compile(
    r"^END(?:\s*(?:SUBROUTINE|FUNCTION|PROCEDURE)\b.*)?$", FLAGS
)
RE_HEAD = re.compile(
    r"^(?:(?:MODULE|PURE|IMPURE|ELEMENTAL|RECURSIVE|NON_RECURSIVE"
    r"|INTEGER|REAL|LOGICAL|CHARACTER|COMPLEX|DOUBLE\s+PRECISION"
    r"|TYPE|CLASS)(?:\s*\(.*?\))?\s+)*"
    r"(?:SUBROUTINE|FUNCTION)\s+(\w+)\s*(?:\((.*?)\))?",
    FLAGS,
)
RE_IFACE_PROC = re.compile(
    r"^(?:MODULE\s+)?PROCEDURE\s*(?:::)?\s*(.+)$", FLAGS
)
RE_BIND_PROC = re.compile(
    r"^PROCEDURE\s*(?:\(\s*(\w+)\s*\))?\s*(?:,[^:]*)?(?:::)?\s*(.+)$", FLAGS
)
RE_BIND_GENERIC = re.compile(
    r"^GENERIC\s*(?:,[^:]*)?::\s*(.+?)\s*=>\s*(.+)$", FLAGS
)

RE_SUMMARY = re.compile(r"^!+>?\s*summary\s*:\s*(.*)$", FLAGS)
RE_EXAMPLES = re.compile(r"^!+\s*#*\s*examples?\s*\d*\s*:?\s*$", FLAGS)
RE_DOC_KEY = re.compile(r"^[A-Za-z_]+:(\s|$)")
RE_COMMENT_MARK = re.compile(r"^!+>?\s?")
DOC_STOPS = ("---", "...", "===", "#", "@")


class ParseError(Exception):
    """A file whose structure could not be followed."""


@dataclass
class Proc:
    """One procedure interface, or a procedure in a CONTAINS section."""

    name: str
    args: list
    summary: str
    has_examples: bool
    abstract: bool = False
    iface_name: str = ""


@dataclass
class Binding:
    """One PROCEDURE or GENERIC line of a type."""

    name: str
    specifics: list
    generic: bool
    comment: str = ""


@dataclass
class FType:
    """One derived type."""

    name: str
    summary: str
    extends: str
    abstract: bool
    file: str
    bindings: list = field(default_factory=list)


@dataclass
class ParsedFile:
    """Everything read from one source file."""

    path: str
    modules: list = field(default_factory=list)
    summary: str = ""
    types: list = field(default_factory=list)
    procs: list = field(default_factory=list)
    contained: list = field(default_factory=list)
    aliases: list = field(default_factory=list)


@dataclass
class Module:
    """All files of src/modules/<name>/src."""

    name: str
    files: list

    def __post_init__(self):
        # Files of one directory can reuse a name, such as obj_Initialize,
        # so lookups keep one table per file.
        self.procs = {}
        self.contained = {}
        for parsed in self.files:
            procs = self.procs.setdefault(parsed.path, {})
            for proc in parsed.procs:
                procs.setdefault(proc.name.lower(), proc)
            contained = self.contained.setdefault(parsed.path, {})
            for proc in parsed.contained:
                contained.setdefault(proc.name.lower(), proc)

    @property
    def types(self):
        return [t for parsed in self.files for t in parsed.types]

    @property
    def summary(self):
        preferred = [
            p for p in self.files if Path(p.path).stem.lower().startswith(
                self.name.lower())
        ]
        for parsed in preferred + self.files:
            if parsed.summary:
                return parsed.summary
        for ftype in self.types:
            if ftype.summary:
                return ftype.summary
        return ""

    @property
    def interfaces(self):
        return [p for procs in self.procs.values() for p in procs.values()]

    def find(self, name, path):
        """Join by specific procedure name: same file first, then the
        other files of the module; interfaces before CONTAINS procedures.
        """
        key = name.lower()
        tables = (
            [self.procs[path], self.contained[path]]
            + [table for table in self.procs.values()]
            + [table for table in self.contained.values()]
        )
        for table in tables:
            if key in table:
                return table[key]
        return None


def split_code(text):
    """Split at ! and ; outside strings: return (statements, comment)."""
    statements = []
    start = 0
    quote = ""
    for pos, char in enumerate(text):
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == ";":
            statements.append(text[start:pos])
            start = pos + 1
        elif char == "!":
            statements.append(text[start:pos])
            return statements, text[pos:].strip()
    statements.append(text[start:])
    return statements, ""


def split_items(text):
    """Split a comma list, ignoring commas inside parentheses."""
    items = []
    depth = 0
    current = ""
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            items.append(current.strip())
            current = ""
        else:
            current += char
    items.append(current.strip())
    return [item for item in items if item]


def logical_lines(lines):
    """Yield (kind, text, comment); kind is blank, comment or code.

    Continuation lines are joined. Preprocessor lines are dropped, with
    their backslash continuations, and so are comments inside a statement.
    """
    buffer = ""
    continuing = False
    in_directive = False
    for raw in lines:
        stripped = raw.strip()
        if in_directive:
            in_directive = stripped.endswith("\\")
            continue
        if stripped.startswith("#"):
            in_directive = stripped.endswith("\\")
            continue
        if not stripped:
            if not continuing:
                yield "blank", "", ""
            continue
        if stripped.startswith("!"):
            if not continuing:
                yield "comment", stripped, ""
            continue
        parts, comment = split_code(stripped)
        for index, part in enumerate(parts):
            code = part.strip()
            if code.startswith("&"):
                code = code[1:].lstrip()
                buffer = buffer.rstrip()
            if index == len(parts) - 1 and code.endswith("&"):
                buffer += code[:-1].rstrip() + " "
                continuing = True
                continue
            buffer += code
            continuing = False
            if buffer.strip():
                yield "code", buffer.strip(), comment
            buffer = ""
    if buffer.strip():
        yield "code", buffer.strip(), ""


def doc_summary(doc):
    """Return the summary: text of a docblock, with continuation lines."""
    for index, line in enumerate(doc):
        match = RE_SUMMARY.match(line)
        if not match:
            continue
        parts = [match.group(1).strip()]
        for following in doc[index + 1:]:
            body = RE_COMMENT_MARK.sub("", following).strip()
            if (
                not body
                or following.startswith("!>")
                or body.startswith(DOC_STOPS)
                or RE_DOC_KEY.match(body)
            ):
                break
            parts.append(body)
        return " ".join(part for part in parts if part)
    return ""


def doc_has_examples(doc):
    return any(RE_EXAMPLES.match(line) for line in doc)


def binding_note(comment):
    """Return the text of a !! comment if it describes a binding.

    Bare !! lines, !! @Section markers and !!, Foo (commented-out code)
    are not descriptions.
    """
    note = comment.lstrip("!").strip()
    return note if re.match(r"[\w`]", note) else ""


def make_proc(match, doc, abstract=False, iface_name=""):
    args = [a for a in split_items(match.group(2) or "") if a != "*"]
    return Proc(
        name=match.group(1),
        args=args,
        summary=doc_summary(doc),
        has_examples=doc_has_examples(doc),
        abstract=abstract,
        iface_name=iface_name,
    )


def parse_procedure_binding(match):
    """Return Binding objects for one PROCEDURE statement."""
    interface, names = match.group(1), match.group(2)
    bindings = []
    for item in split_items(names):
        name, _, target = item.partition("=>")
        name = name.strip()
        target = interface or target.strip() or name
        bindings.append(Binding(name, [target], False))
    return bindings


class Parser:
    """Line-driven parser for the specification part of a module."""

    def __init__(self, path):
        self.result = ParsedFile(path)
        self.scope = "module"
        self.doc = []
        self.ftype = None
        self.type_contains = False
        self.last_bindings = []
        self.iface = None
        self.iface_doc = []
        self.iface_abstract = False
        self.in_proc = False
        self.nest = 0
        self.depth = 0

    def parse(self, lines):
        for kind, text, comment in logical_lines(lines):
            if kind == "blank":
                self.last_bindings = []
                if self.doc:
                    self.doc.append("")
            elif kind == "comment":
                self.on_comment(text)
            else:
                self.on_code(text, comment)
        if self.scope in ("type", "interface"):
            raise ParseError(f"unterminated {self.scope} block")
        return self.result

    def on_comment(self, text):
        if self.last_bindings:
            if text.startswith("!!"):
                for binding in self.last_bindings:
                    binding.comment = binding_note(text)
            self.last_bindings = []
        if text.startswith("!>"):
            self.doc = []
        self.doc.append(text)

    def on_code(self, text, comment):
        self.last_bindings = []
        if self.scope == "type":
            self.on_type(text, comment)
        elif self.scope == "interface":
            self.on_interface(text)
        elif self.scope == "contained":
            self.on_contained(text)
        else:
            self.on_module(text)
        self.doc = []

    def on_module(self, text):
        match = RE_MODULE.match(text)
        if match:
            self.result.modules.append(match.group(1))
            self.result.summary = self.result.summary or doc_summary(self.doc)
            return
        if RE_CONTAINS.match(text):
            self.scope = "contained"
            self.depth = 0
            return
        match = RE_IFACE.match(text)
        if match:
            self.scope = "interface"
            self.iface = "".join(match.group(2).split())
            self.iface_doc = self.doc
            self.iface_abstract = bool(match.group(1))
            self.in_proc = False
            self.nest = 0
            return
        match = RE_TYPE_ATTR.match(text)
        if match:
            self.open_type(match.group(2), match.group(1) or "")
            return
        match = RE_TYPE_OLD.match(text)
        if match:
            self.open_type(match.group(1), "")

    def open_type(self, name, attrs):
        extends = RE_EXTENDS.search(attrs)
        self.ftype = FType(
            name=name,
            summary=doc_summary(self.doc),
            extends=extends.group(1) if extends else "",
            abstract=bool(RE_ABSTRACT.search(attrs)),
            file=self.result.path,
        )
        self.result.types.append(self.ftype)
        self.scope = "type"
        self.type_contains = False

    def on_type(self, text, comment):
        if RE_END_TYPE.match(text):
            self.scope = "module"
            return
        if RE_CONTAINS.match(text):
            self.type_contains = True
            return
        if not self.type_contains:
            return
        bindings = []
        match = RE_BIND_GENERIC.match(text)
        if match:
            name = "".join(match.group(1).split())
            bindings = [Binding(name, split_items(match.group(2)), True)]
        else:
            match = RE_BIND_PROC.match(text)
            if match:
                bindings = parse_procedure_binding(match)
        known = {b.name.lower(): b for b in self.ftype.bindings}
        fresh = []
        touched = []
        for binding in bindings:
            first = known.get(binding.name.lower())
            if first is None:
                binding.comment = binding_note(comment)
                fresh.append(binding)
                touched.append(binding)
            elif first.generic:  # a generic can span several statements
                touched.append(first)
                first.specifics.extend(
                    name for name in binding.specifics
                    if name not in first.specifics
                )
        self.ftype.bindings.extend(fresh)
        self.last_bindings = [b for b in touched if not b.comment]

    def on_interface(self, text):
        if self.in_proc and RE_IFACE.match(text):
            self.nest += 1
            return
        if RE_END_IFACE.match(text):
            if self.nest:
                self.nest -= 1
            else:
                self.scope = "module"
                self.in_proc = False
            return
        if self.nest:
            return
        if RE_END_PROC.match(text):
            self.in_proc = False
            return
        if not self.in_proc:
            match = RE_IFACE_PROC.match(text)
            if match:
                for name in split_items(match.group(1)):
                    self.result.aliases.append((self.iface, name))
                return
        match = RE_HEAD.match(text)
        if match:
            doc = self.doc if doc_summary(self.doc) else self.iface_doc
            self.result.procs.append(
                make_proc(match, doc, self.iface_abstract, self.iface)
            )
            self.in_proc = True

    def on_contained(self, text):
        if RE_END_MODULE.match(text) and self.depth <= 1:
            self.scope = "module"
            return
        if RE_END_PROC.match(text):
            self.depth = max(self.depth - 1, 0)
            return
        match = RE_HEAD.match(text)
        if match:
            if self.depth == 0:
                self.result.contained.append(make_proc(match, self.doc))
            self.depth += 1


def clean(text):
    """Make a string safe for one table cell."""
    return " ".join(text.split()).replace("|", "\\|")


def resolve_specifics(binding, ftype):
    """Follow a generic through the sibling bindings of its type."""
    if not binding.generic:
        return binding.specifics
    by_name = {b.name.lower(): b for b in ftype.bindings if not b.generic}
    resolved = []
    for name in binding.specifics:
        sibling = by_name.get(name.lower())
        resolved.extend(sibling.specifics if sibling else [name])
    return resolved


def binding_row(binding, ftype, module):
    specifics = resolve_specifics(binding, ftype)
    procs = [module.find(name, ftype.file) for name in specifics]
    if binding.generic:
        found = next((p.summary for p in procs if p and p.summary), "")
        summary = binding.comment or found
        args = ""
    else:
        proc = procs[0]
        summary = (proc.summary if proc else "") or binding.comment
        args = ", ".join(proc.args) if proc else ""
    return (binding.name, ", ".join(specifics), summary, args)


def module_rows(module):
    """Rows for interfaces and aliases that no type binding refers to."""
    listed = set()
    for ftype in module.types:
        for binding in ftype.bindings:
            if not binding.generic:
                proc = module.find(binding.specifics[0], ftype.file)
                listed.add(id(proc))
    rows = []
    for parsed in module.files:
        for iface, name in parsed.aliases:
            proc = module.find(name, parsed.path)
            listed.add(id(proc))
            rows.append((
                iface or "-",
                name,
                proc.summary if proc else "",
                ", ".join(proc.args) if proc else "",
            ))
    for proc in module.interfaces:
        if id(proc) in listed:
            continue
        label = proc.iface_name or ("(abstract)" if proc.abstract else "-")
        rows.append((label, proc.name, proc.summary, ", ".join(proc.args)))
    return rows


def table(rows):
    lines = [
        "| Binding | Specific | Summary | Arguments |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(clean(cell) for cell in row) + " |")
    return lines


def render_module(module):
    lines = [f"# {module.name}", ""]
    names = [name for parsed in module.files for name in parsed.modules]
    if names:
        lines.append("Modules: " + ", ".join(names))
    paths = [parsed.path for parsed in module.files]
    lines.append(("File: " if len(paths) == 1 else "Files: ")
                 + ", ".join(paths))
    if module.summary:
        lines.append(f"Summary: {clean(module.summary)}")
    lines.append("")
    if module.types:
        lines.append("Types:")
        for ftype in module.types:
            tags = []
            if ftype.abstract:
                tags.append("abstract")
            if ftype.extends:
                tags.append(f"extends {ftype.extends}")
            tag = f" ({', '.join(tags)})" if tags else ""
            lines.append(f"- {ftype.name}{tag}: {clean(ftype.summary)}")
        lines.append("")
    for ftype in module.types:
        if ftype.bindings:
            lines.append(f"## {ftype.name}")
            lines.append("")
            lines.extend(table(
                binding_row(b, ftype, module) for b in ftype.bindings
            ))
            lines.append("")
    rows = module_rows(module)
    if rows:
        lines.append("## Module procedures")
        lines.append("")
        lines.extend(table(rows))
        lines.append("")
    return "\n".join(lines)


def render_index(repo, modules):
    lines = [
        f"# API index: {repo}",
        "",
        "| Module | Types | Bindings | Summary |",
        "|---|---|---|---|",
    ]
    for module in modules:
        types = ", ".join(t.name for t in module.types)
        count = sum(len(t.bindings) for t in module.types)
        lines.append(
            f"| {module.name} | {types} | {count} "
            f"| {clean(module.summary)} |"
        )
    return "\n".join(lines) + "\n"


def module_gaps(module):
    """Return documentation gaps of one module, by gap name."""
    gaps = {
        "no_comment": [],
        "no_summary": [],
        "no_examples": [],
        "no_interface": [],
    }
    for ftype in module.types:
        for binding in ftype.bindings:
            label = f"{ftype.name}%{binding.name}"
            if not binding.comment:
                gaps["no_comment"].append(label)
            if binding.generic:
                continue
            if not module.find(binding.specifics[0], ftype.file):
                gaps["no_interface"].append(label)
    for proc in module.interfaces:
        if not proc.summary:
            gaps["no_summary"].append(proc.name)
        if not proc.has_examples:
            gaps["no_examples"].append(proc.name)
    return gaps


GAP_TITLES = (
    ("no_comment", "Bindings without !! comment"),
    ("no_summary", "Interfaces without summary:"),
    ("no_examples", "Interfaces without Examples"),
    ("no_interface", "Bindings with no interface found"),
)


def render_coverage(repo, modules):
    all_gaps = [(module, module_gaps(module)) for module in modules]
    bindings = sum(len(t.bindings) for m in modules for t in m.types)
    interfaces = sum(len(m.interfaces) for m in modules)
    totals = {"no_comment": bindings, "no_interface": bindings,
              "no_summary": interfaces, "no_examples": interfaces}
    lines = [f"# API coverage: {repo}", ""]
    lines.append(f"Modules: {len(modules)}, bindings: {bindings}, "
                 f"interfaces: {interfaces}")
    lines.append("")
    lines.extend(["| Gap | Count | Of |", "|---|---|---|"])
    for key, title in GAP_TITLES:
        count = sum(len(gaps[key]) for _, gaps in all_gaps)
        lines.append(f"| {title} | {count} | {totals[key]} |")
    lines.append("")
    for module, gaps in all_gaps:
        if not any(gaps.values()):
            continue
        lines.append(f"## {module.name}")
        lines.append("")
        for key, title in GAP_TITLES:
            if gaps[key]:
                names = ", ".join(gaps[key])
                lines.append(f"- {title} ({len(gaps[key])}): {names}")
        lines.append("")
    return "\n".join(lines)


def parse_file(path, repo):
    relative = path.relative_to(repo).as_posix()
    with open(path, encoding="utf-8", errors="replace") as stream:
        return Parser(relative).parse(stream.read().splitlines())


def load_module(source_dir, repo):
    files = []
    for path in sorted(source_dir.glob("*.F90")):
        try:
            files.append(parse_file(path, repo))
        except Exception as error:  # a bad file must not stop the run
            relative = path.relative_to(repo)
            print(f"warning: skipped {relative}: {error}", file=sys.stderr)
    return Module(source_dir.parent.name, files)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a compact API index for an EASIFEM library."
    )
    parser.add_argument("--repo", required=True, help="library checkout")
    parser.add_argument("--out", default="api-index", help="output root")
    parser.add_argument("--module", help="index only this module")
    options = parser.parse_args()

    repo = Path(options.repo).resolve()
    root = repo / "src" / "modules"
    if not root.is_dir():
        parser.error(f"no src/modules in {options.repo}")
    if options.module:
        dirs = [root / options.module / "src"]
        if not dirs[0].is_dir():
            parser.error(f"no module {options.module}")
    else:
        dirs = sorted(path for path in root.glob("*/src") if path.is_dir())
        dirs = [path for path in dirs if any(path.glob("*.F90"))]

    modules = [load_module(path, repo) for path in dirs]
    out = Path(options.out) / repo.name
    out.mkdir(parents=True, exist_ok=True)
    for module in modules:
        (out / f"{module.name}.md").write_text(
            render_module(module), encoding="utf-8"
        )
    if not options.module:
        (out / "INDEX.md").write_text(
            render_index(repo.name, modules), encoding="utf-8"
        )
        (out / "COVERAGE.md").write_text(
            render_coverage(repo.name, modules), encoding="utf-8"
        )
    print(f"wrote {len(modules)} module(s) to {out}")


if __name__ == "__main__":
    main()
