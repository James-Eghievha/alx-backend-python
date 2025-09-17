# 0x03. Unittests and Integration Tests

This project focuses on learning unit testing and integration testing in Python using the `unittest` module.

## Learning Objectives

By the end of this project, you will understand:
- The difference between unit and integration tests
- Common testing patterns: mocking, parametrizations, and fixtures
- How to write comprehensive test suites for Python applications

## Project Structure

```
alx-backend-python/0x03-Unittests_and_integration_tests/
├── README.md
├── utils.py              # Utility functions to be tested
├── client.py            # GitHub API client
├── fixtures.py          # Test data and fixtures
├── test_utils.py        # Unit tests for utils.py
├── test_client.py       # Unit and integration tests for client.py
└── requirements.txt     # Project dependencies
```

## Files Description

### `utils.py`
Contains utility functions:
- `access_nested_map`: Navigate through nested dictionaries using a path
- `get_json`: Fetch JSON data from a URL
- `memoize`: Decorator for caching method results

### `client.py` 
GitHub organization client that uses the utility functions to interact with GitHub's API.

### `fixtures.py`
Test data used in integration tests - contains sample GitHub API responses.

### `test_utils.py`
Unit tests for the utility functions, focusing on:
- Testing `access_nested_map` with various inputs
- Testing exception handling
- Using parameterized tests

## Key Testing Concepts Learned

### Unit Tests
- Test individual functions in isolation
- Fast and focused
- Use mocks to avoid external dependencies

### Integration Tests  
- Test multiple components working together
- Test real API interactions
- Verify end-to-end workflows

### Testing Patterns
- **Parametrized Tests**: Run the same test with different inputs
- **Mocking**: Replace external dependencies with controlled fake objects
- **Fixtures**: Provide consistent test data

## Requirements

- Ubuntu 18.04 LTS
- Python 3.7
- All files must be executable
- Code must follow pycodestyle (version 2.5)
- All modules, classes, and functions must have documentation
- All functions must be type-annotated

## Dependencies

```bash
pip install parameterized requests
```

## Running Tests

```bash
# Run all tests
python -m unittest discover

# Run specific test file
python -m unittest test_utils

# Run with verbose output
python -m unittest -v test_utils.TestAccessNestedMap.test_access_nested_map
```

## Example Test Execution

```bash
$ python -m unittest test_utils.TestAccessNestedMap.test_access_nested_map
...
----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK
```

## Understanding the Test Structure

Each test follows this pattern:

```python
@parameterized.expand([
    (input_data, expected_output),
    # More test cases...
])
def test_function_name(self, input_data, expected_output):
    result = function_to_test(input_data)
    self.assertEqual(result, expected_output)
```

This approach allows testing multiple scenarios with clean, readable code.
