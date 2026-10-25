# QuickINI

A simple and fast INI file parser for Python with support for loading from URLs and automatic type conversion.

## Installation

```bash
pip install quick_ini
```

## Quick Start

```python
from quick_ini import QuickIni

# Load from file
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

## File Format

```ini
# Comments start with # or ;
debug = yes          ; inline comments need a space before them
port = 8080
timeout = 2.5e1
color = #fff         # a # with no space before it is part of the value

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
- Sections, plus `#`, `;` and inline comments
- Lists using `|` lines
- Write values back to files safely, the file is never left half written
- Error handling with detailed messages
- Static class design for easy use across modules
