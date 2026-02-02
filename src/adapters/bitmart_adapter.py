# src/adapters/bitmart_adapter.py
"""
BitMart Exchange API adapter.
Discovers REST endpoints, WebSocket channels, and products from BitMart API.
"""

from typing import Dict, List, Any, Optional
import requests
import time
import json

from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BitmartAdapter(BaseVendorAdapter):
    """
    Adapter for BitMart Exchange API discovery.

    BitMart API documentation: https://developer-pro.bitmart.com/en/spot
    Base URL: https://api-cloud.bitmart.com
    WebSocket URL: wss://ws-manager-compress.bitmart.com

    API Response Format:
    {
        "code": 1000,           # 1000 = success, other codes = error
        "message": "OK",        # Human-readable message
        "trace": "trace-id",    # Request trace ID
        "data": {}              # Response data (varies by endpoint)
    }
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover BitMart REST API endpoints.

        Returns:
            List of endpoint dictionaries
        """
        logger.info("Discovering BitMart REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. SYSTEM & CONNECTIVITY ENDPOINTS (Public)
        # ============================================================================

        system_endpoints = [
            {
                "path": "/system/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Get server time",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "description": "Response code (1000 = success)"},
                        "message": {"type": "string", "description": "Response message"},
                        "trace": {"type": "string", "description": "Request trace ID"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "server_time": {"type": "integer", "description": "Server timestamp in milliseconds"}
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/system/service",
                "method": "GET",
                "authentication_required": False,
                "description": "Get system service status",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            }
        ]
        endpoints.extend(system_endpoints)

        # ============================================================================
        # 2. MARKET DATA ENDPOINTS (Public)
        # ============================================================================

        # Trading symbol information
        symbol_endpoints = [
            {
                "path": "/spot/v1/symbols",
                "method": "GET",
                "authentication_required": False,
                "description": "Get all trading symbols",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "description": "Response code (1000 = success)"},
                        "message": {"type": "string", "description": "Response message"},
                        "trace": {"type": "string", "description": "Request trace ID"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "symbols": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of trading symbols (e.g., BTC_USDT)"
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/spot/v1/symbols/details",
                "method": "GET",
                "authentication_required": False,
                "description": "Get detailed symbol information",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            }
        ]
        endpoints.extend(symbol_endpoints)

        # Ticker/price data
        ticker_endpoints = [
            {
                "path": "/spot/v1/ticker",
                "method": "GET",
                "authentication_required": False,
                "description": "Get 24-hour ticker for all symbols",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer", "description": "Response code (1000 = success)"},
                        "message": {"type": "string", "description": "Response message"},
                        "trace": {"type": "string", "description": "Request trace ID"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "tickers": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "symbol": {"type": "string", "description": "Trading pair symbol"},
                                            "last_price": {"type": "string", "description": "Last trade price"},
                                            "quote_volume_24h": {"type": "string", "description": "24h quote volume"},
                                            "base_volume_24h": {"type": "string", "description": "24h base volume"},
                                            "high_24h": {"type": "string", "description": "24h high price"},
                                            "low_24h": {"type": "string", "description": "24h low price"},
                                            "open_24h": {"type": "string", "description": "24h opening price"},
                                            "close_24h": {"type": "string", "description": "24h closing price"},
                                            "best_ask": {"type": "string", "description": "Best ask price"},
                                            "best_ask_size": {"type": "string", "description": "Best ask size"},
                                            "best_bid": {"type": "string", "description": "Best bid price"},
                                            "best_bid_size": {"type": "string", "description": "Best bid size"},
                                            "fluctuation": {"type": "string", "description": "Price fluctuation"},
                                            "url": {"type": "string", "description": "Trading page URL"},
                                            "timestamp": {"type": "integer", "description": "Data timestamp"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/spot/v1/ticker/detail",
                "method": "GET",
                "authentication_required": False,
                "description": "Get ticker detail for specific symbol",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol (e.g., BTC_USDT)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/spot/v2/ticker",
                "method": "GET",
                "authentication_required": False,
                "description": "Get ticker data (v2)",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            }
        ]
        endpoints.extend(ticker_endpoints)

        # Order book data
        orderbook_endpoints = [
            {
                "path": "/spot/v1/symbols/book",
                "method": "GET",
                "authentication_required": False,
                "description": "Get order book for symbol",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "precision": {
                        "type": "string",
                        "required": False,
                        "description": "Price precision (optional)"
                    },
                    "size": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of price levels (1-200, default=50)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/spot/quotation/v3/books",
                "method": "GET",
                "authentication_required": False,
                "description": "Get order book depth (v3)",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Depth limit (1-50, default=10)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            }
        ]
        endpoints.extend(orderbook_endpoints)

        # Trade history
        trade_endpoints = [
            {
                "path": "/spot/v1/symbols/trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Get recent trades",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "N": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of trades (default=50, max=100)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/spot/quotation/v3/trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Get recent trades (v3)",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of trades (default=50, max=100)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            }
        ]
        endpoints.extend(trade_endpoints)

        # K-line/Candlestick data
        kline_endpoints = [
            {
                "path": "/spot/v1/symbols/kline",
                "method": "GET",
                "authentication_required": False,
                "description": "Get K-line/candlestick data",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "from": {
                        "type": "integer",
                        "required": True,
                        "description": "Start timestamp (seconds)"
                    },
                    "to": {
                        "type": "integer",
                        "required": True,
                        "description": "End timestamp (seconds)"
                    },
                    "step": {
                        "type": "integer",
                        "required": True,
                        "description": "K-line interval in seconds (60, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 604800)"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of K-lines (default=100, max=1000)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/spot/quotation/v3/klines",
                "method": "GET",
                "authentication_required": False,
                "description": "Get K-line data (v3)",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair symbol"
                    },
                    "start_time": {
                        "type": "integer",
                        "required": False,
                        "description": "Start timestamp (milliseconds)"
                    },
                    "end_time": {
                        "type": "integer",
                        "required": False,
                        "description": "End timestamp (milliseconds)"
                    },
                    "step": {
                        "type": "integer",
                        "required": False,
                        "description": "Interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, 1440, 4320, 10080)"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Number of K-lines (default=100, max=1000)"
                    }
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            }
        ]
        endpoints.extend(kline_endpoints)

        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover BitMart WebSocket channels and message formats.

        BitMart WebSocket documentation:
        - URL: wss://ws-manager-compress.bitmart.com
        - Supports spot, futures, and options markets
        - Uses subscribe/unsubscribe messages

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering BitMart WebSocket channels")

        channels = []

        # ============================================================================
        # SPOT MARKET CHANNELS
        # ============================================================================

        # Public spot channels
        spot_channels = [
            {
                "channel_name": "spot/ticker",
                "description": "Spot market ticker updates",
                "authentication_required": False,
                "subscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "subscribe"},
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of channels to subscribe (e.g., ['spot/ticker:BTC_USDT'])"
                        }
                    }
                },
                "unsubscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "unsubscribe"},
                        "args": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "message_types": ["ticker"],
                "data_format": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string", "description": "Channel name"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "last_price": {"type": "string"},
                                    "timestamp": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            },
            {
                "channel_name": "spot/depth",
                "description": "Spot market order book depth updates",
                "authentication_required": False,
                "subscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "subscribe"},
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of channels (e.g., ['spot/depth5:BTC_USDT'])"
                        }
                    }
                },
                "unsubscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "unsubscribe"},
                        "args": {"type": "array"}
                    }
                },
                "message_types": ["depth", "depth5", "depth20", "depth50"],
                "data_format": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"},
                        "action": {"type": "string", "description": "'partial' or 'update'"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "asks": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "minItems": 2,
                                            "maxItems": 2,
                                            "description": "[price, quantity]"
                                        }
                                    },
                                    "bids": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "minItems": 2,
                                            "maxItems": 2
                                        }
                                    },
                                    "timestamp": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            },
            {
                "channel_name": "spot/trade",
                "description": "Spot market trade updates",
                "authentication_required": False,
                "subscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "subscribe"},
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of channels (e.g., ['spot/trade:BTC_USDT'])"
                        }
                    }
                },
                "unsubscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "unsubscribe"},
                        "args": {"type": "array"}
                    }
                },
                "message_types": ["trade"],
                "data_format": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "side": {"type": "string", "description": "'buy' or 'sell'"},
                                    "price": {"type": "string"},
                                    "size": {"type": "string"},
                                    "timestamp": {"type": "integer"},
                                    "trade_id": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            {
                "channel_name": "spot/kline",
                "description": "Spot market K-line/candlestick updates",
                "authentication_required": False,
                "subscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "subscribe"},
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of channels (e.g., ['spot/kline1m:BTC_USDT'])"
                        }
                    }
                },
                "unsubscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "unsubscribe"},
                        "args": {"type": "array"}
                    }
                },
                "message_types": ["kline1m", "kline5m", "kline15m", "kline30m", "kline1h", "kline4h", "kline1d"],
                "data_format": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string"},
                                    "interval": {"type": "string"},
                                    "open": {"type": "string"},
                                    "high": {"type": "string"},
                                    "low": {"type": "string"},
                                    "close": {"type": "string"},
                                    "volume": {"type": "string"},
                                    "timestamp": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            }
        ]
        channels.extend(spot_channels)

        # ============================================================================
        # ACCOUNT CHANNELS (Authentication Required)
        # ============================================================================

        account_channels = [
            {
                "channel_name": "spot/user/order",
                "description": "User order updates (requires authentication)",
                "authentication_required": True,
                "subscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "login"},
                        "args": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "API key and signature"
                        }
                    }
                },
                "message_types": ["order", "trade"],
                "data_format": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"},
                        "data": {"type": "array"}
                    }
                }
            },
            {
                "channel_name": "spot/user/balance",
                "description": "User balance updates (requires authentication)",
                "authentication_required": True,
                "subscribe_message": {
                    "type": "object",
                    "properties": {
                        "op": {"type": "string", "const": "login"},
                        "args": {"type": "array"}
                    }
                },
                "message_types": ["balance"],
                "data_format": {
                    "type": "object",
                    "properties": {
                        "table": {"type": "string"},
                        "data": {"type": "array"}
                    }
                }
            }
        ]
        channels.extend(account_channels)

        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover BitMart trading products/symbols from live API.

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering BitMart products from live API")

        try:
            # Make API call to get symbols
            base_url = self.base_url
            symbols_endpoint = self.config.get("endpoints", {}).get("products", "/spot/v1/symbols")

            url = f"{base_url}{symbols_endpoint}"
            logger.debug(f"Fetching products from: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # BitMart API response format: {"code": 1000, "message": "OK", "data": {"symbols": [...]}}
            if data.get("code") != 1000:
                error_msg = data.get("message", "Unknown error")
                logger.error(f"BitMart API error: {error_msg}")
                raise Exception(f"BitMart API error: {error_msg}")

            symbols_data = data.get("data", {})
            symbols_list = symbols_data.get("symbols", [])

            if not symbols_list:
                logger.error("No symbols found in BitMart API response")
                raise Exception("No symbols found in BitMart API response")

            logger.info(f"Found {len(symbols_list)} BitMart trading symbols")

            # Convert to standard product format
            products = []
            for symbol in symbols_list:
                # BitMart symbols format: "BTC_USDT", "ETH_USDT", etc.
                # Parse symbol to extract base and quote currencies
                if "_" in symbol:
                    parts = symbol.split("_")
                    if len(parts) >= 2:
                        base_currency = parts[0]
                        quote_currency = parts[1]
                    else:
                        base_currency = symbol
                        quote_currency = "UNKNOWN"
                else:
                    # Fallback for symbols without underscore
                    base_currency = symbol
                    quote_currency = "UNKNOWN"

                product = {
                    "symbol": symbol,
                    "base_currency": base_currency,
                    "quote_currency": quote_currency,
                    "status": "online",
                    "min_order_size": None,
                    "max_order_size": None,
                    "price_increment": None,
                    "vendor_metadata": {
                        "original_symbol": symbol,
                        "symbol_display_name": symbol,
                        "exchange": "bitmart",
                        "product_type": "spot",
                        "discovery_timestamp": int(time.time()),
                        "discovery_source": "live_api"
                    }
                }
                products.append(product)

            logger.info(f"Successfully discovered {len(products)} BitMart products")
            return products

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching BitMart products: {e}")
            raise Exception(f"Network error fetching BitMart products: {e}")
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing BitMart API response: {e}")
            logger.debug(f"Response data: {data if 'data' in locals() else 'No data'}")
            raise Exception(f"Error parsing BitMart API response: {e}")
        except Exception as e:
            logger.error(f"Failed to discover BitMart products: {e}")
            raise Exception(f"Product discovery failed for BitMart: {e}")

    def get_candle_intervals(self) -> Dict[str, int]:
        """
        Get available candle intervals for BitMart.

        Returns:
            Dictionary mapping interval names to seconds
        """
        return {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400,
            "6h": 21600,
            "12h": 43200,
            "1d": 86400,
            "3d": 259200,
            "1w": 604800
        }

    def validate_endpoint(self, endpoint_path: str, method: str = "GET",
                         params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Validate an API endpoint by making a test request.

        Args:
            endpoint_path: API endpoint path
            method: HTTP method
            params: Query parameters

        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating BitMart endpoint: {endpoint_path}")

        try:
            base_url = self.base_url
            url = f"{base_url}{endpoint_path}"

            response = requests.request(
                method=method,
                url=url,
                params=params or {},
                timeout=10
            )

            result = {
                "endpoint": endpoint_path,
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    result["data"] = data

                    # Check BitMart-specific success code
                    if data.get("code") == 1000:
                        result["api_success"] = True
                        result["api_message"] = data.get("message", "OK")
                    else:
                        result["api_success"] = False
                        result["api_message"] = data.get("message", "Unknown error")

                except json.JSONDecodeError:
                    result["raw_response"] = response.text[:500]
                    result["api_success"] = False
            else:
                result["api_success"] = False
                try:
                    result["error_data"] = response.json()
                except:
                    result["error_text"] = response.text[:500]

            return result

        except requests.exceptions.RequestException as e:
            return {
                "endpoint": endpoint_path,
                "url": url,
                "method": method,
                "success": False,
                "error": str(e),
                "api_success": False
            }

    def test_websocket_channel(self, channel_name: str, symbol: str = "BTC_USDT") -> Dict[str, Any]:
        """
        Test WebSocket channel connectivity (simulated - actual WebSocket test requires async client).

        Args:
            channel_name: WebSocket channel name
            symbol: Trading symbol to test with

        Returns:
            Dictionary with test results
        """
        logger.info(f"Testing BitMart WebSocket channel: {channel_name}")

        # This is a simulated test - actual WebSocket testing requires async client
        # Return information about the channel instead

        result = {
            "channel_name": channel_name,
            "symbol": symbol,
            "full_channel": f"{channel_name}:{symbol}",
            "websocket_url": self.websocket_url if self.websocket_url else "wss://ws-manager-compress.bitmart.com",
            "test_type": "simulated",
            "supported": True,
            "note": "Actual WebSocket testing requires websocket-client library and async implementation",
            "subscribe_message": {
                "op": "subscribe",
                "args": [f"{channel_name}:{symbol}"]
            },
            "expected_response_format": "JSON object with 'table' and 'data' fields"
        }

        # Add channel-specific information
        if "ticker" in channel_name:
            result["data_type"] = "ticker"
            result["fields"] = ["symbol", "last_price", "timestamp"]
        elif "depth" in channel_name:
            result["data_type"] = "order_book"
            result["fields"] = ["symbol", "asks", "bids", "timestamp"]
        elif "trade" in channel_name:
            result["data_type"] = "trade"
            result["fields"] = ["symbol", "side", "price", "size", "timestamp", "trade_id"]
        elif "kline" in channel_name:
            result["data_type"] = "candle"
            result["fields"] = ["symbol", "interval", "open", "high", "low", "close", "volume", "timestamp"]

        return result
