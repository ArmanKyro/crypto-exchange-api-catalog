# Exchange Integration Checklist

## 📋 Quick Copy Template
Copy this file to `{exchange_name}_CHECKLIST.md` and fill in exchange-specific details.

## 🎯 Exchange: [Exchange Name]
**Priority**: [High/Medium/Low]  
**Status**: [Not started / In progress / Testing / Complete]
**API Docs**: [URL]
**Base URL**: [REST API base URL]
**WebSocket URL**: [WebSocket URL]
**US Access**: [Yes/No/Restricted]
**Special Notes**: [Any unique features, restrictions, or patterns]

## 📊 Implementation Status
- [ ] **Research Complete** - API docs reviewed
- [ ] **Configuration Added** - settings.py updated
- [ ] **Adapter Created** - adapter file written
- [ ] **Adapter Registered** - spec_generator.py updated
- [ ] **Discovery Tested** - live API tested
- [ ] **Mappings Created** - field mappings done
- [ ] **Coverage Verified** - >50% coverage achieved
- [ ] **Documentation Updated** - TODO list updated

## 🔍 Phase 1: Research & Planning (1-2 hours)

### API Documentation Review
- [ ] **Public REST Endpoints**: Identify key endpoints:
  - Products/symbols endpoint: `[ENDPOINT]`
  - Time endpoint: `[ENDPOINT]`
  - Ticker endpoint: `[ENDPOINT]`
  - Order book endpoint: `[ENDPOINT]`
  - Trades endpoint: `[ENDPOINT]`
  - Candles endpoint: `[ENDPOINT]`

- [ ] **WebSocket Channels**: Identify available channels:
  - Ticker channel format: `[FORMAT]`
  - Order book channel format: `[FORMAT]`
  - Trades channel format: `[FORMAT]`
  - Candles channel format: `[FORMAT]`

- [ ] **Rate Limits**:
  - Public REST: `[REQUESTS/SECOND]`
  - WebSocket: `[CONNECTIONS/SUBSCRIPTIONS]`

- [ ] **API Response Format**:
  - Success pattern: `[e.g., {"code": "00000", "data": ...}]`
  - Error pattern: `[e.g., {"code": "40001", "msg": "..."}]`
  - Product status mapping: `[online → active, offline → inactive]`

- [ ] **Product Discovery**:
  - Endpoint: `[FULL_URL]`
  - Response structure: `[DESCRIBE_STRUCTURE]`
  - Status field name: `[FIELD_NAME]`
  - Status values: `[online, offline, etc.]`

## ⚙️ Phase 2: Configuration (15-30 minutes)

### 1. Add to `config/settings.py`
```python
    "{exchange_name}": {
        "enabled": True,
        "display_name": "{Exchange Name} Exchange",
        "base_url": "{BASE_URL}",
        "websocket_url": "{WS_URL}",
        "documentation_url": "{DOCS_URL}",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "{PRODUCTS_ENDPOINT}",
            "time": "{TIME_ENDPOINT}",
            "tickers": "{TICKER_ENDPOINT}"
        },
        "rate_limits": {
            "public": 20  # UPDATE with actual rate limit
        },
        "authentication": {
            "public_endpoints": True,
            "requires_api_key": False
        }
    }
```

### 2. Create Adapter File
```bash
# Use template (recommended)
cp src/adapters/template_adapter.py src/adapters/{exchange_name}_adapter.py

# Or use automation script
python add_exchange.py --name {exchange_name} \
  --base-url {BASE_URL} \
  --ws-url {WS_URL} \
  --docs {DOCS_URL} \
  --product-endpoint {PRODUCTS_ENDPOINT}
```

### 3. Update `src/discovery/spec_generator.py`
- [ ] Add import: `from src.adapters.{exchange_name}_adapter import {ExchangeName}Adapter`
- [ ] Add to `_create_adapter()` method:
```python
elif vendor_name == '{exchange_name}':
    return {ExchangeName}Adapter(vendor_config)
```
- [ ] Add to `_link_product_feeds()` method (call to `_link_{exchange_name}_feeds`)
- [ ] Add `_link_{exchange_name}_feeds()` method stub at end of file

## 💻 Phase 3: Adapter Implementation (2-4 hours)

### File: `src/adapters/{exchange_name}_adapter.py`

#### 1. Update Class Documentation
- [ ] Update docstring with exchange-specific details
- [ ] Update rate limits, URLs, features

#### 2. Implement `discover_rest_endpoints()`
- [ ] Add 5-10 core public endpoints
- [ ] Include response schemas based on API documentation
- [ ] Set `authentication_required: False` for public endpoints
- [ ] Include path/query parameters

#### 3. Implement `discover_websocket_channels()`
- [ ] Add ticker, order book, trades, candles channels
- [ ] Define subscribe/unsubscribe formats
- [ ] Document message schemas
- [ ] Set `authentication_required: False` for public channels

#### 4. Implement `discover_products()`
- [ ] **CRITICAL**: Make actual API call to fetch products
- [ ] Parse response to extract symbols
- [ ] Map status values to standard (`online` → `active`)
- [ ] Handle error cases gracefully
- [ ] Include vendor_metadata with raw data

**Implementation Pattern Examples:**

