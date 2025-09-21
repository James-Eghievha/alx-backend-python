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

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """Test that public_repos returns expected list of repositories.
        
        This test verifies that:
        1. public_repos returns the correct list of repository names
        2. get_json is called exactly once with the mocked URL
        3. _public_repos_url property is accessed to get the URL
        4. The method correctly extracts repo names from the API payload
        
        Uses dual mocking approach:
        - @patch decorator to mock get_json (avoid HTTP requests)
        - patch context manager to mock _public_repos_url (control URL)
        """
        # Create test payload that mimics GitHub API response structure
        test_payload = [
            {
                "id": 7697149,
                "name": "episodes.dart",
                "full_name": "google/episodes.dart",
                "description": "A framework for timing performance of web apps.",
                "language": "Dart",
                "license": {
                    "key": "bsd-3-clause",
                    "name": "BSD 3-Clause \"New\" or \"Revised\" License"
                }
            },
            {
                "id": 8566972,
                "name": "kratu",
                "full_name": "google/kratu", 
                "description": "Data visualization framework",
                "language": "JavaScript",
                "license": {
                    "key": "apache-2.0",
                    "name": "Apache License 2.0"
                }
            },
            {
                "id": 9060347,
                "name": "traceur-compiler",
                "full_name": "google/traceur-compiler",
                "description": "Traceur is a JavaScript.next-to-JavaScript-of-today compiler",
                "language": "JavaScript",
                "license": {
                    "key": "apache-2.0", 
                    "name": "Apache License 2.0"
                }
            }
        ]
        
        # Expected result: just the repository names
        expected_repos = ["episodes.dart", "kratu", "traceur-compiler"]
        
        # Configure mock_get_json to return our test payload
        mock_get_json.return_value = test_payload
        
        # Test URL that we expect _public_repos_url to return
        test_repos_url = "https://api.github.com/orgs/google/repos"
        
        # Create client and use context manager to mock _public_repos_url
        client = GithubOrgClient("google")
        
        with patch.object(client, '_public_repos_url', return_value=test_repos_url) as mock_repos_url:
            # Call the method we're testing
            result = client.public_repos()
            
            # Verify the result contains expected repository names
            self.assertEqual(result, expected_repos)
            
            # Verify _public_repos_url property was accessed once
            mock_repos_url.assert_called_once()
            
        # Verify get_json was called once with the mocked URL
        mock_get_json.assert_called_once_with(test_repos_url)

    @parameterized.expand([
        # Test case 1: License key matches - should return True
        ({"license": {"key": "my_license"}}, "my_license", True),
        
        # Test case 2: License key doesn't match - should return False
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, expected):
        """Test that has_license correctly identifies repository license status.
        
        This test verifies the static method's ability to:
        1. Access nested license information from repository data
        2. Compare license keys correctly
        3. Return appropriate boolean values for match/no-match scenarios
        
        No mocking required since this tests pure logic without external dependencies.
        
        Parameters:
        -----------
        repo: Dict
            Repository data structure containing license information
        license_key: str  
            The license key to check for
        expected: bool
            Expected return value (True for match, False for no match)
        """
        # Call the static method directly on the class
        result = GithubOrgClient.has_license(repo, license_key)
        
        # Verify the result matches expected boolean value
        self.assertEqual(result, expected)


if __name__ == '__main__':
    # This runs our tests when we execute the file directly
    unittest.main()
