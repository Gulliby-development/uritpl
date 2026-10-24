<p align="center"><img src="docs/logo.svg" width="96" alt="" /></p>

# uritpl

[![CI](https://github.com/Gulliby-development/uritpl/actions/workflows/ci.yml/badge.svg)](https://github.com/Gulliby-development/uritpl/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**uritpl** is an offline command-line toolkit for people who write API clients, OpenAPI
documents, or link headers using URI templates such as `{id}`, `{/path*}`, and
`{?q,page}`. It expands, inspects, and checks URI templates using RFC 6570 level 4
expansion rules.

The tool uses only the Python standard library. It reads the files named on the command
line (or standard input when you use `-`), makes no network requests, and starts no
other programs.

## Install

Use Python 3.11 or newer and a local checkout of this repository. From the repository
root, run the package directly with `python -m uritpl`; no `pip install`, extra
dependency, console-script installation, or network access is required. For example:

```text
python --version
python -m uritpl --help
```

The interpreter selected by `python` must be Python 3.11 or newer.

## Usage

The examples below run from the repository root. `v.json` is a UTF-8 JSON object:

```json
{"id": "42", "q": "a b"}
```

Save that one-line content as `v.json` for the `expand` and `trace` examples.

Expand a template using values from the JSON file:

```text
$ python -m uritpl expand "/users{/id}{?q}" v.json
/users/42?q=a%20b
```

The expansion is written as-is, without an added final LF.

Trace each expression's contribution:

```text
$ python -m uritpl trace "/users{/id}{?q,page}" v.json
N  EXPRESSION   RESULT
1  "{/id}"      "/42"
2  "{?q,page}"  "?q=a%20b"
```

Explain the operator and variable specifications in a template.

No files are needed for this example:

```text
$ python -m uritpl explain "{a}{/b:2}"
N  COL  OP  FORM    NAME  MODIFIER
1  1    -   simple  a     -
2  4    /   path    b     prefix 2
```

List distinct variable names in first-appearance order. No files are needed:

```text
$ python -m uritpl names "{a}{b}{a}"
a
b
```

Percent-encode text, preserving reserved characters with `--reserved`. No files are
needed:

```text
$ python -m uritpl encode --reserved "a/b?c#d"
a/b?c#d
```

Check a UTF-8 template file. For this example, save the following one-line content as
`t.txt` with a final LF:

```text
/users{/id}{?q}
```

```text
$ python -m uritpl check t.txt
1 template checked, 0 problems
```

`expand` and `encode` do not add a final LF to their output. The other examples
produce line-oriented output ending in LF.

## Commands

The help command prints these six usage lines, in this order:

```text
usage: uritpl expand [--strict] TEMPLATE VARS
usage: uritpl trace [--strict] TEMPLATE VARS
usage: uritpl explain TEMPLATE
usage: uritpl names TEMPLATE
usage: uritpl encode [--reserved] TEXT
usage: uritpl check FILE...
```

- `expand` substitutes values from a JSON variables file into a template. `--strict`
  makes the first undefined variable an error.
- `trace` reports each expression and its expansion; `--strict` has the same meaning
  as for `expand`.
- `explain` lists each expression's operator, form, and variable specifications.
- `names` lists distinct variable names in first-appearance order.
- `encode` percent-encodes the supplied text. `--reserved` preserves URI reserved
  characters and valid percent triplets.
- `check` reads each named file and checks its non-empty lines as templates. It uses
  LF to separate lines, removes a CR only when immediately before LF, and treats a
  lone CR as line content. A file can be named as `-` to read standard input.

For `expand` and `trace`, `VARS` is a UTF-8 JSON file containing one object. Values
may be strings, lists of strings, objects whose values are strings, or `null`.
Missing values, `null`, empty lists, and empty objects are undefined; the empty string
is defined. A BOM at the beginning of the JSON file is accepted. Template, JSON, and
check-file input must be valid UTF-8.

Successful commands return status 0. `explain` and `names` return status 1 when a
template has no variables, and `check` returns status 1 when it finds problems.
Errors return status 2, write one diagnostic line to standard error, and leave standard
output empty. A `check` read or decoding error produces no partial report.

## Development

Run the project's checks from the repository root with Python 3.11 or newer and the
development tools available:

```text
ruff check .
ruff format --check .
pytest
```

## License

MIT, see [LICENSE](LICENSE).

---

Built with BAKED.
