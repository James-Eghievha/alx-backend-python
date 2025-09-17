#!/usr/bin/env python3
"""Unit tests for utils module.
"""

import unittest
from parameterized import parameterized
from utils import access_nested_map


class TestAccessNestedMap(unittest.TestCase):
    """Test the access_nested_map function.
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


if __name__ == '__main__':
    # This runs our tests when we execute the file directly
    unittest.main()
