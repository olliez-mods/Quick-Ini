#
# WRITTEN ENTIRELY BY CHATGPT
# I DON'T TRUST IT
#

import unittest
import tempfile
import os
from unittest.mock import patch, mock_open
from quick_ini import QuickIni


class TestQuickIni(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear any previous state
        QuickIni.parsed_ini = {}
        QuickIni.loaded_file_path = None
        QuickIni.auto_type_convert_g = True
        QuickIni.error_message = ""
        QuickIni.web_file = None
        
        # Create a temporary INI file for testing
        self.test_content = """# Test configuration
debug=true
port=8080
timeout=30.5
name=TestApp
empty_value=
false_value=false

# Array example
parts=
|one
|two
|three

# Mixed array
mixed=
|text
|42
|3.14
|true
|false

# Comments and edge cases
# This is a comment
another_key=value with spaces
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    # ===== BASIC LOADING TESTS =====
    
    def test_load_file_success(self):
        """Test loading an INI file successfully."""
        result = QuickIni.load_file(self.temp_file.name)
        self.assertTrue(result)
        self.assertEqual(QuickIni.loaded_file_path, self.temp_file.name)
        
    def test_load_file_nonexistent(self):
        """Test loading a nonexistent file."""
        result = QuickIni.load_file("nonexistent_file.ini")
        self.assertFalse(result)
        error = QuickIni.get_last_error()
        self.assertIn("Could not find file", error)
        
    def test_load_file_with_auto_type_convert_disabled(self):
        """Test loading with auto type conversion disabled."""
        result = QuickIni.load_file(self.temp_file.name, auto_type_convert=False)
        self.assertTrue(result)
        # All values should be strings when auto_type_convert is False
        self.assertEqual(QuickIni.get_value("port"), "8080")
        self.assertEqual(QuickIni.get_value("debug"), "true")
        self.assertEqual(QuickIni.get_value("timeout"), "30.5")
        
    def test_load_file_with_empty_default(self):
        """Test loading with custom empty default value."""
        result = QuickIni.load_file(self.temp_file.name, empty_default="EMPTY")
        self.assertTrue(result)
        self.assertEqual(QuickIni.get_value("empty_value"), "EMPTY")
        
    # ===== TYPE CONVERSION TESTS =====
    
    def test_string_to_type_integer(self):
        """Test string to integer conversion."""
        self.assertEqual(QuickIni.string_to_type("123"), 123)
        self.assertEqual(QuickIni.string_to_type("0"), 0)
        
    def test_string_to_type_float(self):
        """Test string to float conversion."""
        self.assertEqual(QuickIni.string_to_type("123.45"), 123.45)
        self.assertEqual(QuickIni.string_to_type("0.0"), 0.0)
        
    def test_string_to_type_boolean(self):
        """Test string to boolean conversion."""
        self.assertEqual(QuickIni.string_to_type("true"), True)
        self.assertEqual(QuickIni.string_to_type("True"), True)
        self.assertEqual(QuickIni.string_to_type("TRUE"), True)
        self.assertEqual(QuickIni.string_to_type("false"), False)
        self.assertEqual(QuickIni.string_to_type("False"), False)
        self.assertEqual(QuickIni.string_to_type("FALSE"), False)
        
    def test_string_to_type_string(self):
        """Test string remains string when not convertible."""
        self.assertEqual(QuickIni.string_to_type("hello"), "hello")
        self.assertEqual(QuickIni.string_to_type("123abc"), "123abc")
        self.assertEqual(QuickIni.string_to_type("12.34.56"), "12.34.56")
        
    # ===== GET VALUE TESTS =====
        
    def test_get_value_string(self):
        """Test getting string values."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("name")
        self.assertEqual(value, "TestApp")
        self.assertIsInstance(value, str)
        
    def test_get_value_boolean_true(self):
        """Test getting boolean true values."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("debug")
        self.assertTrue(value)
        self.assertIsInstance(value, bool)
        
    def test_get_value_boolean_false(self):
        """Test getting boolean false values."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("false_value")
        self.assertFalse(value)
        self.assertIsInstance(value, bool)
        
    def test_get_value_integer(self):
        """Test getting integer values."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("port")
        self.assertEqual(value, 8080)
        self.assertIsInstance(value, int)
        
    def test_get_value_float(self):
        """Test getting float values."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("timeout")
        self.assertEqual(value, 30.5)
        self.assertIsInstance(value, float)
        
    def test_get_value_default(self):
        """Test getting default values for missing keys."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("missing_key", "default")
        self.assertEqual(value, "default")
        
    def test_get_value_with_type_checking(self):
        """Test get_value with expected_type parameter."""
        QuickIni.load_file(self.temp_file.name)
        
        # Valid type checks should pass
        value = QuickIni.get_value("port", expected_type=int)
        self.assertEqual(value, 8080)
        
        value = QuickIni.get_value("name", expected_type=str)
        self.assertEqual(value, "TestApp")
        
        # Invalid type checks should raise ValueError
        with self.assertRaises(ValueError):
            QuickIni.get_value("port", expected_type=str)
            
    def test_get_value_spaces_in_value(self):
        """Test getting values with spaces."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("another_key")
        self.assertEqual(value, "value with spaces")
        
    # ===== ARRAY TESTS =====
        
    def test_get_array_value(self):
        """Test getting array values."""
        QuickIni.load_file(self.temp_file.name)
        parts = QuickIni.get_value("parts")
        self.assertEqual(parts, ["one", "two", "three"])
        self.assertIsInstance(parts, list)
        
    def test_get_mixed_array_with_type_conversion(self):
        """Test getting mixed type arrays with automatic conversion."""
        QuickIni.load_file(self.temp_file.name)
        mixed = QuickIni.get_value("mixed")
        self.assertEqual(mixed[0], "text")
        self.assertEqual(mixed[1], 42)
        self.assertEqual(mixed[2], 3.14)
        self.assertEqual(mixed[3], True)
        self.assertEqual(mixed[4], False)
        
    def test_array_without_type_conversion(self):
        """Test arrays without automatic type conversion."""
        QuickIni.load_file(self.temp_file.name, auto_type_convert=False)
        mixed = QuickIni.get_value("mixed")
        # All should be strings
        self.assertEqual(mixed, ["text", "42", "3.14", "true", "false"])
        
    def test_write_array_value(self):
        """Test writing array values to file."""
        QuickIni.load_file(self.temp_file.name)
        test_array = ["apple", "banana", "cherry"]
        result = QuickIni.write_value("fruits", test_array, add_if_not_found=True)
        self.assertEqual(result, test_array)
        
        # Verify it was written as an array
        fruits = QuickIni.get_value("fruits")
        self.assertEqual(fruits, test_array)
        self.assertIsInstance(fruits, list)
        
    def test_write_mixed_array(self):
        """Test writing mixed type arrays."""
        QuickIni.load_file(self.temp_file.name)
        mixed_array = ["text", 42, 3.14, True, False]
        QuickIni.write_value("new_mixed", mixed_array, add_if_not_found=True)
        
        # Reload to test parsing
        QuickIni.load_file(self.temp_file.name)
        result = QuickIni.get_value("new_mixed")
        self.assertEqual(result, mixed_array)
        
    def test_replace_existing_array(self):
        """Test replacing an existing array."""
        QuickIni.load_file(self.temp_file.name)
        original_parts = QuickIni.get_value("parts")
        self.assertEqual(original_parts, ["one", "two", "three"])
        
        # Replace with new array
        new_parts = ["alpha", "beta", "gamma"]
        QuickIni.write_value("parts", new_parts)
        
        # Verify replacement
        updated_parts = QuickIni.get_value("parts")
        self.assertEqual(updated_parts, new_parts)
        
    # ===== WRITE VALUE TESTS =====
        
    def test_write_value_new_key(self):
        """Test writing new key-value pairs."""
        QuickIni.load_file(self.temp_file.name)
        result = QuickIni.write_value("new_key", "new_value", add_if_not_found=True)
        self.assertEqual(result, "new_value")
        
        # Verify it was written
        value = QuickIni.get_value("new_key")
        self.assertEqual(value, "new_value")
        
    def test_write_value_existing_key(self):
        """Test updating existing key-value pairs."""
        QuickIni.load_file(self.temp_file.name)
        # Update existing value
        result = QuickIni.write_value("name", "UpdatedApp")
        self.assertEqual(result, "UpdatedApp")
        
        # Verify it was updated
        value = QuickIni.get_value("name")
        self.assertEqual(value, "UpdatedApp")
        
    def test_write_value_key_not_found_without_add_flag(self):
        """Test writing to non-existent key without add_if_not_found flag."""
        QuickIni.load_file(self.temp_file.name)
        with self.assertRaises(ValueError) as context:
            QuickIni.write_value("nonexistent_key", "value")
        self.assertIn("Could not find key", str(context.exception))
        
    def test_write_value_no_file_loaded(self):
        """Test writing when no file is loaded."""
        with self.assertRaises(ValueError) as context:
            QuickIni.write_value("key", "value")
        self.assertIn("No loaded file path", str(context.exception))
        
    def test_write_value_with_backup(self):
        """Test writing with backup functionality."""
        QuickIni.load_file(self.temp_file.name)
        backup_path = f"{self.temp_file.name}.backup"
        
        # Ensure backup doesn't exist initially
        if os.path.exists(backup_path):
            os.remove(backup_path)
            
        QuickIni.write_value("name", "BackupTest", do_backup=True)
        
        # Backup should be created and then removed
        self.assertFalse(os.path.exists(backup_path))
        
    def test_write_value_update_locally_false(self):
        """Test writing without updating local dictionary."""
        QuickIni.load_file(self.temp_file.name)
        original_value = QuickIni.get_value("name")
        
        QuickIni.write_value("name", "NotUpdatedLocally", update_locally=False)
        
        # Local value should remain unchanged
        current_value = QuickIni.get_value("name")
        self.assertEqual(current_value, original_value)
        
    # ===== URL FUNCTIONALITY TESTS =====
        
    def test_is_string_url_valid(self):
        """Test URL validation with valid URLs."""
        self.assertTrue(QuickIni.is_string_url("http://example.com"))
        self.assertTrue(QuickIni.is_string_url("https://example.com"))
        self.assertTrue(QuickIni.is_string_url("ftp://example.com"))
        
    def test_is_string_url_invalid(self):
        """Test URL validation with invalid URLs."""
        self.assertFalse(QuickIni.is_string_url("not_a_url"))
        self.assertFalse(QuickIni.is_string_url("file.txt"))
        self.assertFalse(QuickIni.is_string_url(""))
        
    @patch('urllib.request.urlopen')
    def test_grab_from_url_success_with_different_status(self, mock_urlopen):
        """Test successful URL loading with status 200."""
        # Mock successful HTTP response with explicit status check
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.status = 200
        mock_response.read.return_value = b"status_test=success"
        
        result = QuickIni.grab_from_url("http://example.com/status.ini")
        self.assertTrue(result)
        self.assertEqual(QuickIni.web_file, "status_test=success")
        
    @patch('urllib.request.urlopen')
    def test_grab_from_url_non_200_status(self, mock_urlopen):
        """Test URL loading with non-200 status code."""
        # Mock non-200 HTTP response
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.status = 500
        
        result = QuickIni.grab_from_url("http://example.com/error.ini")
        self.assertFalse(result)
        self.assertIn("Failed to download file", QuickIni.get_last_error())
        self.assertIn("got response: 500", QuickIni.get_last_error())
        
    @patch('urllib.request.urlopen')
    def test_grab_from_url_http_error_exception(self, mock_urlopen):
        """Test URL loading with HTTPError exception."""
        from urllib.error import HTTPError
        # Mock HTTPError exception
        mock_urlopen.side_effect = HTTPError(None, 404, "Not Found", None, None)
        
        result = QuickIni.grab_from_url("http://example.com/notfound.ini")
        self.assertFalse(result)
        self.assertIn("Could not get file from URL", QuickIni.get_last_error())
        
    def test_is_string_url_value_error(self):
        """Test URL validation with malformed URL that raises ValueError."""
        # Test with a string that causes urlparse to raise ValueError
        result = QuickIni.is_string_url("ht tp://invalid url")
        self.assertFalse(result)
        
    def test_write_value_permission_error(self):
        """Test write_value with permission errors."""
        QuickIni.load_file(self.temp_file.name)
        
        # Mock file operations to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                QuickIni.write_value("test_key", "test_value")
                
    def test_write_value_io_error(self):
        """Test write_value with I/O errors."""
        QuickIni.load_file(self.temp_file.name)
        
        # Mock file operations to raise IOError
        with patch('builtins.open', side_effect=IOError("I/O error")):
            with self.assertRaises(IOError):
                QuickIni.write_value("test_key", "test_value")
                
    def test_write_value_failed_write_keeps_original(self):
        """Test a failed write leaves the original file untouched and no temp files behind."""
        QuickIni.load_file(self.temp_file.name)
        directory = os.path.dirname(self.temp_file.name)
        files_before = set(os.listdir(directory))

        with patch('os.replace', side_effect=OSError("Cannot replace")):
            with self.assertRaises(OSError):
                QuickIni.write_value("name", "Broken")

        with open(self.temp_file.name, encoding='utf-8') as f:
            self.assertEqual(f.read(), self.test_content)
        self.assertEqual(set(os.listdir(directory)), files_before)
        
    @patch('urllib.request.urlopen')
    def test_load_file_from_url(self, mock_urlopen):
        """Test loading INI file from URL."""
        # Mock successful HTTP response
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.status = 200
        mock_response.read.return_value = b"url_key=url_value\nurl_port=9090"
        
        result = QuickIni.load_file("http://example.com/config.ini")
        self.assertTrue(result)
        self.assertEqual(QuickIni.get_value("url_key"), "url_value")
        self.assertEqual(QuickIni.get_value("url_port"), 9090)
        
    # ===== ERROR HANDLING TESTS =====
        
    def test_get_last_error(self):
        """Test error message retrieval."""
        # Trigger an error
        QuickIni.load_file("nonexistent_file.ini")
        error = QuickIni.get_last_error()
        self.assertIsInstance(error, str)
        self.assertTrue(len(error) > 0)
        
    def test_file_io_error_handling(self):
        """Test handling of file I/O errors."""
        # Test with invalid file path
        result = QuickIni.load_file("/invalid/path/file.ini")
        self.assertFalse(result)
        error = QuickIni.get_last_error()
        self.assertIn("Could not find file", error)
        
    # ===== EDGE CASES =====
        
    def test_empty_ini_file(self):
        """Test loading empty INI file."""
        empty_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        empty_file.write("")
        empty_file.close()
        
        try:
            result = QuickIni.load_file(empty_file.name)
            self.assertTrue(result)
            # Should have no parsed values
            self.assertEqual(len(QuickIni.parsed_ini), 0)
        finally:
            os.unlink(empty_file.name)
            
    def test_comments_only_file(self):
        """Test loading file with only comments."""
        comments_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        comments_file.write("# Comment 1\n# Comment 2\n# Comment 3")
        comments_file.close()
        
        try:
            result = QuickIni.load_file(comments_file.name)
            self.assertTrue(result)
            # Should have no parsed values
            self.assertEqual(len(QuickIni.parsed_ini), 0)
        finally:
            os.unlink(comments_file.name)
            
    def test_malformed_lines(self):
        """Test handling of malformed lines without equals signs."""
        malformed_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        malformed_file.write("valid_key=valid_value\nmalformed_line_no_equals\nanother_valid=value")
        malformed_file.close()
        
        try:
            result = QuickIni.load_file(malformed_file.name)
            self.assertTrue(result)
            # Should only have valid lines
            self.assertEqual(QuickIni.get_value("valid_key"), "valid_value")
            self.assertEqual(QuickIni.get_value("another_valid"), "value")
            # Malformed line should be ignored
            self.assertIsNone(QuickIni.get_value("malformed_line_no_equals"))
        finally:
            os.unlink(malformed_file.name)


class TestQuickIniFormats(unittest.TestCase):
    """Tests for spacing, comments, sections and the extra value formats."""

    def setUp(self):
        QuickIni.parsed_ini = {}
        QuickIni.loaded_file_path = None
        QuickIni.auto_type_convert_g = True
        QuickIni.error_message = ""
        QuickIni.web_file = None
        self.paths = []

    def tearDown(self):
        for path in self.paths:
            if os.path.exists(path):
                os.unlink(path)

    def load(self, content):
        temp = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False, encoding='utf-8')
        temp.write(content)
        temp.close()
        self.paths.append(temp.name)
        self.assertTrue(QuickIni.load_file(temp.name))
        return temp.name

    def read(self, path):
        with open(path, encoding='utf-8') as f:
            return f.read()

    # ===== PARSING =====

    def test_spaces_around_equals(self):
        self.load("port = 8080\n  name =  App  \n")
        self.assertEqual(QuickIni.get_value("port"), 8080)
        self.assertEqual(QuickIni.get_value("name"), "App")

    def test_signed_and_scientific_numbers(self):
        self.assertEqual(QuickIni.string_to_type("-5"), -5)
        self.assertEqual(QuickIni.string_to_type("+5"), 5)
        self.assertEqual(QuickIni.string_to_type("-1.5"), -1.5)
        self.assertEqual(QuickIni.string_to_type("1e5"), 100000.0)
        self.assertEqual(QuickIni.string_to_type("2.5E-3"), 0.0025)
        self.assertEqual(QuickIni.string_to_type(".5"), 0.5)

    def test_non_numbers_stay_strings(self):
        # These used to crash or be misread
        for s in ["²", "1_000", "١٢", "-", "1e", "e5", "inf", "nan", "."]:
            self.assertEqual(QuickIni.string_to_type(s), s)

    def test_bool_words(self):
        for s in ["yes", "YES", "on", "On", "true"]:
            self.assertIs(QuickIni.string_to_type(s), True)
        for s in ["no", "No", "off", "OFF", "false"]:
            self.assertIs(QuickIni.string_to_type(s), False)

    def test_inline_comments(self):
        self.load("# a comment\n  # indented comment\nport=8080 # dev port\nmode=fast#no space\nkey =   # fill this in\n")
        self.assertEqual(QuickIni.get_all(), {"port": 8080, "mode": "fast", "key": None})

    def test_semicolon_is_not_a_comment(self):
        self.load("list=a;b ; c\n")
        self.assertEqual(QuickIni.get_value("list"), "a;b ; c")

    def test_escaped_comment_characters(self):
        self.load("color=\\#fff\nurl = http://x.com/a\\#b  # link\npath=C:\\new\\dir\nparts =\n|\\#1  # first\n")
        self.assertEqual(QuickIni.get_all(), {"color": "#fff", "url": "http://x.com/a#b", "path": "C:\\new\\dir", "parts": ["#1"]})

    def test_write_escapes_comment_characters(self):
        path = self.load("color=red\n")
        self.assertEqual(QuickIni.write_value("color", "#fff"), "#fff")
        QuickIni.write_value("tags", ["a;b", "#c"], add_if_not_found=True)
        self.assertEqual(self.read(path), "color=\\#fff\ntags=\n|a;b\n|\\#c\n")
        QuickIni.load_file(path)
        self.assertEqual(QuickIni.get_value("color"), "#fff")
        self.assertEqual(QuickIni.get_value("tags"), ["a;b", "#c"])

    def test_array_items_trimmed_and_commented(self):
        self.load("parts =\n  | one\n|2  # two\n")
        self.assertEqual(QuickIni.get_value("parts"), ["one", 2])

    def test_sections(self):
        self.load("port=1\n[db]\nport = 5432\nhost=localhost\n[ web ]  # site\nport=80\n")
        self.assertEqual(QuickIni.get_value("port"), 1)
        self.assertEqual(QuickIni.get_value("port", section="db"), 5432)
        self.assertEqual(QuickIni.get_value("db.port"), 5432)
        self.assertEqual(QuickIni.get_value("port", section="web"), 80)
        self.assertEqual(QuickIni.get_value("missing", "d", section="db"), "d")

    def test_get_all(self):
        self.load("a=1\n[db]\nport=5432\nhost=localhost\n")
        self.assertEqual(QuickIni.get_all(), {"a": 1, "db.port": 5432, "db.host": "localhost"})
        self.assertEqual(QuickIni.get_all("db"), {"port": 5432, "host": "localhost"})
        self.assertEqual(QuickIni.get_all("nope"), {})
        # Should be a copy
        QuickIni.get_all()["a"] = 2
        self.assertEqual(QuickIni.get_value("a"), 1)

    # ===== WRITING =====

    def test_write_existing_key_with_spaces(self):
        path = self.load("port = 8080 # dev\nname=App\n")
        QuickIni.write_value("port", 9090)
        self.assertEqual(self.read(path), "port=9090\nname=App\n")

    def test_write_ignores_commented_key(self):
        path = self.load("# port=1\nport=2\n")
        QuickIni.write_value("port", 3)
        self.assertEqual(self.read(path), "# port=1\nport=3\n")

    def test_write_in_section(self):
        path = self.load("port=1\n\n[db]\nport=5432\n\n[web]\nport=80\n")
        QuickIni.write_value("port", 6000, section="db")
        self.assertEqual(self.read(path), "port=1\n\n[db]\nport=6000\n\n[web]\nport=80\n")
        self.assertEqual(QuickIni.get_value("port", section="db"), 6000)
        self.assertEqual(QuickIni.get_value("port"), 1)

    def test_add_key_to_existing_section(self):
        path = self.load("[db]\nport=5432\n\n[web]\nport=80\n")
        QuickIni.write_value("host", "localhost", add_if_not_found=True, section="db")
        self.assertEqual(self.read(path), "[db]\nport=5432\nhost=localhost\n\n[web]\nport=80\n")

    def test_add_top_level_key_goes_above_sections(self):
        path = self.load("a=1\n\n[db]\nport=5432\n")
        QuickIni.write_value("b", 2, add_if_not_found=True)
        self.assertEqual(self.read(path), "a=1\nb=2\n\n[db]\nport=5432\n")
        QuickIni.load_file(path)
        self.assertEqual(QuickIni.get_value("b"), 2)

    def test_add_new_section(self):
        path = self.load("a=1")
        QuickIni.write_value("port", 80, add_if_not_found=True, section="web")
        self.assertEqual(self.read(path), "a=1\n\n[web]\nport=80\n")

    def test_write_missing_section_without_add_flag(self):
        self.load("a=1\n")
        with self.assertRaises(ValueError) as context:
            QuickIni.write_value("port", 80, section="web")
        self.assertIn("in section 'web'", str(context.exception))

    def test_write_value_with_line_break_rejected(self):
        path = self.load("a=1\n")
        with self.assertRaises(ValueError):
            QuickIni.write_value("a", "two\nlines")
        with self.assertRaises(ValueError):
            QuickIni.write_value("a", ["ok", "not\rok"])
        self.assertEqual(self.read(path), "a=1\n")

    def test_write_keeps_unicode_and_permissions(self):
        path = self.load("name=café\n")
        os.chmod(path, 0o640)
        QuickIni.write_value("city", "Zürich", add_if_not_found=True)
        self.assertEqual(self.read(path), "name=café\ncity=Zürich\n")
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o640)

    def test_write_after_url_load_rejected(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.status = 200
            mock_response.read.return_value = b"a=1"
            QuickIni.load_file("http://example.com/config.ini")
        with self.assertRaises(ValueError) as context:
            QuickIni.write_value("a", 2)
        self.assertIn("URL", str(context.exception))

    # ===== URLS =====

    @patch('urllib.request.urlopen')
    def test_url_network_error_returns_false(self, mock_urlopen):
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("no internet")
        self.assertFalse(QuickIni.load_file("http://example.com/config.ini"))
        self.assertIn("Could not get file from URL", QuickIni.get_last_error())

    @patch('urllib.request.urlopen')
    def test_url_timeout_returns_false(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("timed out")
        self.assertFalse(QuickIni.load_file("http://example.com/config.ini"))
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 10)



class TestQuickIniTemplate(unittest.TestCase):
    """Tests for syncing a config file with a template."""

    TEMPLATE = """# App settings
debug = false
name = MyApp

# Things to load
parts =
|one
|two

[database]
host = localhost
port = 5432
"""

    def setUp(self):
        QuickIni.parsed_ini = {}
        QuickIni.loaded_file_path = None
        QuickIni.auto_type_convert_g = True
        QuickIni.error_message = ""
        QuickIni.web_file = None
        QuickIni.sync_report = None
        self.dir = tempfile.TemporaryDirectory()
        self.config = os.path.join(self.dir.name, "config.ini")

    def tearDown(self):
        self.dir.cleanup()

    def write(self, name, content):
        path = os.path.join(self.dir.name, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path

    def read(self, path):
        with open(path, encoding='utf-8') as f:
            return f.read()

    # ===== FINDING THE TEMPLATE =====

    def test_missing_config_is_created_from_template(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.assertTrue(QuickIni.load_file(self.config, template=True))
        self.assertEqual(self.read(self.config), self.TEMPLATE)
        self.assertEqual(QuickIni.get_value("port", section="database"), 5432)
        report = QuickIni.get_sync_report()
        self.assertTrue(report["created"])
        self.assertTrue(report["changed"])
        self.assertEqual(report["added"], [])
        self.assertIsNone(report["backup"])

    def test_template_path_given_by_name(self):
        template = self.write("template.ini", self.TEMPLATE)
        self.assertTrue(QuickIni.load_file(self.config, template=template))
        self.assertEqual(self.read(self.config), self.TEMPLATE)

    def test_missing_default_template_is_skipped(self):
        self.write("config.ini", "debug = true\n")
        self.assertTrue(QuickIni.load_file(self.config, template=True))
        self.assertTrue(QuickIni.get_value("debug"))
        self.assertIsNone(QuickIni.get_sync_report())
        self.assertEqual(self.read(self.config), "debug = true\n")

    def test_missing_named_template_fails(self):
        self.write("config.ini", "debug = true\n")
        missing = os.path.join(self.dir.name, "nope.ini")
        self.assertFalse(QuickIni.load_file(self.config, template=missing))
        self.assertIn("Could not find template", QuickIni.get_last_error())

    def test_no_template_by_default(self):
        self.write("config.ini", "debug = true\n")
        self.write("config.ini.template", self.TEMPLATE)
        self.assertTrue(QuickIni.load_file(self.config))
        self.assertEqual(self.read(self.config), "debug = true\n")
        self.assertIsNone(QuickIni.get_sync_report())

    def test_url_config_with_template_fails(self):
        self.assertFalse(QuickIni.load_file("https://example.com/config.ini", template=True))
        self.assertIn("URL", QuickIni.get_last_error())

    # ===== MERGING =====

    def test_user_values_are_kept_and_new_keys_added(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.write("config.ini", "debug=yes   # on for now\n\n[database]\nport = 6000\n")
        self.assertTrue(QuickIni.load_file(self.config, template=True))
        self.assertEqual(self.read(self.config), """# App settings
debug=yes   # on for now
name = MyApp

# Things to load
parts =
|one
|two

[database]
host = localhost
port = 6000
""")
        self.assertTrue(QuickIni.get_value("debug"))
        self.assertEqual(QuickIni.get_value("port", section="database"), 6000)
        report = QuickIni.get_sync_report()
        self.assertEqual(report["added"], ["name", "parts", "database.host"])
        self.assertEqual(report["orphaned"], [])

    def test_user_array_replaces_template_array(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.write("config.ini", "parts =\n|three\n")
        QuickIni.load_file(self.config, template=True)
        self.assertEqual(QuickIni.get_value("parts"), ["three"])
        self.assertNotIn("|one", self.read(self.config))

    def test_user_blank_value_replaces_template_array(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.write("config.ini", "parts =\n")
        QuickIni.load_file(self.config, template=True)
        self.assertIsNone(QuickIni.get_value("parts", "missing"))
        self.assertNotIn("|one", self.read(self.config))

    def test_orphaned_keys_kept_in_their_section(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.write("config.ini", "old = 1\n[database]\nuser = admin\n[cache]\nsize = 10\n")
        self.assertTrue(QuickIni.load_file(self.config, template=True))
        self.assertEqual(QuickIni.get_value("old"), 1)
        self.assertEqual(QuickIni.get_value("user", section="database"), "admin")
        self.assertEqual(QuickIni.get_value("size", section="cache"), 10)
        self.assertEqual(QuickIni.get_sync_report()["orphaned"], ["old", "database.user", "cache.size"])
        text = self.read(self.config)
        self.assertEqual(text.count("# Not in the template"), 3)
        self.assertLess(text.index("old = 1"), text.index("[database]"))

    def test_sync_is_stable(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.write("config.ini", "old = 1\n[database]\nport = 6000\nuser = admin\n[cache]\nsize = 10\n")
        QuickIni.load_file(self.config, template=True)
        first = self.read(self.config)
        os.remove(self.config + ".bak")
        QuickIni.load_file(self.config, template=True)
        self.assertEqual(self.read(self.config), first)
        report = QuickIni.get_sync_report()
        self.assertFalse(report["changed"])
        self.assertEqual(report["added"], [])
        self.assertIsNone(report["backup"])
        self.assertFalse(os.path.exists(self.config + ".bak"))

    def test_backup_holds_previous_config(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.write("config.ini", "debug = true\n")
        QuickIni.load_file(self.config, template=True)
        report = QuickIni.get_sync_report()
        self.assertEqual(report["backup"], os.path.realpath(self.config) + ".bak")
        self.assertEqual(self.read(report["backup"]), "debug = true\n")

    def test_template_comments_win(self):
        self.write("config.ini.template", "# new comment\ndebug = false\n")
        self.write("config.ini", "# my own comment\ndebug = true\n")
        QuickIni.load_file(self.config, template=True)
        self.assertEqual(self.read(self.config), "# new comment\ndebug = true\n")

    def test_sync_template_without_loading(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.assertTrue(QuickIni.sync_template(self.config))
        self.assertTrue(os.path.exists(self.config))
        self.assertEqual(QuickIni.parsed_ini, {})

    def test_failed_sync_write_keeps_original(self):
        self.write("config.ini.template", self.TEMPLATE)
        self.write("config.ini", "debug = true\n")
        with patch('os.replace', side_effect=PermissionError("denied")):
            self.assertFalse(QuickIni.load_file(self.config, template=True))
        self.assertIn("Could not write synced config", QuickIni.get_last_error())
        self.assertEqual(self.read(self.config), "debug = true\n")
        self.assertEqual(os.listdir(self.dir.name).count("config.ini"), 1)
        self.assertFalse(any(name.endswith(".tmp") for name in os.listdir(self.dir.name)))


if __name__ == '__main__':
    unittest.main()