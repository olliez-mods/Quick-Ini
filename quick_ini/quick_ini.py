from urllib.parse import urlparse
from typing import Any
import os
import re
import shutil
import tempfile

TRUE_WORDS = ("true", "yes", "on")
FALSE_WORDS = ("false", "no", "off")
INT_PATTERN = re.compile(r"[+-]?[0-9]+")
FLOAT_PATTERN = re.compile(r"[+-]?(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|[+-]?[0-9]+[eE][+-]?[0-9]+")

class QuickIni:
    parsed_ini: dict[str, str | int | bool | float | list | None] = {}
    loaded_file_path: str | None = None
    auto_type_convert_g: bool = True
    error_message: str = ""
    web_file: str | None = None
    sync_report: dict[str, Any] | None = None

    @staticmethod
    def grab_from_url(url:str, timeout:float = 10) -> bool:
        import urllib.request, urllib.error
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                if(response.status == 200):
                    QuickIni.web_file = response.read().decode('utf-8')
                    return True
                else:
                    QuickIni.error_message = f"Failed to download file from {url}, got response: {response.status}"
                    return False
        # URLError, HTTPError and timeouts are all OSErrors
        except (OSError, UnicodeDecodeError) as e:
            QuickIni.error_message = f"Could not get file from URL: '{e}'"
            return False

    @staticmethod
    def is_string_url(stri:str) -> bool:
        try:
            res = urlparse(stri)
            return all([res.scheme, res.netloc])
        except ValueError:
            return False

    @staticmethod
    def get_last_error() -> str:
        """
        Returns the last error thrown by the library
        Returns:
            str: A formatted error message
        """
        return QuickIni.error_message

    @staticmethod
    def strip_comment(s:str) -> str:
        """
        Removes a comment from a line. Any "#" starts a comment, unless it is escaped
        as "\\#", so values like "color=\\#fff" are kept intact.
        """
        for i, c in enumerate(s):
            if(c == "#" and (i == 0 or s[i - 1] != "\\")):
                return s[:i]
        return s

    @staticmethod
    def unescape(s:str) -> str:
        """
        Turns "\\#" in a value back into "#". Other backslashes are left alone.
        """
        return s.replace("\\#", "#")

    @staticmethod
    def escape(s:str) -> str:
        """
        Escapes "#" in a value as "\\#", so it isn't read as a comment.
        """
        return s.replace("#", "\\#")

    @staticmethod
    def section_name(line:str) -> str | None:
        """
        Returns the section name if the line is a "[section]" header, otherwise None.
        """
        stripped = QuickIni.strip_comment(line).strip()
        if(len(stripped) >= 2 and stripped.startswith("[") and stripped.endswith("]")):
            return stripped[1:-1].strip()
        return None

    @staticmethod
    def string_to_type(s:str) -> Any:
        """
        Convert a string to the appropriate type (int, float, bool, or str).

        Parameters:
        s (str): The input string to convert.

        Returns:
        Any: The converted value as int, float, bool, or str, based on the content of `s`.
            - Returns an int if `s` is a whole number, optionally signed (e.g. "42", "-5").
            - Returns a float if `s` is a decimal or scientific number (e.g. "3.14", "-1.5", "1e5").
            - Returns True for "true", "yes" or "on", and False for "false", "no" or "off" (case-insensitive).
            - Returns `s` unchanged if no other conditions are met.
        """
        if(INT_PATTERN.fullmatch(s)): return int(s)
        elif(FLOAT_PATTERN.fullmatch(s)): return float(s)
        elif(s.lower() in FALSE_WORDS): return False
        elif(s.lower() in TRUE_WORDS): return True
        return s

    @staticmethod
    def split_blocks(lines:list[str]) -> list[tuple[str | None, str | None, list[str]]]:
        """
        Splits lines into (key, section, lines) blocks. A key's block is its own line plus any "|" array lines,
        keys in a section are given as "section.key". Every other line is its own block with a key of None.
        """
        blocks = []
        current_section = None
        i = 0

        while i < len(lines):
            stripped = lines[i].strip()
            start = i
            key = None
            i += 1

            if(not stripped.startswith("#")):
                section = QuickIni.section_name(stripped)
                if(section is not None):
                    current_section = section
                else:
                    content = QuickIni.strip_comment(stripped)
                    if("=" in content):
                        left, right = content.split("=", 1)
                        key = left.strip()
                        if(current_section):
                            key = f"{current_section}.{key}"
                        if(not right.strip()):
                            while i < len(lines) and lines[i].strip().startswith("|"):
                                i += 1

            blocks.append((key, current_section, lines[start:i]))
        return blocks

    @staticmethod
    def atomic_write(path:str, text:str, mode_from:str) -> None:
        """
        Writes text to a temporary file next to path, then swaps it in, so the file is never left half written.
        The new file gets the permissions of mode_from.
        """
        fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".quick_ini_", suffix=".tmp")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as file:
                file.write(text)
            shutil.copymode(mode_from, temp_path)
            os.replace(temp_path, path)
        except BaseException:
            try: os.remove(temp_path)
            except OSError: pass
            raise

    @staticmethod
    def sync_template(file_location:str, template:bool | str = True) -> bool:
        """
        Brings a config file up to date with its template, keeping the values already set in the config.
        \nThe template decides which keys exist, their order, sections and comments. Keys the config doesn't have yet get
        the template's value, and keys the template doesn't have are kept at the end of their section.
        If the config doesn't exist it is created from the template. The file is only written when something changed,
        and the previous version is saved as "<config>.bak". Use get_sync_report() to see what changed.
        Args:
            file_location (str): The path of the config file.
            template (bool | str): True to use "<config>.template", skipped quietly if it doesn't exist.
                Or the path of the template file, which must exist.
        Returns:
            bool: True if successfull, False otherwise
        Example:
            >>> sync_template("config.ini")
                True
            >>> get_sync_report()["added"]
                ['database.timeout']
        """
        QuickIni.sync_report = None
        if(not template):
            return True

        file_location = str(file_location)
        if(QuickIni.is_string_url(file_location)):
            QuickIni.error_message = "Cannot sync a template into a file loaded from a URL"
            return False

        template_path = f"{file_location}.template" if template is True else str(template)
        if(QuickIni.is_string_url(template_path)):
            QuickIni.error_message = "Templates must be local files, not URLs"
            return False

        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                template_lines = file.read().splitlines()
        except FileNotFoundError:
            # A missing "<config>.template" is fine, a template that was asked for by name isn't
            if(template is True):
                return True
            QuickIni.error_message = f"Could not find template at: '{template_path}'"
            return False
        except IOError as e:
            QuickIni.error_message = f"Error reading template: '{e}'"
            return False

        # Resolve symlinks so the real file gets replaced, not the link
        path = os.path.realpath(file_location)
        old_text = None
        try:
            with open(path, 'r', encoding='utf-8') as file:
                old_text = file.read()
        except FileNotFoundError:
            pass
        except IOError as e:
            QuickIni.error_message = f"Error reading file: '{e}'"
            return False

        user_values = {}
        user_sections = {}
        if(old_text is not None):
            for key, section, block in QuickIni.split_blocks(old_text.splitlines()):
                if(key is not None):
                    user_values[key] = block
                    user_sections[key] = section

        # Walk the template, swapping in the user's lines for every key they have set
        new_lines = []
        template_keys = set()
        added = []
        for key, _, block in QuickIni.split_blocks(template_lines):
            if(key is None):
                new_lines.extend(block)
                continue
            template_keys.add(key)
            if(key in user_values):
                new_lines.extend(user_values[key])
            else:
                new_lines.extend(block)
                if(key not in added):
                    added.append(key)

        # Keep keys the template doesn't have, at the end of their own section
        orphaned = [key for key in user_values if key not in template_keys]
        sections = {}
        for key in orphaned:
            sections.setdefault(user_sections[key], []).extend(user_values[key])
        for section, block in sections.items():
            block = ["# Not in the template, kept from your config"] + block
            insert_at = QuickIni.find_insert_index(new_lines, section)
            if(insert_at is None):
                if(new_lines and new_lines[-1].strip()):
                    new_lines.append("")
                new_lines.append(f"[{section}]")
                new_lines.extend(block)
                continue
            if(insert_at > 0 and new_lines[insert_at - 1].strip()):
                block = [""] + block
            if(insert_at < len(new_lines) and new_lines[insert_at].strip()):
                block = block + [""]
            new_lines[insert_at:insert_at] = block

        new_text = "\n".join(new_lines) + "\n" if new_lines else ""
        changed = new_text != old_text
        backup = None

        if(changed):
            try:
                if(old_text is not None):
                    backup = f"{path}.bak"
                    shutil.copy2(path, backup)
                QuickIni.atomic_write(path, new_text, path if old_text is not None else template_path)
            except OSError as e:
                QuickIni.error_message = f"Could not write synced config '{file_location}': '{e}'"
                return False

        QuickIni.sync_report = {
            "created": old_text is None,
            "changed": changed,
            "added": added if old_text is not None else [],
            "orphaned": orphaned,
            "backup": backup,
        }
        return True

    @staticmethod
    def get_sync_report() -> dict[str, Any] | None:
        """
        Returns what the last template sync did, or None if no template was synced.
        Return:
            dict[str, Any]: "created" (bool) the config was made from the template, "changed" (bool) the config was rewritten,
                "added" (list) keys taken from the template, "orphaned" (list) keys kept that aren't in the template,
                "backup" (str | None) the path of the backup of the previous config
        Example:
            >>> load_file("config.ini", template=True)
                True
            >>> get_sync_report()
                {'created': False, 'changed': True, 'added': ['database.timeout'], 'orphaned': [], 'backup': '/app/config.ini.bak'}
        """
        if(QuickIni.sync_report is None):
            return None
        return {k: list(v) if isinstance(v, list) else v for k, v in QuickIni.sync_report.items()}

    @staticmethod
    def load_file(file_location:str, auto_type_convert:bool = True, empty_default:Any = None, template:bool | str = False) -> bool:
        """
        Load a ini style file from the file system or from a URL.
        \nUse get_value() or get_all() to access. Keys inside a [section] are stored as "section.key".
        Args:
            name (str): The path/URL of the file to load.
            auto_type_convert (bool): Automaticly convert into recognized types such as True/False, int, float.
            empty_default (Any): The default value when a value is left blank (overrides auto_type_convert).
            template (bool | str): Sync the file with a template before loading, see sync_template().
                True uses "<file>.template" if it exists, or pass the path of the template file.
        Returns:
            bool: True if successfull, False otherwise
        Example:
            >>> load_file("../config.ini", empty_default="")
                True
            >>> load_file("config.ini", template=True)
                True
        """
        QuickIni.parsed_ini = {}
        QuickIni.auto_type_convert_g = auto_type_convert

        if(not QuickIni.sync_template(file_location, template)):
            # sync_template sets the error message
            return False

        f_data:str

        # Check if the provided location is a URL
        if(QuickIni.is_string_url(file_location)):
            if(not QuickIni.grab_from_url(file_location)):
                # The grab_from_url sets the error message
                return False
            f_data = QuickIni.web_file
        # Otherwise assume it's a file path
        else:
            try:
                with open(str(file_location), 'r', encoding='utf-8') as file:
                    f_data = file.read()
            except FileNotFoundError:
                QuickIni.error_message = f"Could not find file at: '{file_location}'"
                return False
            except IOError as e:
                QuickIni.error_message = f"Error reading file: '{e}'"
                return False

        lines = f_data.splitlines()
        current_section = None
        i = 0

        while i < len(lines):
            stripped = lines[i].strip()

            # Skip full line comments
            if(stripped.startswith("#")):
                i += 1
                continue

            # Section headers apply to every key below them
            section = QuickIni.section_name(stripped)
            if(section is not None):
                current_section = section
                i += 1
                continue

            line = QuickIni.strip_comment(stripped)

            # Skip lines without "="
            if("=" not in line):
                i += 1
                continue

            left, right = line.split("=", 1)
            key = left.strip()
            right = QuickIni.unescape(right.strip())
            if(current_section):
                key = f"{current_section}.{key}"

            # Check if this is an array (empty value and next line starts with |)
            if not right and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
                # This is an array, collect all array items
                array_items = []
                i += 1  # Move to the first array item

                while i < len(lines) and lines[i].strip().startswith("|"):
                    array_value = QuickIni.unescape(QuickIni.strip_comment(lines[i].strip()[1:]).strip())  # Remove the | prefix

                    if auto_type_convert:
                        array_value = QuickIni.string_to_type(array_value)

                    array_items.append(array_value)
                    i += 1

                QuickIni.parsed_ini[key] = array_items
            else:
                # Regular key-value pair
                if(not right):
                    right = empty_default
                elif(not auto_type_convert):
                    pass # If we aren't auto converting, skip the conversion
                else:
                    right = QuickIni.string_to_type(right)

                QuickIni.parsed_ini[key] = right
                i += 1

        QuickIni.loaded_file_path=file_location
        return True

    @staticmethod
    def get_value(name:str, default:Any = None, expected_type:type | None = None, section:str | None = None) -> Any:
        """
        Returns the value attached to the given name.
        \nIf no setting is found, it will return the passed in default
        Args:
            name (str): The name of the setting, keys in a section can also be given as "section.key"
            default (Any): What will be returned if nothing is found
            expected_type (type): Will make sure the returned object is of this type, otherwise Raise()
            section (str): The [section] the setting is in, None for keys above any section
        Return:
            Any: The value associated with the name
        Example:
            >>> get_value("do_debug_logs", False)
            True
            >>> get_value("port", section="database")
            5432
        """
        if(section):
            name = f"{section}.{name}"
        value:Any = QuickIni.parsed_ini.get(name, default)
        if(expected_type != None):
            if(not isinstance(value, expected_type)):
                QuickIni.error_message = f"Expected type '{expected_type.__name__}', instead got '{type(value).__name__}'"
                raise(ValueError(QuickIni.error_message))
        return value

    @staticmethod
    def get_all(section:str | None = None) -> dict[str, Any]:
        """
        Returns a copy of all loaded settings.
        Args:
            section (str): Only return the settings in this [section], with the section prefix removed
        Return:
            dict[str, Any]: The settings, keys in a section are given as "section.key" when no section is passed
        Example:
            >>> get_all("database")
            {'host': 'localhost', 'port': 5432}
        """
        if(not section):
            return dict(QuickIni.parsed_ini)
        prefix = f"{section}."
        return {k[len(prefix):]: v for k, v in QuickIni.parsed_ini.items() if k.startswith(prefix)}

    @staticmethod
    def find_insert_index(lines:list[str], section:str | None) -> int | None:
        """
        Returns the index just after the last non-blank line of a section (None for keys above any section),
        or None if the section doesn't exist.
        """
        start = 0 if section is None else None
        end = len(lines)
        for i, line in enumerate(lines):
            name = QuickIni.section_name(line)
            if(name is None):
                continue
            if(start is not None):
                end = i
                break
            if(name == section):
                start = i + 1

        if(start is None):
            return None
        while end > start and not lines[end - 1].strip():
            end -= 1
        return end

    @staticmethod
    def write_value(key:str, value:Any, add_if_not_found:bool=False, update_locally:bool=True, do_backup:bool=False, section:str | None=None) -> Any:
        """
        Writes a key-value pair to the loaded .ini file.
        \nThe file is written to a temporary file first and then swapped in, so it is never left half written.

        Parameters:
        key (str): The key to update or add in the .ini file.
        value (Any): The value to write, which will be converted to a string. If value is a list, it will be written as an array.
        add_if_not_found (bool): If True, adds the key-value pair if the key is not found in the file (default is False).
        update_localy (bool): If True, updates the parsed_ini dictionary locally with the new key-value pair (default is True).
        do_backup (bool): Deprecated and ignored, writes are always safe now.
        section (str): The [section] the key is in, None for keys above any section. A missing section is created if add_if_not_found is True.

        Returns:
        Any: The value written, with optional type conversion if `auto_type_convert` was enabled.

        Raises:
        ValueError: If no local file is loaded, the key isn't found, or the value cannot be converted to a single line string.
        FileNotFoundError: If the specified file cannot be found.
        PermissionError: If there is an issue with file permissions.
        IOError: If there is a read or write error.

        Example:
        >>> write_value("example_key", 42, add_if_not_found=True)
        42
        >>> write_value("parts", ["one", "two", "three"], add_if_not_found=True)
        ["one", "two", "three"]
        >>> write_value("port", 5432, section="database")
        5432
        """

        if(not QuickIni.loaded_file_path):
            QuickIni.error_message = "No loaded file path, was a local file loaded?"
            raise(ValueError(QuickIni.error_message))
        if(QuickIni.is_string_url(QuickIni.loaded_file_path)):
            QuickIni.error_message = "Cannot write to a file loaded from a URL"
            raise(ValueError(QuickIni.error_message))

        items = value if isinstance(value, list) else [value]
        try: item_strings = [str(item) for item in items]
        except(TypeError, ValueError):
            QuickIni.error_message = "Could not convert value to a string"
            raise(ValueError(QuickIni.error_message))
        if(any("\n" in s or "\r" in s for s in item_strings)):
            QuickIni.error_message = "Values cannot contain line breaks"
            raise(ValueError(QuickIni.error_message))

        # Handle array values
        escaped = [QuickIni.escape(s) for s in item_strings]
        if isinstance(value, list):
            key_value_lines = [f"{key}=\n"] + [f"|{s}\n" for s in escaped]
        else:
            key_value_lines = [f"{key}={escaped[0]}\n"]

        # Resolve symlinks so the real file gets replaced, not the link
        path = os.path.realpath(str(QuickIni.loaded_file_path))

        try:
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            key_found=False
            current_section = None
            new_lines = []
            i = 0

            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                name = QuickIni.section_name(stripped)
                if(name is not None and not stripped.startswith("#")):
                    current_section = name
                elif(not key_found and current_section == section and not stripped.startswith("#")):
                    content = QuickIni.strip_comment(stripped)
                    if("=" in content):
                        left, right = content.split("=", 1)
                        if(left.strip() == key):
                            # Found the key, replace it and skip any existing array items
                            new_lines.extend(key_value_lines)
                            key_found = True
                            i += 1

                            if(not right.strip()):
                                while i < len(lines) and lines[i].strip().startswith("|"):
                                    i += 1
                            continue

                new_lines.append(line)
                i += 1

            if(not key_found):
                if(not add_if_not_found):
                    QuickIni.error_message = f"Could not find key '{key}'" + (f" in section '{section}'" if section else "")
                    raise(ValueError(QuickIni.error_message))

                insert_at = QuickIni.find_insert_index(new_lines, section)
                if(insert_at is None):
                    # The section doesn't exist yet, add it to the end of the file
                    if new_lines and not new_lines[-1].endswith("\n"):
                        new_lines[-1] += "\n"
                    if new_lines and new_lines[-1].strip():
                        new_lines.append("\n")
                    new_lines.append(f"[{section}]\n")
                    new_lines.extend(key_value_lines)
                else:
                    if insert_at > 0 and not new_lines[insert_at - 1].endswith("\n"):
                        new_lines[insert_at - 1] += "\n"
                    new_lines[insert_at:insert_at] = key_value_lines

            QuickIni.atomic_write(path, "".join(new_lines), path)

        except FileNotFoundError as e:
            QuickIni.error_message = f"Could not find file '{QuickIni.loaded_file_path}'"
            raise(e)
        except PermissionError as e:
            QuickIni.error_message = f"Permission error for file '{QuickIni.loaded_file_path}'"
            raise(e)
        except IOError as e:
            QuickIni.error_message = f"IOError when reading or writting to the file '{QuickIni.loaded_file_path}'"
            raise(e)

        # Handle return value, matching what load_file would read back
        converted = [QuickIni.string_to_type(s.strip()) if QuickIni.auto_type_convert_g else s.strip() for s in item_strings]
        v = converted if isinstance(value, list) else converted[0]

        if(update_locally):
            QuickIni.parsed_ini[f"{section}.{key}" if section else str(key)] = v

        return v
