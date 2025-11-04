# QuickINI

A simple and fast INI file parser for Python with support for loading from URLs and automatic type conversion.

## Installation

```bash
pip install quickini
```

## Quick Start

```python
from quickini import QuickIni

# Load from file
QuickIni.load_file("config.ini")

# Load from URL
QuickIni.load_file("https://example.com/config.ini")

# Get values with automatic type conversion
debug = QuickIni.get_value("debug", False)  # Returns boolean
port = QuickIni.get_value("port", 8080)     # Returns integer

# Write values back to file
QuickIni.write_value("new_setting", "value", add_if_not_found=True)
```

## Features

- Load INI files from local filesystem or URLs
- Automatic type conversion (int, float, bool, str)
- Write values back to files
- Error handling with detailed messages
- Static class design for easy use across modules
