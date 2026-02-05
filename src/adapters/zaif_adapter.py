# src/adapters/zaif_adapter.py
"""
Template adapter for new cryptocurrency exchange implementations.

This file serves as a starting point for implementing new exchange adapters.
Copy this file to a new filename (e.g., `bybit_adapter.py`), rename the class,
and implement the three required abstract methods.

Key Principles:
1. Live API Discovery: Always fetch real data from the exchange API when possible
2. Documentation-First: Base implementations on official API documentation
3. Error Handling: Implement robust error handling with meaningful messages
4. Rate Limiting: Respect exchange rate limits in discovery process

Required Methods to Implement:
- discover_rest_endpoints(): Find all REST API endpoints
- discover_websocket_channels(): Map WebSocket channels and message formats
- discover_products(): Fetch live trading pairs/products from API

See CONTRIBUTING.md for detailed implementation guidelines.
"""

from typing import Dict, List, Any, Optional
from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ZaifAdapter(BaseVendorAdapter):
    """
    Template adapter for Zaif Exchange API.

    Replace all occurrences of:
    - 'ZaifAdapter' with '[ExchangeName]Adapter' (e.g., 'BybitAdapter')
    - 'Zaif' with actual exchange name (e.g., 'Bybit')
    - 'https://api.zaif.jp' with actual REST API base URL
    - 'wss://api.zaif.jp' with actual WebSocket URL
    - Documentation URLs and endpoint patterns

    Configuration Example (add to config/settings.py):
    "[exchange_id]": {
        "enabled": True,
        "display_name": "[Exchange Display Name]",
        "base_url": "https://api.exchange.com",
        "websocket_url": "wss://ws.exchange.com",
        "documentation_url": "https://docs.exchange.com/api",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {
            "products": "/api/v3/exchangeInfo",  # Example product endpoint
            "time": "/api/v3/time",              # Server time endpoint
        },
        "rate_limits": {
            "public": 10  # Requests per second (approximate)
        }
    }
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Zaif REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Zaif REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Product/Instrument information endpoints
        product_endpoints = [
            {
                "path": "/api/1/currency_pairs/all",
                "method": "GET",
                "authentication_required": False,
                "description": "Get all available currency pairs and their trading rules",
                "query_parameters": {},
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "currency_pair": {"type": "string", "description": "Currency pair in format 'btc_jpy'"},
                            "name": {"type": "string", "description": "Display name like 'BTC/JPY'"},
                            "title": {"type": "string", "description": "Japanese title"},
                            "item_japanese": {"type": "string", "description": "Base currency Japanese name"},
                            "aux_japanese": {"type": "string", "description": "Quote currency Japanese name"},
                            "item_unit_min": {"type": "number", "description": "Minimum order size"},
                            "item_unit_step": {"type": "number", "description": "Order size step"},
                            "aux_unit_min": {"type": "number", "description": "Minimum price increment"},
                            "aux_unit_step": {"type": "number", "description": "Price step"},
                            "aux_unit_point": {"type": "integer", "description": "Decimal places for quote currency"},
                            "is_token": {"type": "boolean", "description": "Whether it's a token pair"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(product_endpoints)

        # Market data endpoints
        market_data_endpoints = [
            {
                "path": "/api/1/ticker/{currency_pair}",
                "method": "GET",
                "authentication_required": False,
                "description": "24-hour ticker data for a currency pair",
                "path_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., btc_jpy, eth_jpy)"
                    }
                },
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "last": {"type": "number", "description": "Last trade price"},
                        "high": {"type": "number", "description": "24-hour high"},
                        "low": {"type": "number", "description": "24-hour low"},
                        "vwap": {"type": "number", "description": "Volume weighted average price"},
                        "volume": {"type": "number", "description": "24-hour volume"},
                        "bid": {"type": "number", "description": "Current best bid"},
                        "ask": {"type": "number", "description": "Current best ask"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/1/last_price/{currency_pair}",
                "method": "GET",
                "authentication_required": False,
                "description": "Last trade price for a currency pair",
                "path_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., btc_jpy, eth_jpy)"
                    }
                },
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "last_price": {"type": "number", "description": "Last trade price"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/1/depth/{currency_pair}",
                "method": "GET",
                "authentication_required": False,
                "description": "Order book depth for a currency pair",
                "path_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., btc_jpy, eth_jpy)"
                    }
                },
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "asks": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "[price, quantity]"
                            },
                            "description": "Ask orders (sell side)"
                        },
                        "bids": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "[price, quantity]"
                            },
                            "description": "Bid orders (buy side)"
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/1/trades/{currency_pair}",
                "method": "GET",
                "authentication_required": False,
                "description": "Recent trades for a currency pair",
                "path_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., btc_jpy, eth_jpy)"
                    }
                },
                "query_parameters": {},
                "response_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "integer", "description": "Unix timestamp"},
                            "price": {"type": "number", "description": "Trade price"},
                            "amount": {"type": "number", "description": "Trade amount"},
                            "tid": {"type": "integer", "description": "Trade ID"},
                            "currency_pair": {"type": "string", "description": "Currency pair"},
                            "trade_type": {"type": "string", "description": "Trade type (bid/ask)"}
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(market_data_endpoints)

        # ============================================================================
        # 2. AUTHENTICATED ENDPOINTS (Phase 3 - Optional for initial implementation)
        # ============================================================================

        # Uncomment and implement when adding authenticated endpoint support
        """
        authenticated_endpoints = [
            {
                "path": "/api/1/trade",
                "method": "POST",
                "authentication_required": True,
                "description": "Place a trade order",
                "query_parameters": {
                    "currency_pair": {"type": "string", "required": True},
                    "action": {"type": "string", "required": True, "enum": ["bid", "ask"]},
                    "price": {"type": "number", "required": True},
                    "amount": {"type": "number", "required": True}
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
            {
                "path": "/api/1/balance",
                "method": "POST",
                "authentication_required": True,
                "description": "Get account balance",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
        ]
        endpoints.extend(authenticated_endpoints)
        """

        # ============================================================================
        # 3. DYNAMIC DISCOVERY (Optional - if exchange provides endpoint listing)
        # ============================================================================

        # Zaif doesn't provide endpoint discovery endpoint, so we use static endpoints

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Zaif WebSocket channels.

        Note: Zaif WebSocket API documentation is not readily available.
        This method returns an empty list for now, focusing on REST API integration.
        WebSocket support can be added later when documentation is available.

        Returns:
            Empty list - WebSocket channels not yet implemented for Zaif
        """
        logger.info("Zaif WebSocket channels not yet implemented - returning empty list")
        return []

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Zaif trading products/symbols from live API.

        Fetches currency pairs from /api/1/currency_pairs/all endpoint and maps
        to standard product format.

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering Zaif products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM ZAIF API
            # ========================================================================

            products_url = f"{self.base_url}/api/1/currency_pairs/all"
            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE ZAIF RESPONSE FORMAT
            # ========================================================================

            if not isinstance(response, list):
                logger.error(f"Unexpected response format: {type(response)}")
                raise Exception(f"Unexpected response format from Zaif. Expected list, got {type(response)}")

            products = []

            # ========================================================================
            # 3. PROCESS EACH CURRENCY PAIR
            # ========================================================================

            for pair_info in response:
                try:
                    # Extract currency pair identifier
                    currency_pair = pair_info.get('currency_pair', '')
                    name = pair_info.get('name', '')

                    # Determine symbol format: convert "btc_jpy" to "BTC-JPY"
                    if currency_pair:
                        # currency_pair is like "btc_jpy", "eth_jpy", etc.
                        parts = currency_pair.split('_')
                        if len(parts) == 2:
                            base = parts[0].upper()
                            quote = parts[1].upper()
                            symbol = f"{base}-{quote}"
                        else:
                            # Fallback to name field if currency_pair format unexpected
                            symbol = name.replace('/', '-').upper()
                    else:
                        # Fallback to name field
                        symbol = name.replace('/', '-').upper()

                    # Extract base and quote currencies
                    base_currency = None
                    quote_currency = None

                    if currency_pair and '_' in currency_pair:
                        base, quote = currency_pair.split('_')
                        base_currency = base.upper()
                        quote_currency = quote.upper()
                    elif name and '/' in name:
                        base, quote = name.split('/')
                        base_currency = base.strip().upper()
                        quote_currency = quote.strip().upper()
                    else:
                        logger.warning(f"Cannot extract currencies from pair: {pair_info}")
                        continue

                    # All Zaif pairs are assumed to be online/trading
                    status = 'online'

                    # Extract trading limits from Zaif response
                    min_order_size = pair_info.get('item_unit_min')
                    max_order_size = None  # Zaif doesn't provide max order size
                    price_increment = pair_info.get('aux_unit_step')

                    # Convert to appropriate types
                    if min_order_size is not None:
                        try:
                            min_order_size = float(min_order_size)
                        except (ValueError, TypeError):
                            min_order_size = None

                    if price_increment is not None:
                        try:
                            price_increment = float(price_increment)
                        except (ValueError, TypeError):
                            price_increment = None

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": max_order_size,
                        "price_increment": price_increment,
                        "vendor_metadata": pair_info  # Store full raw data
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"], product["quote_currency"]]):
                        logger.warning(f"Skipping product with missing required fields: {pair_info}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse product {pair_info.get('currency_pair', 'unknown')}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from API response")
                raise Exception("No products found in API response")

            logger.info(f"Discovered {len(products)} Zaif products")

            return products

        except Exception as e:
            logger.error(f"Failed to discover Zaif products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for Zaif: {e}")

    # ============================================================================
    # OPTIONAL HELPER METHODS
    # ============================================================================

    def get_candle_intervals(self) -> List[int]:
        """
        Get available candle intervals for this exchange.

        Returns:
            List of granularity values in seconds
        """
        # Common intervals in seconds
        # Adjust based on exchange documentation
        return [60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 28800, 43200, 86400, 259200, 604800]

    def validate_endpoint(self, endpoint: Dict[str, Any]) -> bool:
        """
        Validate that an endpoint is accessible (optional override).

        Can be used to test endpoints during discovery.

        Args:
            endpoint: Endpoint dictionary

        Returns:
            True if endpoint is accessible, False otherwise
        """
        try:
            url = self.base_url + endpoint['path']

            # Test with minimal parameters
            test_params = {}
            if 'query_parameters' in endpoint:
                # Build minimal valid parameters for testing
                for param_name, param_info in endpoint['query_parameters'].items():
                    if param_info.get('required', False):
                        # Provide dummy/default value for required parameters
                        if param_info.get('type') == 'string':
                            test_params[param_name] = 'test'
                        elif param_info.get('type') == 'integer':
                            test_params[param_name] = 1
                        elif 'enum' in param_info:
                            test_params[param_name] = param_info['enum'][0]

            # Make test request
            self.http_client.get(url, params=test_params)
            return True

        except Exception as e:
            logger.debug(f"Endpoint validation failed for {endpoint['path']}: {e}")
            return False

    def test_websocket_channel(self, channel: Dict[str, Any]) -> bool:
        """
        Test WebSocket channel connectivity (optional override).

        Can be implemented to actually connect and test WebSocket channels.

        Args:
            channel: Channel dictionary

        Returns:
            True if channel is accessible, False otherwise
        """
        # Basic implementation - override for actual WebSocket testing
        logger.debug(f"WebSocket test not implemented for {channel['channel_name']}")
        return True
