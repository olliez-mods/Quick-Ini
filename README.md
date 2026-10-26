# QuickINI

A simple and fast INI file parser for Python with support for loading from URLs and automatic type conversion.

## Installation

```bash
pip install quick_ini
```

## Quick Start

```python
from quick_ini import QuickIni

# Load from file, before any get_value() or get_all() (those raise RuntimeError otherwise)
QuickIni.load_file("config.ini")

# Load from URL
QuickIni.load_file("https://example.com/config.ini")

# Get values with automatic type conversion
debug = QuickIni.get_value("debug", False)  # Returns boolean
port = QuickIni.get_value("port", 8080)     # Returns integer

# Values inside a [section]
db_port = QuickIni.get_value("port", section="database")  # or get_value("database.port")

# Get everything, or everything in one section
settings = QuickIni.get_all()
database = QuickIni.get_all("database")

# Write values back to file
QuickIni.write_value("new_setting", "value", add_if_not_found=True)
QuickIni.write_value("port", 5433, section="database")
```

## Keeping config.ini up to date with a template

Projects often ship a `config.ini.template` that you copy to `config.ini`. When the template gets new settings later, QuickINI can update `config.ini` for you:

```python
QuickIni.load_file("config.ini", template=True)            # uses config.ini.template
QuickIni.load_file("config.ini", template="defaults.ini")  # uses defaults.ini
```

- If `config.ini` doesn't exist, it is created from the template
- The template decides which settings exist, their order, sections and comments. Your values are kept exactly as you wrote them
- New settings from the template are added with their default values
- Settings that are no longer in the template are kept at the end of their section, under a comment
- The file is only rewritten when something changed, and the previous version is saved as `config.ini.bak`
- With `template=True` a missing template is skipped, so deployed copies without one still load. A template given by name must exist

```python
report = QuickIni.get_sync_report()
if report and report["added"]:
    print("New settings added to config.ini:", ", ".join(report["added"]))
```

The report also has `created`, `changed`, `orphaned` (settings kept that aren't in the template), `backup` and `text` (the synced file). Use `QuickIni.sync_template("config.ini")` to sync without loading, and `dry_run=True` to work out the changes without writing anything.

### From the command line

Installing QuickINI adds a `quick-ini` command (or run `python -m quick_ini`), so you can sync without starting your program:

```bash
quick-ini sync                     # config.ini with config.ini.template
quick-ini sync --dry-run           # show what would change as a diff, write nothing (--diff works too)
quick-ini sync --config app.ini --template defaults.ini
```

`--config` defaults to `config.ini` and `--template` to `<config>.template`. Unlike `template=True`, a missing template is an error here. It prints the settings added and kept, and exits with 1 on any error.

## File Format

```ini
# Comments start with #
debug = yes          # comments can also go after a value
port = 8080
timeout = 2.5e1
color = \#fff        # use \# to put a # in a value

# Lists
parts =
|one
|two

[database]
host = localhost
port = 5432
```

## Features

- Load INI files from local filesystem or URLs
- Automatic type conversion: int, float (including `-1.5` and `1e5`), bool (`true`/`false`, `yes`/`no`, `on`/`off`) and str
- Sections, plus `#` comments, including after a value (escape `#` as `\#` in values)
- Lists using `|` lines
- Keep `config.ini` up to date with a template file
- Write values back to files safely, the file is never left half written
- Error handling with detailed messages
- Static class design for easy use across modules

## Examples

Runnable examples are in the [examples](examples) folder:

- [basic](examples/basic/basic.py): loading a file, defaults, types and lists
- [sections](examples/sections/sections.py): reading keys in `[sections]` and `get_all()`
- [writing](examples/writing/writing.py): changing and adding values
- [template_sync](examples/template_sync/template_sync.py): creating and updating `config.ini` from `config.ini.template`

Run one with `python examples/basic/basic.py` after installing QuickINI.
