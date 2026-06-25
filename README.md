# Duplicate File Finder

A small utility for scanning a directory tree and identifying duplicate files by content.

## Project layout

- `src/` - source package (cli, detector, scanner, deleter, formatter)
- `test/` - unit tests
- `pyproject.toml` - pytest configuration for `src` and `test`

## Requirements

- Python 3.11+ (or a compatible Python 3 version)

## Install

No install is required for this repository. Use the repository root as the working directory.

## Usage

Run the CLI via the package:

```bash
python -m src /path/to/directory
```

Options:

- `--format text|json` - choose output format
- `--min-size N` - only consider files at least `N` bytes
- `--delete` - delete duplicate files and keep the first copy
- `--dry-run` - show deletion actions without modifying files

Example:

```bash
python -m src /tmp/data --format json
```

## Testing

Run the test suite from the repository root:

```bash
python -m pytest -q
```

## Notes

- Source files live in `src/`
- Tests live in `test/`
- `pyproject.toml` configures pytest to add `src` to `PYTHONPATH`

## License

This project is licensed under the [MIT License](LICENSE).
