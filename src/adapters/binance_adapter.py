# src/adapters/binance_adapter.py
"""
Binance Exchange API adapter.
Discovers REST endpoints, WebSocket channels, and products from Binance API.
"""

from typing import Dict, List, Any

from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BinanceAdapter(BaseVendorAdapter):
    """
    Adapter for Binance Exchange API discovery.
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Binance REST API endpoints.

        Returns:
            List of endpoint dictionaries
        """
        logger.info("Discovering Binance REST endpoints")

        endpoints = []

        # Market data endpoints (public)
        market_endpoints = [
            {
                "path": "/api/v3/ping",
                "method": "GET",
                "authentication_required": False,
                "description": "Test connectivity to the Rest API",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Test connectivity and get server time",
                "query_parameters": {},
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/exchangeInfo",
                "method": "GET",
                "authentication_required": False,
                "description": "Current exchange trading rules and symbol information",
                "query_parameters": {
                    "symbol": "string (optional)",
                    "symbols": "array (optional)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/depth",
                "method": "GET",
                "authentication_required": False,
                "description": "Order book depth",
                "query_parameters": {
                    "symbol": "string (required)",
                    "limit": "integer (5, 10, 20, 50, 100, 500, 1000, 5000)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/trades",
                "method": "GET",
                "authentication_required": False,
                "description": "Recent trades list",
                "query_parameters": {
                    "symbol": "string (required)",
                    "limit": "integer (default 500, max 1000)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/historicalTrades",
                "method": "GET",
                "authentication_required": True,
                "description": "Old trade lookup (requires API key)",
                "query_parameters": {
                    "symbol": "string (required)",
                    "limit": "integer (default 500, max 1000)",
                    "fromId": "long (trade id to fetch from)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/aggTrades",
                "method": "GET",
                "authentication_required": False,
                "description": "Compressed/Aggregate trades list",
                "query_parameters": {
                    "symbol": "string (required)",
                    "fromId": "long (optional)",
                    "startTime": "long (optional)",
                    "endTime": "long (optional)",
                    "limit": "integer (default 500, max 1000)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/klines",
                "method": "GET",
                "authentication_required": False,
                "description": "Kline/candlestick bars for a symbol",
                "query_parameters": {
                    "symbol": "string (required)",
                    "interval": "string (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)",
                    "startTime": "long (optional)",
                    "endTime": "long (optional)",
                    "limit": "integer (default 500, max 1000)"
                },
                "response_schema": {"type": "array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/avgPrice",
                "method": "GET",
                "authentication_required": False,
                "description": "Current average price for a symbol",
                "query_parameters": {
                    "symbol": "string (required)"
                },
                "response_schema": {"type": "object"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/ticker/24hr",
                "method": "GET",
                "authentication_required": False,
                "description": "24 hour rolling window price change statistics",
                "query_parameters": {
                    "symbol": "string (optional - omit for all symbols)",
                    "symbols": "array (optional)"
                },
                "response_schema": {"type": "object or array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/ticker/price",
                "method": "GET",
                "authentication_required": False,
                "description": "Latest price for a symbol or symbols",
                "query_parameters": {
                    "symbol": "string (optional)",
                    "symbols": "array (optional)"
                },
                "response_schema": {"type": "object or array"},
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/v3/ticker/bookTicker",
                "method": "GET",
                "authentication_required": False,
                "description": "Best price/qty on the order book",
                "query_parameters": {
                    "symbol": "string (optional)",
                    "symbols": "array (optional)"
                },
                "response_schema": {"type": "object or array"},
                "rate_limit_tier": "public"
            }
        ]

        endpoints.extend(market_endpoints)

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Binance WebSocket channels.

        Returns:
            List of channel dictionaries
        """
        logger.info("Discovering Binance WebSocket channels")

        channels = [
            {
                "channel_name": "trade",
                "authentication_required": False,
                "description": "The Trade Streams push raw trade information",
                "subscribe_format": {
                    "method": "SUBSCRIBE",
                    "params": ["btcusdt@trade"],
                    "id": 1
                },
                "unsubscribe_format": {
                    "method": "UNSUBSCRIBE",
                    "params": ["btcusdt@trade"],
                    "id": 1
                },
                "message_types": ["trade"],
                "message_schema": {
                    "e": "trade",
                    "E": "Event time",
                    "s": "Symbol",
                    "t": "Trade ID",
                    "p": "Price",
                    "q": "Quantity",
                    "b": "Buyer order ID",
                    "a": "Seller order ID",
                    "T": "Trade time",
                    "m": "Is buyer market maker",
                    "M": "Ignore"
                }
            },
            {
                "channel_name": "kline",
                "authentication_required": False,
                "description": "Kline/Candlestick Streams",
                "subscribe_format": {
                    "method": "SUBSCRIBE",
                    "params": ["btcusdt@kline_1m"],
                    "id": 1
                },
                "unsubscribe_format": {
                    "method": "UNSUBSCRIBE",
                    "params": ["btcusdt@kline_1m"],
                    "id": 1
                },
                "message_types": ["kline"],
                "message_schema": {
                    "e": "kline",
                    "E": "Event time",
                    "s": "Symbol",
                    "k": {
                        "t": "Kline start time",
                        "T": "Kline close time",
                        "s": "Symbol",
                        "i": "Interval",
                        "f": "First trade ID",
                        "L": "Last trade ID",
                        "o": "Open price",
                        "c": "Close price",
                        "h": "High price",
                        "l": "Low price",
                        "v": "Base asset volume",
                        "n": "Number of trades",
                        "x": "Is this kline closed",
                        "q": "Quote asset volume",
                        "V": "Taker buy base asset volume",
                        "Q": "Taker buy quote asset volume"
                    }
                }
            },
            {
                "channel_name": "miniTicker",
                "authentication_required": False,
                "description": "24hr rolling window mini-ticker statistics",
                "subscribe_format": {
                    "method": "SUBSCRIBE",
                    "params": ["btcusdt@miniTicker"],
                    "id": 1
                },
                "message_types": ["24hrMiniTicker"],
                "message_schema": {
                    "e": "24hrMiniTicker",
                    "E": "Event time",
                    "s": "Symbol",
                    "c": "Close price",
                    "o": "Open price",
                    "h": "High price",
                    "l": "Low price",
                    "v": "Total traded base asset volume",
                    "q": "Total traded quote asset volume"
                }
            },
            {
                "channel_name": "ticker",
                "authentication_required": False,
                "description": "24hr rolling window ticker statistics",
                "subscribe_format": {
                    "method": "SUBSCRIBE",
                    "params": ["btcusdt@ticker"],
                    "id": 1
                },
                "message_types": ["24hrTicker"],
                "message_schema": {
                    "e": "24hrTicker",
                    "E": "Event time",
                    "s": "Symbol",
                    "p": "Price change",
                    "P": "Price change percent",
                    "w": "Weighted average price",
                    "x": "First trade price",
                    "c": "Last price",
                    "Q": "Last quantity",
                    "b": "Best bid price",
                    "B": "Best bid quantity",
                    "a": "Best ask price",
                    "A": "Best ask quantity",
                    "o": "Open price",
                    "h": "High price",
                    "l": "Low price",
                    "v": "Total traded base asset volume",
                    "q": "Total traded quote asset volume",
                    "O": "Statistics open time",
                    "C": "Statistics close time",
                    "F": "First trade ID",
                    "L": "Last trade Id",
                    "n": "Total number of trades"
                }
            },
            {
                "channel_name": "bookTicker",
                "authentication_required": False,
                "description": "Best bid/ask price and quantity in real-time",
                "subscribe_format": {
                    "method": "SUBSCRIBE",
                    "params": ["btcusdt@bookTicker"],
                    "id": 1
                },
                "message_types": ["bookTicker"],
                "message_schema": {
                    "u": "order book updateId",
                    "s": "symbol",
                    "b": "best bid price",
                    "B": "best bid qty",
                    "a": "best ask price",
                    "A": "best ask qty"
                }
            },
            {
                "channel_name": "depth",
                "authentication_required": False,
                "description": "Partial Book Depth Streams",
                "subscribe_format": {
                    "method": "SUBSCRIBE",
                    "params": ["btcusdt@depth"],
                    "id": 1
                },
                "message_types": ["depthUpdate"],
                "message_schema": {
                    "e": "depthUpdate",
                    "E": "Event time",
                    "s": "Symbol",
                    "U": "First update ID in event",
                    "u": "Final update ID in event",
                    "b": "Bids to be updated",
                    "a": "Asks to be updated"
                }
            },
            {
                "channel_name": "aggTrade",
                "authentication_required": False,
                "description": "Aggregate Trade Streams",
                "subscribe_format": {
                    "method": "SUBSCRIBE",
                    "params": ["btcusdt@aggTrade"],
                    "id": 1
                },
                "message_types": ["aggTrade"],
                "message_schema": {
                    "e": "aggTrade",
                    "E": "Event time",
                    "s": "Symbol",
                    "a": "Aggregate trade ID",
                    "p": "Price",
                    "q": "Quantity",
                    "f": "First trade ID",
                    "l": "Last trade ID",
                    "T": "Trade time",
                    "m": "Is buyer market maker"
                }
            }
        ]

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Binance trading products by fetching from /api/v3/exchangeInfo endpoint.

        Returns:
            List of product dictionaries
        """
        logger.info("Discovering Binance products from live API")

        try:
            # Fetch exchange info from Binance API
            url = f"{self.base_url}/api/v3/exchangeInfo"
            response = self.http_client.get(url)

            products = []
            for symbol_info in response.get('symbols', []):
                # Only include actively trading symbols
                if symbol_info.get('status') != 'TRADING':
                    continue

                # Parse product information
                product = {
                    "symbol": symbol_info.get("symbol"),
                    "base_currency": symbol_info.get("baseAsset"),
                    "quote_currency": symbol_info.get("quoteAsset"),
                    "status": "online" if symbol_info.get("status") == "TRADING" else "offline",
                    "vendor_metadata": symbol_info  # Store full response
                }

                # Extract order size limits if available
                for filter_item in symbol_info.get('filters', []):
                    if filter_item.get('filterType') == 'LOT_SIZE':
                        product['min_order_size'] = float(filter_item.get('minQty', 0))
                        product['max_order_size'] = float(filter_item.get('maxQty', 0))
                    elif filter_item.get('filterType') == 'PRICE_FILTER':
                        product['price_increment'] = float(filter_item.get('tickSize', 0))

                products.append(product)

            logger.info(f"Discovered {len(products)} products")
            return products

        except Exception as e:
            logger.error(f"Failed to discover products: {e}")
            raise

    def get_kline_intervals(self) -> List[str]:
        """
        Get available kline (candlestick) intervals for Binance.

        Returns:
            List of interval strings
        """
        return [
            "1m", "3m", "5m", "15m", "30m",  # Minutes
            "1h", "2h", "4h", "6h", "8h", "12h",  # Hours
            "1d", "3d",  # Days
            "1w",  # Week
            "1M"  # Month
        ]
