#!/usr/bin/env python3
"""Unit tests for utils module.

This is like being a quality inspector for our treasure hunting tools!
We need to make sure our access_nested_map function works perfectly
in all situations before we trust it with real treasure hunts.
"""

import unittest
from parameterized import parameterized
from utils import access_nested_map


class TestAccessNestedMap(unittest.TestCase):
    """Test the access_nested_map function.
    
    Think of this class as our "Testing Laboratory" where we verify
    our treasure hunting tool works correctly!
    """
    
    @parameterized.expand([
        # Test case 1: Simple treasure chest (one level deep)
        # Like opening a single chest to find gold
        ({"a": 1}, ("a",), 1),
        
        # Test case 2: Chest within chest, but only opening outer chest  
        # Like opening the first chest and finding another chest inside
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        
        # Test case 3: Deep treasure hunting (two levels deep)
        # Like opening first chest, then second chest, and finding treasure
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(self, nested_map, path, expected):
        """Test that access_nested_map returns correct treasure for given path.
        
        Parameters:
        -----------
        nested_map: dict
            Our treasure map (the nested dictionary)
        path: tuple  
            The path to follow (sequence of keys)
        expected: any
            What treasure we expect to find
        """
        # This is our actual test - only 2 lines as required!
        result = access_nested_map(nested_map, path)
        self.assertEqual(result, expected)
    
    @parameterized.expand([
        # Test case 1: Empty treasure room - looking for chest "a" that doesn't exist
        # Like searching for a specific chest in an empty room
        ({}, ("a",), "a"),
        
        # Test case 2: Wrong treasure type - trying to open a gold coin as a chest
        # Like trying to use a gold coin (value 1) as another treasure map
        ({"a": 1}, ("a", "b"), "b"),
    ])
    def test_access_nested_map_exception(self, nested_map, path, expected_key):
        """Test that access_nested_map raises KeyError with correct message.
        
        This tests our "safety mechanisms" - making sure the function
        fails properly and tells us exactly what went wrong.
        
        Parameters:
        -----------
        nested_map: dict
            Our treasure map (the nested dictionary)
        path: tuple  
            The path to follow that should cause an error
        expected_key: str
            The key that should be mentioned in the error message
        """
        # Test that KeyError is raised and check the error message
        with self.assertRaises(KeyError) as context:
            access_nested_map(nested_map, path)
        self.assertEqual(str(context.exception), f"'{expected_key}'")


if __name__ == '__main__':
    # This runs our tests when we execute the file directly
    unittest.main()
