from urllib.parse import urlparse
from typing import Type, Any, Union, Dict, Optional
import os

class QuickIni:
    parsed_ini: Dict[str, Union[str, int, bool, float, None]] = {}
    loaded_file_path: Optional[str] = None
    auto_type_convert_g: bool = True
    error_message: str = ""
    web_file: Optional[str] = None

    @staticmethod
    def grab_from_url(url:str) -> bool:
        import urllib.request, urllib.error
        try:
            with urllib.request.urlopen(url) as response:
                if(response.status == 200):
                    QuickIni.web_file = response.read().decode('utf-8')
                    return True
                else:
                    QuickIni.error_message = f"Failed to download file from {url}, got response: {response.status}"
                    return False
        except urllib.error.HTTPError as e:
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
    def string_to_type(s:str) -> Any:
        """
        Convert a string to the appropriate type (int, float, bool, or str).

        Parameters:
        s (str): The input string to convert.

        Returns:
        Any: The converted value as int, float, bool, or str, based on the content of `s`.
            - Returns an int if `s` contains only digits.
            - Returns a float if `s` is a numeric value with a single decimal point.
            - Returns a boolean (True or False) if `s` matches the strings "true" or "false" (case-insensitive).
            - Returns `s` unchanged if no other conditions are met.
        """
        if(s.isnumeric()): return int(s)
        elif(s.count(".") == 1 and s.replace(".", "").isnumeric()): return float(s)
        elif(s.lower() == "false"): return False
        elif(s.lower() == "true"): return True
        return s

    @staticmethod
    def load_file(file_location:str, auto_type_convert:bool = True, empty_default:Any = None) -> bool:
        """
        Load a ini style file from the file system or from a URL.
        \nUse get_value() or get_all() to access.
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

        for line in lines:
            if(line.startswith("#") or "=" not in line): continue # Ignore comments and lines without "="
            left, right = line.split("=", 1)
            if(not right): right = empty_default
            elif(not auto_type_convert): pass # If we aren't auto converting, skip the conversion
            else: right = QuickIni.string_to_type(right)

            QuickIni.parsed_ini[left] = right

        QuickIni.loaded_file_path=file_location
        return True

    @staticmethod
    def get_value(name:str, default:Any = None, expected_type:Type = None) -> Any:
        """
        Returns the value attached to the given name.
        \nIf no setting is found, it will return the passed in default
        Args:
            name (str): The name of the setting
            default (Any): What will be returned if nothing is found
            expected_type (Type): Will make sure the returned object is of this Type, otherwise Raise()
        Return:
            Any: The value associated with the name
        Example:
            >>> get_value("do_debug_logs", False)
            True
        """
        value:Any = QuickIni.parsed_ini.get(name, default)
        if(expected_type != None):
            if(not isinstance(value, expected_type)):
                QuickIni.error_message = f"Expected type '{expected_type.__name__}', instead got '{type(value).__name__}'"
                raise(ValueError(QuickIni.error_message))
        return value

    def write_value(key:str, value:Any, add_if_not_found:bool=False, update_locally:bool=True, do_backup:bool=False) -> Any:
        """
        Writes a key-value pair to the loaded .ini file, with an optional dry run mode.
        
        Parameters:
        key (str): The key to update or add in the .ini file.
        value (Any): The value to write, which will be converted to a string.
        add_if_not_found (bool): If True, adds the key-value pair if the key is not found in the file (default is False).
        update_localy (bool): If True, updates the parsed_ini dictionary locally with the new key-value pair (default is True).
        do_backup (bool): If True, creates a backup of the original file before making changes, and removes if successful.
        
        Returns:
        Any: The value written or simulated, with optional type conversion if `auto_type_convert` was enabled.

        Raises:
        ValueError: If no file path is loaded or if the value cannot be converted to a string.
        FileNotFoundError: If the specified file cannot be found.
        PermissionError: If there is an issue with file permissions.
        IOError: If there is a read or write error.

        Example:
        >>> write_value("example_key", 42, add_if_not_found=True)
        42
        """

        if(not QuickIni.loaded_file_path):
            QuickIni.error_message = "No loaded file path, was a local file loaded?"
            raise(ValueError(QuickIni.error_message))

        try: str(value)
        except(TypeError, ValueError):
            QuickIni.error_message = "Could not convert value to a string"
            raise(ValueError(QuickIni.error_message))

        key_value_pair = f"{str(key)}={str(value)}\n"

        try:
            file = open(str(QuickIni.loaded_file_path), 'r', encoding='utf-8')
            lines = file.readlines()
            file.close()

            # Create backup
            if(do_backup):
                backup_file = open(f"{str(QuickIni.loaded_file_path)}.backup", 'w', encoding='utf-8')
                backup_file.writelines(lines)
                backup_file.close()
                print("Backup created at", f"{str(QuickIni.loaded_file_path)}.backup")

            key_found=False
            last_line=""
            file = open(str(QuickIni.loaded_file_path), 'w')
            for line in lines:
                if(not line.startswith("#") and not key_found and line.startswith(f"{key}=")):
                    last_line = key_value_pair
                    key_found = True
                else:
                    last_line = line
                file.write(last_line)

            if(not key_found):
                if(add_if_not_found):
                    if(not last_line.endswith("\n")):
                        file.write("\n")
                    file.write(f"{key_value_pair}")
                else:
                    QuickIni.error_message = f"Could not find key '{key}'"
                    raise(ValueError(QuickIni.error_message))

            file.close()

        except FileNotFoundError as e:
            QuickIni.error_message = f"Could not find file '{QuickIni.loaded_file_path}'"
            raise(e)
        except PermissionError as e:
            QuickIni.error_message = f"Permission error for file '{QuickIni.loaded_file_path}'"
            raise(e)
        except IOError as e:
            QuickIni.error_message = f"IOError when reading or writting to the file '{QuickIni.loaded_file_path}'"
            raise(e)

        v = QuickIni.string_to_type(str(value)) if QuickIni.auto_type_convert_g else str(value)
        if(update_locally):
            QuickIni.parsed_ini[str(key)] = v

        # Remove backup
        if(do_backup):
            try: os.remove(f"{str(QuickIni.loaded_file_path)}.backup")
            except Exception as e:
                QuickIni.error_message = "Failed to remove backup file"
                raise(e)

        return v