```python
# REST endpoints pattern
endpoints.append({
    "path": "/api/path",
    "method": "GET",
    "authentication_required": False,
    "description": "Description",
    "query_parameters": {...},
    "response_schema": {...}
})

# WebSocket channels pattern
channels.append({
    "channel_name": "ticker",
    "authentication_required": False,
    "description": "Real-time ticker updates",
    "subscribe_format": {...},
    "message_schema": {...}
})

# Product discovery pattern
response = self.http_client.get(products_url)
for symbol_info in response['data']:
    product = {
        "symbol": symbol_info['symbol'],
        "base_currency": symbol_info['baseCoin'],
        "quote_currency": symbol_info['quoteCoin'],
        "status": "online" if symbol_info['status'] == 'online' else 'offline',
        "vendor_metadata": symbol_info
    }
```

## 🧪 Phase 4: Testing & Validation (1-2 hours)

### 1. Initial Discovery Test
```bash
# Test adapter creation
python3 main.py discover --vendor {exchange_name}
```

**Expected Results**:
- [ ] No syntax errors
- [ ] Products discovered (> 0)
- [ ] Endpoints saved to database
- [ ] WebSocket channels saved to database

**Troubleshooting**:
- **400 Bad Request**: Check base URL and endpoint paths
- **No products**: Verify product endpoint URL and response parsing
- **Import errors**: Check class name matches filename

### 2. Database Verification
```bash
# Check products were saved
python3 main.py query "SELECT COUNT(*) FROM products WHERE vendor_id = (SELECT vendor_id FROM vendors WHERE vendor_name = '{exchange_name}')"

# Check endpoints
python3 main.py query "SELECT method, path FROM rest_endpoints WHERE vendor_id = (SELECT vendor_id FROM vendors WHERE vendor_name = '{exchange_name}')"
```

### 3. Create Field Mappings
```bash
# Create mapping script (if needed)
cp src/scripts/create_coinbase_mappings.py src/scripts/create_{exchange_name}_mappings.py
# Update class name and field mappings

# Test mappings (dry run)
python3 src/scripts/create_{exchange_name}_mappings.py --dry-run

# Create actual mappings
python3 src/scripts/create_{exchange_name}_mappings.py
```

### 4. Test Coverage
```bash
# Run coverage test
python3 src/scripts/test_exchange_coverage.py {exchange_name}
```

**Success Criteria**:
- [ ] > 50% coverage for ticker data type
- [ ] All tests pass
- [ ] No critical errors in logs

## 📈 Phase 5: Documentation & Cleanup (30 minutes)

### 1. Update TODO List
- [ ] Update `AI-EXCHANGE-TODO-LIST.txt`:
  - Change `[→]` to `[x]` when complete
  - Add completion date
  - Note product count and coverage percentage

### 2. Update Implementation Status
- [ ] Add to `IMPLEMENTATION-STATUS.md` if exists
- [ ] Note any special implementation details
- [ ] Document US access restrictions if any

### 3. Clean Up
- [ ] Remove any debug print statements
- [ ] Ensure proper error handling
- [ ] Add meaningful log messages
- [ ] Verify PEP8 compliance

## 🚨 Common Issues & Solutions

### Product Discovery Fails (400 Bad Request)
1. **Check URL**: Verify `base_url + endpoint` is correct
2. **Check API version**: Some exchanges require specific API version in path
3. **Check required headers**: Some exchanges require User-Agent or other headers
4. **Test with curl**: `curl -v "{FULL_URL}"`

### WebSocket Channel Issues
1. **Format mismatch**: Verify subscribe format matches API docs exactly
2. **Authentication**: Ensure `authentication_required` is set correctly
3. **Symbol format**: Check if symbols need transformation (e.g., `BTC-USD` vs `BTCUSD`)

### Low Coverage (< 50%)
1. **Field mapping incomplete**: Add more mappings in mapping script
2. **Schema mismatch**: Verify WebSocket message schema in adapter
3. **Missing fields**: Some exchanges may not provide all standard fields

### Database Errors
1. **Foreign key violations**: Ensure vendor exists before linking products
2. **Duplicate entries**: Check if exchange was already added
3. **Schema issues**: Run `python3 main.py init` to ensure latest schema

## 📝 Exchange-Specific Notes

### API Patterns Observed
```
[REST Response Format]:
[WebSocket Message Format]:
[Product Status Mapping]:
[Rate Limit Handling]:
```

### Unique Features
- [ ] Futures/derivatives support
- [ ] Margin trading endpoints
- [ ] Staking/earn endpoints
- [ ] Unique data types

### Testing Data
**Test Results**:
- Products discovered: `[COUNT]`
- REST endpoints: `[COUNT]`
- WebSocket channels: `[COUNT]`
- Ticker coverage: `[PERCENTAGE]%`
- Test duration: `[SECONDS]s`

**Sample Product**: `[SYMBOL]` - `[BASE]/[QUOTE]`

## 🔗 Relevant Files
- `config/settings.py` - Vendor configuration
- `src/adapters/{exchange_name}_adapter.py` - Main adapter
- `src/discovery/spec_generator.py` - Adapter registration
- `src/scripts/create_{exchange_name}_mappings.py` - Field mappings
- `AI-EXCHANGE-TODO-LIST.txt` - Progress tracking

## ✅ Completion Checklist
- [ ] All [ ] checkboxes in this file are checked
- [ ] Exchange appears in `python3 main.py list-vendors`
- [ ] `python3 main.py discover --vendor {exchange_name}` completes successfully
- [ ] `python3 src/scripts/test_exchange_coverage.py {exchange_name}` shows >50% coverage
- [ ] TODO list updated with completion status
- [ ] No errors in `api_spec_generator.log`

---
**Created**: [DATE]
**Last Updated**: [DATE]
**Completed**: [DATE] (if applicable)
**Estimated Time**: [HOURS] hours
**Developer**: [NAME]