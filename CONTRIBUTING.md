# Contributing to Vendor API Specification Generator

Thank you for considering contributing to this project! We welcome contributions from the community.

## ⚠️ Contributor Acknowledgment

By contributing to this project, you acknowledge and agree that:
- This is **experimental software** for informational purposes only
- You have read and understood the [DISCLAIMER.md](DISCLAIMER.md)
- Your contributions are provided under the MIT License
- You accept that the software comes with **NO WARRANTY** and **NO LIABILITY**
- The project authors are not responsible for any trading losses or damages

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Adding a New Vendor](#adding-a-new-vendor)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/crypto-exchange-api-catalog.git
   cd crypto-exchange-api-catalog
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 main.py init

# Run discovery to test
python3 main.py discover --vendor coinbase
```

## Adding a New Vendor

To add support for a new exchange (e.g., Binance, Kraken):

### 1. Use Adapter Template

Start with our comprehensive adapter template:

```bash
cp src/adapters/template_adapter.py src/adapters/new_vendor_adapter.py
```

Then edit `src/adapters/new_vendor_adapter.py`:

1. **Rename the class** from `TemplateAdapter` to `NewVendorAdapter`
2. **Update all placeholders**:
   - `[EXCHANGE_NAME]` → Your exchange name (e.g., "Bybit", "OKX")
   - `[BASE_URL]` → Actual REST API base URL (e.g., "https://api.bybit.com")
   - `[WEBSOCKET_URL]` → Actual WebSocket URL (e.g., "wss://stream.bybit.com")
3. **Implement the three required methods** based on the exchange's API documentation
4. **Update documentation URLs** and endpoint patterns

The template includes:
- Complete structure for all three required methods (`discover_rest_endpoints()`, `discover_websocket_channels()`, `discover_products()`)
- Examples of common endpoint patterns and WebSocket channel formats
- Helper methods for candle intervals and validation
- Comprehensive error handling and logging patterns
- Placeholders for authenticated endpoints (Phase 3)
- Extensive inline documentation and implementation guidance

**Important**: The `discover_products()` method MUST make live API calls to fetch actual products. Do not hardcode products. The template provides examples for parsing different exchange response formats.

### 2. Add Vendor Configuration

In `config/settings.py`, add vendor configuration:

```python
VENDORS = {
    # ... existing vendors ...
    
    "newvendor": {
        "enabled": True,
        "display_name": "NewVendor Exchange",
        "base_url": "https://api.newvendor.com",
        "websocket_url": "wss://stream.newvendor.com",
        "documentation_url": "https://newvendor-docs.github.io/apidocs/",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "exchange_info": "/api/v3/exchangeInfo",
            "time": "/api/v3/time"
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False
        }
    }
}
```

**Note on Regional Endpoints:** Some exchanges have different endpoints by region (e.g., Binance.com vs Binance.US). Choose the endpoint that works for your primary user base. Document regional alternatives in the README with instructions on how to modify `config/settings.py` for different regions.

### 3. Register Adapter

In `src/discovery/spec_generator.py`, add to `_create_adapter()`:

```python
def _create_adapter(self, vendor_name: str, vendor_config: Dict[str, Any]) -> BaseVendorAdapter:
    if vendor_name == 'coinbase':
        return CoinbaseAdapter(vendor_config)
    elif vendor_name == 'newvendor':
        return NewVendorAdapter(vendor_config)
    else:
        raise ValueError(f"Unknown vendor: {vendor_name}")
```

### 4. Test Your Adapter

```bash
# Discover API
python3 main.py discover --vendor newvendor

# Export specification
python3 main.py export --vendor newvendor --format snake_case

# Verify in database
python3 main.py query "SELECT * FROM products WHERE vendor_id = (SELECT vendor_id FROM vendors WHERE vendor_name = 'newvendor')"
```

## Code Style Guidelines

### General Principles

1. **Function Length**: Keep functions under 50 lines
2. **Docstrings**: Every function must have a docstring
3. **File Headers**: First line of each file should be a comment with the filename
4. **PEP8 Compliance**: Follow Python PEP8 style guide
5. **Type Hints**: Use type hints where appropriate

### Example

```python
# src/utils/example.py
"""
Example utility module.
"""

from typing import List, Dict


def process_data(items: List[Dict]) -> List[Dict]:
    """
    Process list of items and return filtered results.
    
    Args:
        items: List of item dictionaries
        
    Returns:
        Filtered list of items
        
    Raises:
        ValueError: If items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    
    # Process items
    filtered = [item for item in items if item.get('status') == 'active']
    
    return filtered
```

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Imports

```python
# Standard library imports first
import json
import logging
from typing import Dict, List

# Third-party imports
import requests

# Local imports
from config.settings import DATABASE_PATH
from src.utils.logger import get_logger
```

## Testing

### Manual Testing

```bash
# Test discovery
python3 main.py discover --vendor coinbase

# Test export
python3 main.py export --vendor coinbase --format snake_case

# Test queries
python3 main.py query "SELECT COUNT(*) FROM products"
```

### Before Submitting

- [ ] All functions have docstrings
- [ ] Code follows PEP8 guidelines
- [ ] Functions are under 50 lines
- [ ] No hardcoded values (use configuration)
- [ ] Error handling implemented
- [ ] Logging added for key operations
- [ ] Tested manually with real API

## Submitting Changes

### Pull Request Process

1. **Update documentation** if you've added features
2. **Test thoroughly** with actual vendor APIs
3. **Commit with clear messages**:
   ```bash
   git commit -m "feat: Add Binance adapter with 15 REST endpoints"
   ```
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Create Pull Request** on GitHub
6. **Describe your changes** in the PR description:
   - What was added/changed
   - Why it was needed
   - How to test it
   - Screenshots/output (if applicable)

### Commit Message Format

```
<type>: <subject>

<body>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Example:**
```
feat: Add Binance adapter with WebSocket support

- Implemented BinanceAdapter with 15 REST endpoints
- Added WebSocket channel discovery for 8 channels
- Tested with live API, discovered 1,200+ products
- Updated configuration in settings.py
```

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: 
   ```bash
   python3 main.py discover --vendor coinbase
   # Error occurs at...
   ```
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happened
5. **Environment**:
   - OS: Ubuntu 22.04
   - Python version: 3.10.12
   - Dependencies: `pip freeze`
6. **Logs**: Include relevant log output from `api_spec_generator.log`

### Feature Requests

When suggesting features:

1. **Use Case**: Describe the problem you're trying to solve
2. **Proposed Solution**: How you'd like it to work
3. **Alternatives**: Other solutions you've considered
4. **Additional Context**: Any other relevant information

## Questions?

- **Issues**: https://github.com/jsoprych/crypto-exchange-api-catalog/issues
- **Discussions**: https://github.com/jsoprych/crypto-exchange-api-catalog/discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Vendor API Specification Generator!** 🚀

Built by [John Soprych](https://github.com/jsoprych) / [Elko.AI](https://elko.ai)
