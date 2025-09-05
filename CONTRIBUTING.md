# Contributing to 2KCompLeague Discord Bot

Thank you for your interest in contributing to the 2KCompLeague Discord Bot! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.11+
- Docker (optional, for containerized development)
- Git
- Discord Bot Token (for testing)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/2kcomp-league-bot.git
   cd 2kcomp-league-bot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Environment Setup**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep functions small and focused
- Add docstrings for all public functions

### Testing
- Write tests for new features
- Ensure all tests pass before submitting
- Aim for good test coverage

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov=cogs
```

### Commit Messages
Use clear, descriptive commit messages:

```
feat: add new /player command with detailed stats
fix: resolve timeout issue in /records command
docs: update deployment guide with Docker instructions
```

## Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation if needed

3. **Test Changes**
   ```bash
   # Run tests
   pytest tests/ -v
   
   # Test with Docker (optional)
   docker-compose up -d
   ```

4. **Submit Pull Request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

## Project Structure

```
discord-bot/
├── cogs/                 # Discord bot command modules
├── core/                 # Core functionality and utilities
├── data/                 # Persistent data storage
├── tests/                # Test files
├── scripts/              # Utility scripts
├── monitoring/           # Monitoring configuration
├── bot.py               # Main bot entry point
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
└── Dockerfile          # Docker configuration
```

## Command Categories

### Core Commands
- `/league` - League information
- `/standings` - Current standings
- `/player` - Player statistics
- `/records` - All-time records

### Admin Commands
- `/admin-announce` - Send announcements
- `/admin-sync` - Sync commands
- `/admin-status` - Bot status

### Achievement Commands
- `/doubledoubles` - Double-double records
- `/tripledoubles` - Triple-double records
- `/milestones` - Career milestones

## Adding New Features

### New Commands
1. Create new cog in `cogs/` directory
2. Follow existing patterns for command structure
3. Add proper error handling and logging
4. Include tests for new functionality

### New Core Features
1. Add functionality to appropriate `core/` module
2. Use type hints and proper documentation
3. Add comprehensive tests
4. Update configuration if needed

## Bug Reports

When reporting bugs, please include:
- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Relevant log output

## Feature Requests

For feature requests:
- Describe the feature clearly
- Explain the use case
- Consider implementation complexity
- Check for existing similar features

## Code Review

All submissions require review. Reviewers will check:
- Code quality and style
- Test coverage
- Documentation updates
- Security considerations
- Performance impact

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag
4. Deploy to production

## Contact

- GitHub Issues: For bugs and feature requests
- Discord: For community discussion
- Email: For security issues

Thank you for contributing to the 2KCompLeague Discord Bot!
