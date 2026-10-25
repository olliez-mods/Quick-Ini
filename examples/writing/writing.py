import os
from quick_ini import QuickIni

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "settings.ini")

# Start from a fresh file each run
with open(PATH, "w", encoding="utf-8") as f:
    f.write("# Saved settings\nvolume = 50\n\n[window]\nwidth = 800\n")

QuickIni.load_file(PATH)

# Change existing values
QuickIni.write_value("volume", 75)
QuickIni.write_value("width", 1024, section="window")

# Add new ones, missing sections are created
QuickIni.write_value("muted", False, add_if_not_found=True)
QuickIni.write_value("height", 768, add_if_not_found=True, section="window")
QuickIni.write_value("recent", ["a.txt", "b.txt"], add_if_not_found=True, section="files")

# Writing a key that doesn't exist without add_if_not_found raises
try:
    QuickIni.write_value("typo", 1)
except ValueError:
    print("Error:", QuickIni.get_last_error())

print("volume is now", QuickIni.get_value("volume"))
print("\n--- settings.ini ---")
with open(PATH, encoding="utf-8") as f:
    print(f.read())
