from urllib.parse import urlparse
from typing import Type, Any, Union, Dict, Optional, List
import os
import re
import shutil
import tempfile

TRUE_WORDS = ("true", "yes", "on")
FALSE_WORDS = ("false", "no", "off")
INT_PATTERN = re.compile(r"[+-]?[0-9]+")
FLOAT_PATTERN = re.compile(r"[+-]?(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|[+-]?[0-9]+[eE][+-]?[0-9]+")

class QuickIni:
    parsed_ini: Dict[str, Union[str, int, bool, float, List, None]] = {}
    loaded_file_path: Optional[str] = None
    auto_type_convert_g: bool = True
    error_message: str = ""
    web_file: Optional[str] = None

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
        Removes an inline comment from a line. A "#" or ";" only starts a comment when it
        follows whitespace, so values like "color=#fff" are kept intact.
        """
        for i in range(1, len(s)):
            if(s[i] in "#;" and s[i - 1].isspace()):
                return s[:i]
        return s

    @staticmethod
    def section_name(line:str) -> Optional[str]:
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
    def load_file(file_location:str, auto_type_convert:bool = True, empty_default:Any = None) -> bool:
        """
        Load a ini style file from the file system or from a URL.
        \nUse get_value() or get_all() to access. Keys inside a [section] are stored as "section.key".
        Args:
            name (str): The path/URL of the file to load.
            auto_type_convert (bool): Automaticly convert into recognized types such as True/False, int, float.
            empty_default (Any): The default value when a value is left blank (overrides auto_type_convert).
        Returns:
            bool: True if successfull, False otherwise
        Example:
            >>> load_file("../config.ini", empty_default="")
                True
        """
        QuickIni.parsed_ini = {}
        QuickIni.auto_type_convert_g = auto_type_convert

        f_data:str = None

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
            if(stripped.startswith(("#", ";"))):
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
            right = right.strip()
            if(current_section):
                key = f"{current_section}.{key}"

            # Check if this is an array (empty value and next line starts with |)
            if not right and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
                # This is an array, collect all array items
                array_items = []
                i += 1  # Move to the first array item

                while i < len(lines) and lines[i].strip().startswith("|"):
                    array_value = QuickIni.strip_comment(lines[i].strip()[1:]).strip()  # Remove the | prefix

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
    def get_value(name:str, default:Any = None, expected_type:Type = None, section:Optional[str] = None) -> Any:
        """
        Returns the value attached to the given name.
        \nIf no setting is found, it will return the passed in default
        Args:
            name (str): The name of the setting, keys in a section can also be given as "section.key"
            default (Any): What will be returned if nothing is found
            expected_type (Type): Will make sure the returned object is of this Type, otherwise Raise()
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
    def get_all(section:Optional[str] = None) -> Dict[str, Any]:
        """
        Returns a copy of all loaded settings.
        Args:
            section (str): Only return the settings in this [section], with the section prefix removed
        Return:
            Dict[str, Any]: The settings, keys in a section are given as "section.key" when no section is passed
        Example:
            >>> get_all("database")
            {'host': 'localhost', 'port': 5432}
        """
        if(not section):
            return dict(QuickIni.parsed_ini)
        prefix = f"{section}."
        return {k[len(prefix):]: v for k, v in QuickIni.parsed_ini.items() if k.startswith(prefix)}

    @staticmethod
    def find_insert_index(lines:List[str], section:Optional[str]) -> Optional[int]:
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
    def write_value(key:str, value:Any, add_if_not_found:bool=False, update_locally:bool=True, do_backup:bool=False, section:Optional[str]=None) -> Any:
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
        if isinstance(value, list):
            key_value_lines = [f"{key}=\n"] + [f"|{s}\n" for s in item_strings]
        else:
            key_value_lines = [f"{key}={item_strings[0]}\n"]

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
                if(name is not None and not stripped.startswith(("#", ";"))):
                    current_section = name
                elif(not key_found and current_section == section and not stripped.startswith(("#", ";"))):
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

            # Write to a temporary file next to the original, then swap it in
            fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".quick_ini_", suffix=".tmp")
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as file:
                    file.writelines(new_lines)
                shutil.copymode(path, temp_path)
                os.replace(temp_path, path)
            except BaseException:
                try: os.remove(temp_path)
                except OSError: pass
                raise

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
