"""
Command line: quick-ini sync [--config config.ini] [--template <config>.template] [--dry-run | --diff]
\nAlso runs as "python -m quick_ini". Brings a config file up to date with its template, see QuickIni.sync_template().
"""
from .quick_ini import QuickIni
import argparse
import difflib
import sys

def sync(config:str, template:str | None, dry_run:bool) -> int:
    # Unlike load_file(template=True), a missing template is an error here: on the command line it's a typo
    template = template or f"{config}.template"
    try:
        with open(config, 'r', encoding='utf-8') as file:
            old_text = file.read()
    except FileNotFoundError:
        old_text = ""
    except IOError as e:
        print(f"Error reading file: '{e}'", file=sys.stderr)
        return 1

    if(not QuickIni.sync_template(config, template, dry_run=dry_run)):
        print(QuickIni.get_last_error(), file=sys.stderr)
        return 1
    report = QuickIni.get_sync_report()

    if(dry_run and report["changed"]):
        diff = difflib.unified_diff(old_text.splitlines(keepends=True), report["text"].splitlines(keepends=True),
                                    config, f"{config} (synced)")
        sys.stdout.writelines(diff)
        print()

    if(report["added"]):
        print("Added from template:", ", ".join(report["added"]))
    if(report["orphaned"]):
        print("Kept at the end (not in template):", ", ".join(report["orphaned"]))

    if(not report["changed"]):
        print("Already in sync")
    elif(dry_run):
        print(f"Would create {config} from {template}" if report["created"] else "Dry run: nothing written")
    elif(report["created"]):
        print(f"Created {config} from {template}")
    else:
        print(f"Synced {config} (previous version: {report['backup']})")
    return 0

def main(argv:list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quick-ini", description="Tools for .ini config files.")
    commands = parser.add_subparsers(dest="command")
    sync_parser = commands.add_parser("sync", help="bring a config file up to date with its template",
                                      description="Bring a config file up to date with its template. Your values are "
                                      "kept, new keys get the template's value, keys the template doesn't have are kept "
                                      "at the end of their section. The previous version is saved as <config>.bak.")
    sync_parser.add_argument("--config", default="config.ini", help="the config file (default: config.ini)")
    sync_parser.add_argument("--template", help="the template (default: <config>.template)")
    sync_parser.add_argument("--dry-run", "--diff", dest="dry_run", action="store_true",
                             help="show the changes as a diff, write nothing")

    args = parser.parse_args(argv)
    if(args.command == "sync"):
        return sync(args.config, args.template, args.dry_run)
    parser.print_help()
    return 1

if __name__ == "__main__":
    sys.exit(main())
