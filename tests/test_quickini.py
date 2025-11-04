import unittest
import tempfile
import os
from quick_ini import QuickIni


class TestQuickIni(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary INI file for testing
        self.test_content = """# Test configuration
debug=true
port=8080
timeout=30.5
name=TestApp
empty_value=

# Array example
parts=
|one
|two
|three
"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_load_file(self):
        """Test loading an INI file."""
        result = QuickIni.load_file(self.temp_file.name)
        self.assertTrue(result)
        
    def test_get_value_string(self):
        """Test getting string values."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("name")
        self.assertEqual(value, "TestApp")
        
    def test_get_value_boolean(self):
        """Test getting boolean values."""
        QuickIni.load_file(self.temp_file.name)
        value = QuickIni.get_value("debug")
        self.assertTrue(value)
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
        
    def test_write_value(self):
        """Test writing values to file."""
        QuickIni.load_file(self.temp_file.name)
        result = QuickIni.write_value("new_key", "new_value", add_if_not_found=True)
        self.assertEqual(result, "new_value")
        
        # Verify it was written
        value = QuickIni.get_value("new_key")
        self.assertEqual(value, "new_value")
        
    def test_get_array_value(self):
        """Test getting array values."""
        QuickIni.load_file(self.temp_file.name)
        parts = QuickIni.get_value("parts")
        self.assertEqual(parts, ["one", "two", "three"])
        self.assertIsInstance(parts, list)
        
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
        
    def test_array_type_conversion(self):
        """Test type conversion in arrays."""
        QuickIni.load_file(self.temp_file.name)
        mixed_array = ["text", 42, 3.14, True]
        QuickIni.write_value("mixed", mixed_array, add_if_not_found=True)
        
        # Reload to test parsing
        QuickIni.load_file(self.temp_file.name)
        mixed = QuickIni.get_value("mixed")
        self.assertEqual(mixed[0], "text")
        self.assertEqual(mixed[1], 42)
        self.assertEqual(mixed[2], 3.14)
        self.assertEqual(mixed[3], True)
        
    def test_error_handling(self):
        """Test error handling for missing files."""
        result = QuickIni.load_file("nonexistent_file.ini")
        self.assertFalse(result)
        error = QuickIni.get_last_error()
        self.assertIn("Could not find file", error)


if __name__ == '__main__':
    unittest.main()