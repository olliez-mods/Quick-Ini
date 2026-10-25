import os
from quick_ini import QuickIni

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config.ini")

# template=True uses "config.ini.template" next to config.ini.
# The first run creates config.ini from it. Later runs keep your values and add any new
# settings from the template, so after editing either file just run this again.
# Pass a path instead, like template="defaults.ini", to use a differently named template.
if(not QuickIni.load_file(CONFIG, template=True)):
    print("Could not load config:", QuickIni.get_last_error())
    raise SystemExit(1)

report = QuickIni.get_sync_report()
if(report is None):
    print("No template found, loaded config.ini as is")
elif(report["created"]):
    print("Created config.ini from the template, edit it and run again")
elif(report["changed"]):
    if(report["added"]):
        print("New settings added to config.ini:", ", ".join(report["added"]))
    if(report["orphaned"]):
        print("Settings no longer in the template (kept):", ", ".join(report["orphaned"]))
    print("Previous config saved to", report["backup"])
else:
    print("config.ini is already up to date")

print(f"\nport={QuickIni.get_value('port')}, database timeout={QuickIni.get_value('timeout', section='database')}")
