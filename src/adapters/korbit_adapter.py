# src/adapters/korbit_adapter.py
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


class KorbitAdapter(BaseVendorAdapter):
    """
    Adapter for Korbit Exchange API.

    Korbit is a South Korean cryptocurrency exchange.
    API Documentation: https://apidocs.korbit.co.kr/

    Key endpoints:
    - GET /v1/constants - Exchange configuration and trading pairs
    - GET /v1/ticker - Current price for currency pair
    - GET /v1/orderbook - Order book depth
    - WebSocket: wss://ws.korbit.co.kr

    Market format: "btc_krw", "eth_krw" (base_quote, lowercase with underscore)
    Constants endpoint provides trading rules: tick_size, min_price, max_price, order_min_size, order_max_size
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Korbit REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from documentation
        2. Consider dynamic discovery if exchange provides endpoint listing
        3. Include both market data and (optionally) authenticated endpoints
        4. Document rate limits, authentication requirements, parameters

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Korbit REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Exchange configuration and product information
        product_endpoints = [
            {
                "path": "/v1/constants",
                "method": "GET",
                "authentication_required": False,
                "description": "Get exchange configuration and trading rules for all currency pairs",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "exchange": {
                            "type": "object",
                            "additionalProperties": {
                                "type": "object",
                                "properties": {
                                    "tick_size": {"type": "number"},
                                    "min_price": {"type": "number"},
                                    "max_price": {"type": "number"},
                                    "order_min_size": {"type": "number"},
                                    "order_max_size": {"type": "number"}
                                }
                            }
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
                "path": "/v1/ticker",
                "method": "GET",
                "authentication_required": False,
                "description": "Current price for a currency pair",
                "query_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., btc_krw, eth_krw)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "integer", "description": "Unix timestamp in milliseconds"},
                        "last": {"type": "string", "description": "Last trade price"}
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/v1/orderbook",
                "method": "GET",
                "authentication_required": False,
                "description": "Order book depth for a currency pair",
                "query_parameters": {
                    "currency_pair": {
                        "type": "string",
                        "required": True,
                        "description": "Currency pair (e.g., btc_krw, eth_krw)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "integer", "description": "Unix timestamp in milliseconds"},
                        "bids": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "[price, quantity, order_count]"
                            }
                        },
                        "asks": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 3,
                                "maxItems": 3,
                                "description": "[price, quantity, order_count]"
                            }
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

        # Korbit requires authentication for most account-related endpoints
        # These are placeholder for future implementation
        authenticated_endpoints = [
            {
                "path": "/v1/user/balances",
                "method": "GET",
                "authentication_required": True,
                "description": "Account balance information",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
            {
                "path": "/v1/user/orders",
                "method": "POST",
                "authentication_required": True,
                "description": "Place new order",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "private"
            },
        ]
        endpoints.extend(authenticated_endpoints)

        # ============================================================================
        # 3. DYNAMIC DISCOVERY (Optional - if exchange provides endpoint listing)
        # ============================================================================

        # Korbit doesn't provide endpoint discovery, using static endpoints

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Korbit WebSocket channels and message formats.

        Korbit WebSocket API documentation:
        - Connection URL: wss://ws.korbit.co.kr
        - Market format: "btc_krw", "eth_krw" (base_quote, lowercase with underscore)
        - Based on REST API patterns, WebSocket likely follows similar structure

        Implementation Strategy:
        1. Map public WebSocket channels based on REST API patterns
        2. Include Korbit-specific subscribe/unsubscribe message formats
        3. Document message types and schemas based on REST responses
        4. Note authentication requirements (none for public channels)

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering Korbit WebSocket channels")

        channels = []

        # ============================================================================
        # 1. MARKET DATA CHANNELS (Public - No Authentication Required)
        # ============================================================================

        # Ticker channel - Real-time price updates
        channels.append({
            "channel_name": "ticker",
            "authentication_required": False,
            "description": "Real-time ticker updates for currency pairs",
            "subscribe_format": {
                "type": "subscribe",
                "method": "ticker",
                "params": ["<currency_pair>"],  # Replace <currency_pair> with actual pair (e.g., btc_krw)
                "id": 1
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "method": "ticker",
                "params": ["<currency_pair>"],
                "id": 2
            },
            "message_types": ["ticker", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (ticker)"},
                    "currency_pair": {"type": "string", "description": "Currency pair (e.g., btc_krw)"},
                    "timestamp": {"type": "integer", "description": "Unix timestamp in milliseconds"},
                    "last": {"type": "string", "description": "Last trade price"},
                    "open": {"type": "string", "description": "Opening price (24h)"},
                    "high": {"type": "string", "description": "Highest price (24h)"},
                    "low": {"type": "string", "description": "Lowest price (24h)"},
                    "volume": {"type": "string", "description": "Trading volume (24h)"},
                    "bid": {"type": "string", "description": "Current best bid price"},
                    "ask": {"type": "string", "description": "Current best ask price"}
                }
            },
            "vendor_metadata": {
                "channel_pattern": "ticker",  # Korbit likely uses method-based subscription
                "supports_multiple_symbols": True,
                "update_frequency": "real-time",
                "market_format": "base_quote_lowercase"  # e.g., btc_krw, eth_krw
            }
        })

        # Order book channel - Real-time order book updates
        channels.append({
            "channel_name": "orderbook",
            "authentication_required": False,
            "description": "Real-time order book depth updates",
            "subscribe_format": {
                "type": "subscribe",
                "method": "orderbook",
                "params": ["<currency_pair>"],
                "id": 1
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "method": "orderbook",
                "params": ["<currency_pair>"],
                "id": 2
            },
            "message_types": ["orderbook", "snapshot", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (orderbook)"},
                    "currency_pair": {"type": "string", "description": "Currency pair"},
                    "timestamp": {"type": "integer", "description": "Unix timestamp in milliseconds"},
                    "bids": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "[price, quantity, order_count] - Based on REST orderbook format"
                        }
                    },
                    "asks": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 3,
                            "maxItems": 3,
                            "description": "[price, quantity, order_count] - Based on REST orderbook format"
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "orderbook",
                "levels": "full",  # Based on REST orderbook which shows full depth
                "update_type": "snapshot",  # Assuming full snapshot updates
                "format": "price_quantity_count"  # REST returns [price, quantity, order_count]
            }
        })

        # Trade channel - Real-time trade execution updates
        channels.append({
            "channel_name": "trade",
            "authentication_required": False,
            "description": "Real-time trade execution updates",
            "subscribe_format": {
                "type": "subscribe",
                "method": "trade",
                "params": ["<currency_pair>"],
                "id": 1
            },
            "unsubscribe_format": {
                "type": "unsubscribe",
                "method": "trade",
                "params": ["<currency_pair>"],
                "id": 2
            },
            "message_types": ["trade", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (trade)"},
                    "currency_pair": {"type": "string", "description": "Currency pair"},
                    "timestamp": {"type": "integer", "description": "Unix timestamp in milliseconds"},
                    "price": {"type": "string", "description": "Trade price"},
                    "amount": {"type": "string", "description": "Trade amount/quantity"},
                    "side": {"type": "string", "description": "Trade side (buy/sell)"},
                    "trade_id": {"type": "integer", "description": "Unique trade identifier"}
                }
            },
            "vendor_metadata": {
                "channel_pattern": "trade",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time",
                "trade_types": ["individual"],
                "include_maker_info": False  # REST doesn't show maker info, WebSocket likely similar
            }
        })

        # ============================================================================
        # 2. HEARTBEAT/CONNECTION MANAGEMENT
        # ============================================================================

        channels.append({
            "channel_name": "heartbeat",
            "authentication_required": False,
            "description": "Connection heartbeat/ping-pong messages",
            "subscribe_format": {
                "type": "ping"
            },
            "unsubscribe_format": {
                "type": "pong"
            },
            "message_types": ["pong", "connection", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Message type (pong)"},
                    "timestamp": {"type": "integer", "description": "Timestamp"}
                }
            },
            "vendor_metadata": {
                "keepalive_interval": 30000,  # milliseconds (typical)
                "auto_reconnect": True,
                "ping_format": {"type": "ping"}  # Simple ping message
            }
        })

        # ============================================================================
        # 3. AUTHENTICATED CHANNELS (Phase 3 - Optional)
        # ============================================================================

        # Korbit requires authentication for account-related WebSocket channels
        # Placeholder for future implementation
        """
        channels.append({
            "channel_name": "account",
            "authentication_required": True,
            "description": "Account updates (balance changes, orders, etc.)",
            "subscribe_format": {
                "type": "auth",
                "method": "login",
                "params": ["api_key", "nonce", "signature"]
            },
            "message_types": ["balance", "order", "trade"],
            "message_schema": {"type": "object"},
            "vendor_metadata": {
                "requires_signature": True,
                "update_types": ["balance", "order", "trade"],
                "auth_method": "api_key_signature_nonce"
            }
        })
        """

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Korbit trading products/symbols from live API.

        IMPORTANT: This method MUST make live API calls to fetch actual products.
        Do not hardcode products. Fetch from exchange's product endpoint.

        Implementation Steps:
        1. Call Korbit's constants endpoint /v1/constants
        2. Parse response to extract currency pair information
        3. Map to our standard product format with trading rules
        4. Extract base/quote from currency pair format "btc_krw"
        5. Implement error handling and retry logic

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering Korbit products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM KORBIT API
            # ========================================================================

            # Korbit endpoint: /v1/constants
            products_url = f"{self.base_url}/v1/constants"

            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE RESPONSE BASED ON KORBIT FORMAT
            # ========================================================================

            products = []

            # Korbit response format: {"exchange": {"btc_krw": {...}, "eth_krw": {...}, ...}}
            if 'exchange' not in response:
                logger.error(f"Unexpected response format, missing 'exchange' key: {response.keys()}")
                raise Exception(f"Unexpected response format from Korbit, expected 'exchange' key")

            exchange_data = response['exchange']

            # Ensure we have a dictionary
            if not isinstance(exchange_data, dict):
                logger.error(f"Unexpected exchange data format: {type(exchange_data)}")
                raise Exception(f"Unexpected exchange data format from Korbit, expected dict")

            # ========================================================================
            # 3. PROCESS EACH CURRENCY PAIR
            # ========================================================================

            for currency_pair, pair_info in exchange_data.items():
                try:
                    # Validate currency pair format (e.g., "btc_krw")
                    if not isinstance(currency_pair, str) or '_' not in currency_pair:
                        logger.warning(f"Skipping malformed currency pair: {currency_pair}")
                        continue

                    # Parse base and quote currency (format: "base_quote", lowercase)
                    parts = currency_pair.split('_')
                    if len(parts) != 2:
                        logger.warning(f"Skipping malformed currency pair {currency_pair}, expected format 'xxx_xxx'")
                        continue

                    base_currency = parts[0].upper()
                    quote_currency = parts[1].upper()

                    # Create standard symbol format (BTC-KRW)
                    symbol = f"{base_currency}-{quote_currency}"

                    # Korbit doesn't provide status in this endpoint, assume online
                    status = 'online'

                    # Extract trading limits from pair info
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    if isinstance(pair_info, dict):
                        # Korbit provides order_min_size and order_max_size
                        order_min_size = pair_info.get('order_min_size')
                        order_max_size = pair_info.get('order_max_size')
                        tick_size = pair_info.get('tick_size')

                        if order_min_size is not None:
                            try:
                                min_order_size = float(order_min_size)
                            except (ValueError, TypeError):
                                logger.warning(f"Failed to parse order_min_size for {currency_pair}: {order_min_size}")

                        if order_max_size is not None:
                            try:
                                max_order_size = float(order_max_size)
                            except (ValueError, TypeError):
                                logger.warning(f"Failed to parse order_max_size for {currency_pair}: {order_max_size}")

                        if tick_size is not None:
                            try:
                                price_increment = float(tick_size)
                            except (ValueError, TypeError):
                                logger.warning(f"Failed to parse tick_size for {currency_pair}: {tick_size}")

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": max_order_size,
                        "price_increment": price_increment,
                        "vendor_metadata": {
                            "currency_pair": currency_pair,
                            "raw_pair_info": pair_info,
                            "trading_rules": {
                                "tick_size": pair_info.get('tick_size') if isinstance(pair_info, dict) else None,
                                "min_price": pair_info.get('min_price') if isinstance(pair_info, dict) else None,
                                "max_price": pair_info.get('max_price') if isinstance(pair_info, dict) else None,
                                "order_min_size": pair_info.get('order_min_size') if isinstance(pair_info, dict) else None,
                                "order_max_size": pair_info.get('order_max_size') if isinstance(pair_info, dict) else None
                            }
                        }
                    }

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse currency pair {currency_pair}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from API response")
                raise Exception("No products found in API response")

            logger.info(f"Discovered {len(products)} products")

            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for Korbit: {e}")

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
