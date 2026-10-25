import os
from quick_ini import QuickIni

HERE = os.path.dirname(os.path.abspath(__file__))

if(not QuickIni.load_file(os.path.join(HERE, "config.ini"))):
    print("Could not load config:", QuickIni.get_last_error())
    raise SystemExit(1)

debug = QuickIni.get_value("debug", False)          # True, "yes" counts as a bool
port = QuickIni.get_value("port", 80, int)          # 8080, raises if it isn't an int
timeout = QuickIni.get_value("timeout", 10.0)       # 2.5
name = QuickIni.get_value("name")                   # "My App"
color = QuickIni.get_value("color")                 # "#ff8800"
admins = QuickIni.get_value("admins", [])           # ["alice", "bob"]
retries = QuickIni.get_value("retries", 3)          # 3, not in the file so the default is used

print(f"{name} on port {port} (debug={debug}, timeout={timeout}s, retries={retries})")
print(f"Color: {color}")
print(f"Admins: {', '.join(admins)}")
