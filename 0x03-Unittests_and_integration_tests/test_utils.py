#!/usr/bin/env python3
"""Unit tests for client module.

This module tests the GithubOrgClient class to ensure it properly
interacts with the GitHub API through our utility functions.
We focus on testing the integration between the client and its dependencies
while avoiding actual network requests.
"""

import unittest
from unittest.mock import patch
from parameterized import parameterized
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """Test the GithubOrgClient class.
    
    This class tests our GitHub API client to ensure it correctly
    constructs API requests and processes responses without making
    actual HTTP calls to GitHub.
    """
    
    @parameterized.expand([
        # Test case 1: Google organization
        ("google",),
        
        # Test case 2: ABC organization  
        ("abc",),
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test that GithubOrgClient.org returns correct value and calls get_json properly.
        
        This test verifies that:
        1. The org property returns the data from get_json
        2. get_json is called exactly once with the correct GitHub API URL
        3. The URL is properly constructed using the organization name
        4. No actual HTTP requests are made (mocking ensures this)
        
        Parameters:
        -----------
        org_name: str
            The GitHub organization name to test with
        mock_get_json: Mock
            The mocked get_json function (injected by @patch)
        """
        # Configure the mock to return test organization data
        test_org_data = {
            "login": org_name,
            "id": 12345,
            "url": f"https://api.github.com/orgs/{org_name}",
            "repos_url": f"https://api.github.com/orgs/{org_name}/repos"
        }
        mock_get_json.return_value = test_org_data
        
        # Create a client instance with the test organization name
        client = GithubOrgClient(org_name)
        
        # Access the org property (this should trigger the get_json call)
        result = client.org
        
        # Verify that get_json was called exactly once with the correct URL
        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.assert_called_once_with(expected_url)
        
        # Verify that the org property returns the expected data
        self.assertEqual(result, test_org_data)


if __name__ == '__main__':
    # This runs our tests when we execute the file directly
    unittest.main()
