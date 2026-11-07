# EASIFEM cookbook

Knowledge base for developing and using EASIFEM: recipes, theory notes and
a generated API index. See `INDEX.md` for the list of entries.

## API index

`scripts/gen_api_index.py` builds a compact index of a library checkout, so
that you can find a class, binding or procedure without reading the full
source. It needs Python 3 and uses only the standard library.

Run it from the root of this repository, with the library repositories
checked out next to it:

```sh
# Index all of classes
python3 scripts/gen_api_index.py --repo ../classes

# Index one module
python3 scripts/gen_api_index.py --repo ../classes --module FEDOF
```

| Option | Meaning |
|---|---|
| `--repo PATH` | Library checkout (required). Its last path component names the output directory. |
| `--out DIR` | Output root (default `api-index`). |
| `--module NAME` | Index only `src/modules/NAME`. The name is case-sensitive. |

### Output

The script writes to `api-index/<repo>/`:

| File | Content |
|---|---|
| `<Module>.md` | Files and types, then a table Binding, Specific, Summary, Arguments for each type. Interfaces with no binding are listed under "Module procedures". |
| `INDEX.md` | One line per module: types, number of bindings, summary. |
| `COVERAGE.md` | Counts at the top, then gaps by module: bindings without a `!!` comment, interfaces without `summary:` or Examples, and bindings with no interface found. |

With `--module`, only `<Module>.md` is written, so `INDEX.md` and
`COVERAGE.md` from an earlier full run stay as they were.

`api-index/` is git-ignored and reflects the current checkout. Do not edit
it by hand. Regenerate it after changing branches or source files.

### Reading the tables

- Summary comes from the `summary:` of the interface docblock, or from the
  `!!` comment of the binding if there is none.
- A row for a generic lists its specific procedures and has no arguments;
  look at the row of each specific procedure.
- Arguments are dummy-argument names only, without types.
- Inherited bindings are not repeated. The type list shows `extends`, so
  look in the parent type.

### Limits

- Only `src/modules/<Module>/src/*.F90` is read, not subdirectories of
  `src/`.
- `#include` files and macros are not expanded, so procedures declared
  that way appear under "Bindings with no interface found".
- Both branches of an `#ifdef` are read. The first definition of a name is
  kept.
- An Examples section is a heading such as `! Examples` or `!## Example 1`.
  `!### Usage` does not count.
- A file that cannot be parsed is skipped with a warning on stderr.

The index is a hint. Check the source before relying on a detail.
