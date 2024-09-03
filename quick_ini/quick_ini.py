from urllib.parse import urlparse
from typing import Type, Any

parsed_ini:dict[str,str|int|bool|float|None] = {}
error_message:str = ""
web_file:str = None

def grab_from_url(url:str) -> bool:
    global web_file, error_message
    import urllib.request, urllib.error
    try:
        with urllib.request.urlopen(url) as response:
            if(response.status == 200):
                web_file = response.read().decode('utf-8')
                return True
            else:
                error_message = f"Failed to download file from {url}, got response: {response.status}"
                return False
    except urllib.error.HTTPError as e:
        error_message = f"Could not get file from URL: '{e}'"
        return False

def is_string_url(stri:str) -> bool:
    try:
        res = urlparse(stri)
        return all([res.scheme, res.netloc])
    except ValueError:
        return False

def get_last_error() -> str:
    """
    Returns the last error thrown by the library
    Returns:
        str: A formatted error message
    """
    return error_message

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
    global error_message, parsed_ini
    parsed_ini = {}

    f_data:str = None

    # Check if the provided location is a URL
    if(is_string_url(file_location)):
        if(not grab_from_url(file_location)):
            # The grab_from_url sets the error message
            return False
        f_data = web_file
    # Otherwise assume it's a file path
    else:
        try:
            f_data = open(str(file_location), 'r', encoding='utf-8').read()
        except FileNotFoundError:
            error_message = f"Could not find file at: '{file_location}'"
            return False
        except IOError as e:
            error_message = f"Error reading file: '{e}'"
            return False

    lines = f_data.splitlines()
    
    for line in lines:
        if(line.startswith("#") or "=" not in line): continue # Ignore comments and lines without "="
        left, right = line.split("=", 1)
        if(not right): right = empty_default
        elif(not auto_type_convert): pass # If we arn't auto converting, pass through the rest of the IFs
        elif(right.isnumeric()): right = int(right)
        elif(right.count(".") == 1 and right.replace(".", "").isnumeric()): right = float(right)
        elif(right.lower() == "false"): right = False
        elif(right.lower() == "true"): right = True

        parsed_ini[left] = right
    return True
    
def get_value(name:str, default:Any = None, expected_type:Type = None):
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
    value:Any = parsed_ini.get(name, default)
    if(expected_type != None):
        if(not isinstance(value, expected_type)):
            error = f"Expected type '{expected_type.__name__}', instead got '{type(value).__name__}'"
            raise(ValueError(error))
    return value