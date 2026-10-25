import os
from quick_ini import QuickIni

HERE = os.path.dirname(os.path.abspath(__file__))
QuickIni.load_file(os.path.join(HERE, "config.ini"))

# Two ways to read a key inside a section
host = QuickIni.get_value("host", section="database")
port = QuickIni.get_value("database.port")
print(f"Database: {host}:{port}")

# Everything in one section, with the section name removed
cache = QuickIni.get_all("cache")
print("Cache settings:", cache)          # {'enabled': True, 'size': 256}

# Everything, keys in a section are given as "section.key"
for key, value in QuickIni.get_all().items():
    print(f"  {key} = {value!r}")
