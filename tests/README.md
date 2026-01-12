# Tests

## Running Tests

To run the tests, first install the dependencies:

```bash
pip install -r requirements.txt
```

Then run the tests:

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.test_basic

# Run with verbose output
python -m unittest tests.test_basic -v
```

## Test Coverage

The test suite includes:

1. **Configuration Tests**: Verify config module works correctly
2. **Parser Tests**: Test HTML parsing and data extraction
3. **Database Tests**: Test database module initialization

## Adding New Tests

When adding new functionality, please add corresponding tests:

1. Create test files in the `tests/` directory
2. Name test files with `test_` prefix
3. Use descriptive test names
4. Include docstrings

Example:

```python
import unittest

class TestNewFeature(unittest.TestCase):
    def test_feature_works(self):
        """Test that new feature works as expected"""
        # Your test code here
        self.assertTrue(True)
```

## Integration Tests

For integration tests that require database and browser:

1. Ensure MySQL is running
2. Ensure Redis is running (for Celery tests)
3. Set test environment variables
4. Run tests in isolation

Note: Some tests may be skipped if required services are not available.
