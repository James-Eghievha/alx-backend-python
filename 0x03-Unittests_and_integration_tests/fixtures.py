#!/usr/bin/env python3

# Organization payload fixture
org_payload = {"repos_url": "https://api.github.com/orgs/google/repos"}

# Repository list payload fixture
repos_payload = [
  {
    "id": 7697149,
    "name": "episodes.dart",
    "full_name": "google/episodes.dart",
    "private": False,
    "description": "A framework for timing performance of web apps.",
    "language": "Dart",
    "license": {
      "key": "bsd-3-clause",
      "name": "BSD 3-Clause \"New\" or \"Revised\" License"
    }
  },
  {
    "id": 7776515,
    "name": "cpp-netlib",
    "full_name": "google/cpp-netlib",
    "private": False,
    "description": "The C++ Network Library Project",
    "language": "C++",
    "license": {
      "key": "bsl-1.0",
      "name": "Boost Software License 1.0"
    }
  },
  {
    "id": 7968417,
    "name": "dagger",
    "full_name": "google/dagger",
    "private": False,
    "description": "A fast dependency injector for Android and Java.",
    "language": "Java",
    "license": {
      "key": "apache-2.0",
      "name": "Apache License 2.0"
    }
  },
  {
    "id": 8165161,
    "name": "ios-webkit-debug-proxy",
    "full_name": "google/ios-webkit-debug-proxy",
    "private": False,
    "description": "A DevTools proxy for iOS devices",
    "language": "C",
    "license": {
      "key": "other",
      "name": "Other"
    }
  },
  {
    "id": 8566972,
    "name": "kratu",
    "full_name": "google/kratu",
    "private": False,
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
    "private": False,
    "description": "Traceur is a JavaScript.next-to-JavaScript-of-today compiler",
    "language": "JavaScript",
    "license": {
      "key": "apache-2.0",
      "name": "Apache License 2.0"
    }
  }
]

# Expected repository names
expected_repos = [
  "episodes.dart",
  "cpp-netlib", 
  "dagger",
  "ios-webkit-debug-proxy",
  "kratu",
  "traceur-compiler"
]

# Apache 2.0 licensed repositories only
apache2_repos = [
  "dagger",
  "kratu", 
  "traceur-compiler"
]

# Test payload tuple for parameterized_class
TEST_PAYLOAD = (org_payload, repos_payload, expected_repos, apache2_repos)
