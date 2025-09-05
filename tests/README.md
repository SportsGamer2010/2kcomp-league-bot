# Testing Guide for 2KCompLeague Discord Bot

This directory contains comprehensive unit tests for the Discord bot's core functionality.

## 🧪 Test Coverage

### Core Modules Tested

- **`test_records.py`** - Single game records functionality
  - Record candidate creation and validation
  - Record update logic (`_try_update_max`)
  - Records computation from events
  - Discord embed formatting
  - Record change detection
  - Seed data loading

- **`test_leaders.py`** - Season and career leaders functionality
  - Player stats aggregation
  - Leader sorting and ranking
  - Season leaders computation
  - Career leaders computation
  - Discord embed formatting

- **`test_types.py`** - Data type validation
  - Pydantic model creation
  - Default value handling
  - Data validation edge cases
  - Type conversion (int to float)

## 🚀 Running Tests

### Prerequisites

Install the required testing dependencies:

```bash
pip install pytest pytest-asyncio
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### Running All Tests

```bash
# From the project root directory
python run_tests.py

# Or directly with pytest
pytest tests/ -v
```

### Running Specific Test Files

```bash
# Test only records functionality
pytest tests/test_records.py -v

# Test only leaders functionality
pytest tests/test_leaders.py -v

# Test only data types
pytest tests/test_types.py -v
```

### Running Specific Test Classes

```bash
# Test only record candidate functionality
pytest tests/test_records.py::TestRecordCandidate -v

# Test only record update logic
pytest tests/test_records.py::TestTryUpdateMax -v

# Test only leaders aggregation
pytest tests/test_leaders.py::TestAggregatePlayerStats -v
```

### Running Specific Test Methods

```bash
# Test specific record update scenario
pytest tests/test_records.py::TestTryUpdateMax::test_update_max_with_higher_value -v

# Test specific leaders computation
pytest tests/test_leaders.py::TestComputeSeasonLeaders::test_compute_season_leaders_success -v
```

### Running Tests with Coverage

```bash
# Install coverage tools
pip install pytest-cov

# Run tests with coverage report
python run_tests.py coverage

# Or directly with pytest
pytest tests/ --cov=core --cov-report=term-missing --cov-report=html
```

## 📊 Test Structure

### Fixtures and Mocks

The tests use pytest fixtures and unittest.mock to provide:

- **Sample data** - Realistic test data for all data types
- **Mock HTTP client** - Simulated HTTP responses
- **Mock settings** - Configuration values for testing
- **Mock API responses** - Simulated SportsPress API data

### Test Categories

#### Unit Tests
- Individual function testing
- Data model validation
- Edge case handling
- Error condition testing

#### Integration Tests
- End-to-end workflow testing
- API integration simulation
- Data flow validation

#### Edge Case Tests
- Empty data handling
- Invalid input handling
- Error recovery testing
- Boundary condition testing

## 🔍 Test Data

### Sample Records Data

```python
# Example of test records data
records = RecordsData(
    points=SingleGameRecord(
        stat="points",
        value=45.0,
        holder="Player1",
        game="Game1",
        date="2024-01-15"
    ),
    rebounds=SingleGameRecord(
        stat="rebounds",
        value=15.0,
        holder="Player2",
        game="Game2",
        date="2024-01-16"
    )
)
```

### Sample Events Data

```python
# Example of test events data
events = [
    {
        "id": 1,
        "date": "2024-01-15",
        "title": "Team A vs Team B",
        "results": {
            "boxscore": [
                {
                    "name": "Player1",
                    "pts": 45.0,
                    "rebtwo": 12.0,
                    "ast": 8.0,
                    # ... more stats
                }
            ]
        }
    }
]
```

## 🛠️ Test Configuration

### pytest.ini

The project includes a `pytest.ini` file with:

- Test discovery patterns
- Verbose output settings
- Async test configuration
- Custom markers for test categorization

### conftest.py

Shared fixtures and configuration in `conftest.py`:

- Common test data fixtures
- Mock objects
- Helper functions
- Test utilities

## 📝 Writing New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<description>`

### Example Test Structure

```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_feature_creation(self):
        """Test creating a new feature."""
        # Arrange
        input_data = "test"
        
        # Act
        result = create_feature(input_data)
        
        # Assert
        assert result is not None
        assert result.value == input_data
```

### Adding New Fixtures

Add new fixtures to `conftest.py`:

```python
@pytest.fixture
def new_test_data():
    """Provide new test data for tests."""
    return {
        "key": "value",
        "number": 42
    }
```

## 🚨 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running tests from the project root
2. **Mock Issues**: Check that mocks are properly configured
3. **Async Test Errors**: Verify pytest-asyncio is installed and configured

### Debug Mode

Run tests with more verbose output:

```bash
pytest tests/ -v -s --tb=long
```

### Test Isolation

Run tests in isolation to identify issues:

```bash
# Run one test at a time
pytest tests/test_records.py::TestRecordCandidate::test_record_candidate_creation -v
```

## 📈 Continuous Integration

The test suite is designed to work with CI/CD pipelines:

- Fast execution (< 30 seconds for full suite)
- Deterministic results
- Proper error reporting
- Coverage reporting
- Mock-based isolation

## 🤝 Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain test coverage above 90%
4. Add appropriate test documentation
5. Update this README if needed

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Pydantic Testing](https://pydantic-docs.helpmanual.io/usage/testing/)
