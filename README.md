# journal-verifier

Validate a journal markdown file that follows a fixed daily template. The tool checks:

- missing or out-of-order sections
- missing dates (full year by default)
- weekday name mismatches
- available sections per day (CSV output when requested)

## Usage

Run with uv (report goes to stderr by default; CSV is disabled unless requested):

```bash
uv run journal-verifier path/to/journal.md
```

CLI options:

- `path` (positional): path to the journal markdown file
- `--csv`: CSV output path (default: no CSV output; use `-` for stdout)
- `--report`: report output path (default: stderr; use `-` for stdout)
- `--start`: start date (YYYY-MM-DD)
- `--end`: end date (YYYY-MM-DD)
- `--year`: shortcut for `--start`/`--end` for a full year (e.g. 2026)
- `--missing-limit`: max missing dates to list per range (0 = all)
- `--debug-weekday`: include weekday debug details for invalid headers
- `--fix`: apply autofixes for supported problems
- `--fix-dry-run`: show autofix summary without writing changes

Write CSV and report to files:

```bash
uv run journal-verifier path/to/journal.md --csv sections.csv --report report.txt
```

Limit the date range check:

```bash
uv run journal-verifier path/to/journal.md --start 2026-01-01 --end 2026-12-31
```

Shortcut for a full year:

```bash
uv run journal-verifier path/to/journal.md --year 2026
```

Autofix missing sections (preserves order):

```bash
uv run journal-verifier path/to/journal.md --fix
```

Autofix missing days too (same flag):

```bash
uv run journal-verifier path/to/journal.md --fix --year 2026
```

Preview autofix summary without writing:

```bash
uv run journal-verifier path/to/journal.md --fix-dry-run
```

Show all missing dates (no limit):

```bash
uv run journal-verifier path/to/journal.md --missing-limit 0
```

Debug weekday parsing (shows raw characters and codepoints):

```bash
uv run journal-verifier path/to/journal.md --debug-weekday
```

## CSV columns

- `date`
- `weekday_header`
- `weekday_actual`
- `weekday_matches`
- `sections_present`
- `sections_missing`

## Notes

- The default missing-date check expects a full calendar year for each year present in the file.
- Use `--start`/`--end` if you want to validate a partial range instead.
