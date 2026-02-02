# src/adapters/bitget_adapter.py
"""
Bitget Exchange API adapter.

This adapter implements live API discovery for Bitget cryptocurrency exchange.

Bitget API Documentation:
- REST API: https://bitgetlimited.github.io/apidoc/en/spot/
- WebSocket API: https://bitgetlimited.github.io/apidoc/en/spot/#websocketapi

Key Features:
- High-volume derivatives and spot trading
- Support for USDT, USDC, and COIN futures
- Real-time market data via WebSocket
- Public REST endpoints for market data

Implementation based on Bitget API v1 (spot) documentation.
"""

from typing import Dict, List, Any, Optional
from src.adapters.base_adapter import BaseVendorAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BitgetAdapter(BaseVendorAdapter):
    """
    Adapter for Bitget Exchange API discovery.

    Bitget API Configuration:
    - Base URL: https://api.bitget.com
    - WebSocket URL: wss://ws.bitget.com/spot/v1/stream
    - Documentation: https://bitgetlimited.github.io/apidoc/en/spot/

    API Features:
    - Public endpoints require no authentication
    - WebSocket channels for real-time data
    - Support for spot, futures, and margin trading
    - USDT, USDC, and COIN futures product types

    Rate Limits:
    - Public endpoints: 20 requests per second (per IP)
    - WebSocket: 100 connections per IP
    - Subscription limit: 240 per hour

    Implementation covers spot trading API v1 endpoints.
    """

    def discover_rest_endpoints(self) -> List[Dict[str, Any]]:
        """
        Discover Bitget REST API endpoints.

        Implementation Strategy:
        1. Start with known public endpoints from Bitget spot API documentation
        2. Include market data endpoints (ticker, order book, trades, candles)
        3. Document rate limits, authentication requirements, parameters
        4. Map response schemas based on API documentation

        Returns:
            List of endpoint dictionaries with standard structure
        """
        logger.info("Discovering Bitget REST endpoints")

        endpoints = []

        # ============================================================================
        # 1. MARKET DATA ENDPOINTS (Public - No Authentication Required)
        # ============================================================================

        # Basic connectivity and system status endpoints
        system_endpoints = [
            {
                "path": "/api/spot/v1/public/time",
                "method": "GET",
                "authentication_required": False,
                "description": "Get server time",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code (00000 = success)"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {"type": "integer", "description": "Server time in milliseconds"}
                    }
                },
                "rate_limit_tier": "public"
            }
        ]
        endpoints.extend(system_endpoints)

        # Product/Instrument information endpoints
        product_endpoints = [
            {
                "path": "/api/spot/v1/public/products",
                "method": "GET",
                "authentication_required": False,
                "description": "Get list of all trading pairs with basic configuration",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code (00000 = success)"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string", "description": "Symbol ID"},
                                    "symbolName": {"type": "string", "description": "Symbol name"},
                                    "symbolDisplayName": {"type": "string", "description": "Symbol display name"},
                                    "baseCoin": {"type": "string", "description": "Base coin"},
                                    "quoteCoin": {"type": "string", "description": "Quote coin"},
                                    "minTradeAmount": {"type": "string", "description": "Minimum trading amount"},
                                    "maxTradeAmount": {"type": "string", "description": "Maximum trading amount"},
                                    "takerFeeRate": {"type": "string", "description": "Taker fee rate"},
                                    "makerFeeRate": {"type": "string", "description": "Maker fee rate"},
                                    "priceScale": {"type": "string", "description": "Price decimal scale"},
                                    "quantityScale": {"type": "string", "description": "Quantity decimal scale"},
                                    "status": {"type": "string", "description": "Status (online, offline, gray)"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/spot/v1/public/product",
                "method": "GET",
                "authentication_required": False,
                "description": "Get single symbol information",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Symbol ID (e.g., BTCUSDT_SPBL)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string", "description": "Symbol ID"},
                                    "symbolName": {"type": "string", "description": "Symbol name"},
                                    "symbolDisplayName": {"type": "string", "description": "Symbol display name"},
                                    "baseCoin": {"type": "string", "description": "Base coin"},
                                    "quoteCoin": {"type": "string", "description": "Quote coin"},
                                    "minTradeAmount": {"type": "string", "description": "Minimum trading amount"},
                                    "maxTradeAmount": {"type": "string", "description": "Maximum trading amount"},
                                    "takerFeeRate": {"type": "string", "description": "Taker fee rate"},
                                    "makerFeeRate": {"type": "string", "description": "Maker fee rate"},
                                    "priceScale": {"type": "string", "description": "Price decimal scale"},
                                    "quantityScale": {"type": "string", "description": "Quantity decimal scale"},
                                    "status": {"type": "string", "description": "Status"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/spot/v1/public/currencies",
                "method": "GET",
                "authentication_required": False,
                "description": "Get list of all coins with basic data and supported chains",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "coinId": {"type": "string", "description": "Coin ID"},
                                    "coinName": {"type": "string", "description": "Coin name"},
                                    "coinDisplayName": {"type": "string", "description": "Coin display name"},
                                    "transfer": {"type": "string", "description": "Whether can be transferred"},
                                    "chains": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "chain": {"type": "string", "description": "Chain name"},
                                                "needTag": {"type": "string", "description": "Whether need tag"},
                                                "withdrawable": {"type": "string", "description": "Whether can be withdrawn"},
                                                "rechargeable": {"type": "string", "description": "Whether can be deposited"},
                                                "withdrawFee": {"type": "string", "description": "Withdrawal fee"},
                                                "depositConfirm": {"type": "string", "description": "Deposit confirmation blocks"},
                                                "withdrawConfirm": {"type": "string", "description": "Withdrawal confirmation blocks"},
                                                "minDepositAmount": {"type": "string", "description": "Minimum deposit amount"},
                                                "minWithdrawAmount": {"type": "string", "description": "Minimum withdrawal amount"},
                                                "browserUrl": {"type": "string", "description": "Blockchain browser URL"}
                                            }
                                        }
                                    }
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
                "path": "/api/spot/v1/market/ticker",
                "method": "GET",
                "authentication_required": False,
                "description": "Get single ticker information",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Symbol ID (e.g., BTCUSDT_SPBL)"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code (00000 = success)"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string", "description": "Symbol ID"},
                                "high24h": {"type": "string", "description": "24h highest price"},
                                "low24h": {"type": "string", "description": "24h lowest price"},
                                "close": {"type": "string", "description": "Latest transaction price"},
                                "quoteVol": {"type": "string", "description": "Denomination coin volume"},
                                "baseVol": {"type": "string", "description": "Base coin volume"},
                                "usdtVol": {"type": "string", "description": "USDT volume"},
                                "ts": {"type": "string", "description": "System timestamp in milliseconds"},
                                "buyOne": {"type": "string", "description": "Buy one price"},
                                "sellOne": {"type": "string", "description": "Sell one price"},
                                "bidSz": {"type": "string", "description": "Bid1 size"},
                                "askSz": {"type": "string", "description": "Ask1 size"},
                                "openUtc0": {"type": "string", "description": "UTC0 opening price"},
                                "changeUtc": {"type": "string", "description": "Change since UTC0"},
                                "change": {"type": "string", "description": "24h change"}
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/spot/v1/market/tickers",
                "method": "GET",
                "authentication_required": False,
                "description": "Get all tickers information",
                "query_parameters": {},
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string", "description": "Symbol ID"},
                                    "high24h": {"type": "string", "description": "24h highest price"},
                                    "low24h": {"type": "string", "description": "24h lowest price"},
                                    "close": {"type": "string", "description": "Latest transaction price"},
                                    "quoteVol": {"type": "string", "description": "Denomination coin volume"},
                                    "baseVol": {"type": "string", "description": "Base coin volume"},
                                    "usdtVol": {"type": "string", "description": "USDT volume"},
                                    "ts": {"type": "string", "description": "System timestamp"},
                                    "buyOne": {"type": "string", "description": "Buy one price"},
                                    "sellOne": {"type": "string", "description": "Sell one price"},
                                    "bidSz": {"type": "string", "description": "Bid1 size"},
                                    "askSz": {"type": "string", "description": "Ask1 size"},
                                    "openUtc0": {"type": "string", "description": "UTC0 open price"},
                                    "changeUtc": {"type": "string", "description": "Change since UTC0"},
                                    "change": {"type": "string", "description": "24h change"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/spot/v1/market/fills",
                "method": "GET",
                "authentication_required": False,
                "description": "Get most recent 500 trades",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Symbol ID"
                    },
                    "limit": {
                        "type": "string",
                        "required": False,
                        "description": "Default is 100, Max. is 500"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string", "description": "Symbol ID"},
                                    "tradeId": {"type": "string", "description": "Filled order ID"},
                                    "side": {"type": "string", "description": "Trade direction: buy or sell"},
                                    "fillPrice": {"type": "string", "description": "Transaction price, quote coin"},
                                    "fillQuantity": {"type": "string", "description": "Transaction quantity, base coin"},
                                    "fillTime": {"type": "string", "description": "Transaction time"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/spot/v1/market/fills-history",
                "method": "GET",
                "authentication_required": False,
                "description": "Fetch trade history within 30 days",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Symbol ID"
                    },
                    "limit": {
                        "type": "string",
                        "required": False,
                        "description": "Default is 500, Max is 1000"
                    },
                    "tradeId": {
                        "type": "string",
                        "required": False,
                        "description": "tradeId, return records with 'tradeId' less than the provided value"
                    },
                    "startTime": {
                        "type": "string",
                        "required": False,
                        "description": "startTime, ms"
                    },
                    "endTime": {
                        "type": "string",
                        "required": False,
                        "description": "endTime, ms"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symbol": {"type": "string", "description": "Symbol ID"},
                                    "tradeId": {"type": "string", "description": "Filled order ID, desc"},
                                    "side": {"type": "string", "description": "Trade direction: Buy or Sell"},
                                    "fillPrice": {"type": "string", "description": "Transaction price, quote coin"},
                                    "fillQuantity": {"type": "string", "description": "Transaction quantity, base coin"},
                                    "fillTime": {"type": "string", "description": "Transaction time"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/spot/v1/market/candles",
                "method": "GET",
                "authentication_required": False,
                "description": "Get candlestick line data",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Symbol ID"
                    },
                    "period": {
                        "type": "string",
                        "required": True,
                        "description": "Candlestick line time unit, granularity (1min, 5min, 15min, 30min, 1h, 4h, 6h, 12h, 1day, 3day, 1week, 1M, 6Hutc, 12Hutc, 1Dutc, 3Dutc, 1Wutc, 1Mutc)"
                    },
                    "after": {
                        "type": "string",
                        "required": False,
                        "description": "Time after, milliseconds, return greater than or equals"
                    },
                    "before": {
                        "type": "string",
                        "required": False,
                        "description": "Time before, milliseconds, return less than or equals"
                    },
                    "limit": {
                        "type": "string",
                        "required": False,
                        "description": "Default 100, max 1000"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "ts": {"type": "string", "description": "System timestamp"},
                                    "open": {"type": "string", "description": "Opening price"},
                                    "high": {"type": "string", "description": "Highest price"},
                                    "low": {"type": "string", "description": "Lowest price"},
                                    "close": {"type": "string", "description": "Closing price"},
                                    "baseVol": {"type": "string", "description": "Base coin volume"},
                                    "quoteVol": {"type": "string", "description": "Denomination coin volume"},
                                    "usdtVol": {"type": "string", "description": "USDT volume"}
                                }
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/spot/v1/market/depth",
                "method": "GET",
                "authentication_required": False,
                "description": "Get order book depth",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Symbol ID"
                    },
                    "type": {
                        "type": "string",
                        "required": True,
                        "description": "Default: step0; value: step0, step1, step2, step3, step4, step5"
                    },
                    "limit": {
                        "type": "string",
                        "required": False,
                        "description": "default 150, max 200"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "asks": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 2,
                                        "maxItems": 2
                                    },
                                    "description": "All buy orders at the current price"
                                },
                                "bids": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 2,
                                        "maxItems": 2
                                    },
                                    "description": "All sell orders at the current price"
                                },
                                "timestamp": {"type": "string", "description": "Timestamp"}
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
            {
                "path": "/api/spot/v1/market/merge-depth",
                "method": "GET",
                "authentication_required": False,
                "description": "Get merged depth data",
                "query_parameters": {
                    "symbol": {
                        "type": "string",
                        "required": True,
                        "description": "Trading pair name, e.g., BTCUSDT_SPBL"
                    },
                    "precision": {
                        "type": "string",
                        "required": False,
                        "description": "Price accuracy: scale0/scale1/scale2/scale3"
                    },
                    "limit": {
                        "type": "string",
                        "required": False,
                        "description": "Fixed gear enumeration value: 1/5/15/50/max, default 100"
                    }
                },
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Response code"},
                        "msg": {"type": "string", "description": "Response message"},
                        "requestTime": {"type": "integer", "description": "Request timestamp"},
                        "data": {
                            "type": "object",
                            "properties": {
                                "asks": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": 2,
                                        "maxItems": 2
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
                                "ts": {"type": "string", "description": "Timestamp"},
                                "scale": {"type": "string", "description": "Actual precision value"},
                                "precision": {"type": "string", "description": "Current gear"},
                                "isMaxPrecision": {"type": "string", "description": "YES/NO"}
                            }
                        }
                    }
                },
                "rate_limit_tier": "public"
            },
        ]
        endpoints.extend(market_data_endpoints)

        # ============================================================================
        # 3. AUTHENTICATED CHANNELS (Phase 3 - Optional for initial implementation)
        # ============================================================================

        # Bitget authenticated channels require login with:
        # - apiKey, passphrase, timestamp (seconds), sign (HMAC SHA256 + Base64)
        # Private channels: account (balances), orders (order updates)

        """
        authenticated_channels = [
            {
                "channel_name": "account",
                "authentication_required": True,
                "description": "Account updates (balance changes)",
                "subscribe_format": {
                    "op": "login",
                    "args": [{
                        "apiKey": "<api_key>",
                        "passphrase": "<passphrase>",
                        "timestamp": "<timestamp_seconds>",
                        "sign": "<signature>"
                    }]
                },
                "message_types": ["snapshot", "update"],
                "message_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "arg": {"type": "object"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "coinId": {"type": "string"},
                                    "coinName": {"type": "string"},
                                    "available": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "vendor_metadata": {
                    "requires_login": True,
                    "login_format": "HMAC SHA256 signature",
                    "update_types": ["balance"]
                }
            },
            {
                "channel_name": "orders",
                "authentication_required": True,
                "description": "Order updates (private spot channel)",
                "subscribe_format": {
                    "op": "subscribe",
                    "args": [{
                        "instType": "spbl",
                        "channel": "orders",
                        "instId": "<symbol>_SPBL"  # e.g., BTCUSDT_SPBL
                    }]
                },
                "unsubscribe_format": {
                    "op": "unsubscribe",
                    "args": [{
                        "instType": "spbl",
                        "channel": "orders",
                        "instId": "<symbol>_SPBL"
                    }]
                },
                "message_types": ["snapshot", "update"],
                "message_schema": {"type": "object"},
                "vendor_metadata": {
                    "requires_login": True,
                    "channel_pattern": "spbl:orders:{}"
                }
            }
        ]
        channels.extend(authenticated_channels)
        """


        # ============================================================================
        # 3. DYNAMIC DISCOVERY (Optional - if exchange provides endpoint listing)
        # ============================================================================

        # Some exchanges provide API endpoint listings. Example pattern:
        """
        try:
            # If exchange provides endpoint discovery endpoint
            discovery_url = f"{self.base_url}/api/v3/endpoints"
            response = self.http_client.get(discovery_url)

            for endpoint_info in response.get('endpoints', []):
                endpoint = {
                    "path": endpoint_info['path'],
                    "method": endpoint_info['method'],
                    "authentication_required": endpoint_info.get('auth_required', False),
                    "description": endpoint_info.get('description', ''),
                    "query_parameters": endpoint_info.get('params', {}),
                    "response_schema": endpoint_info.get('response_schema', {}),
                    "rate_limit_tier": endpoint_info.get('rate_limit', 'public')
                }
                endpoints.append(endpoint)

        except Exception as e:
            logger.warning(f"Dynamic endpoint discovery failed: {e}. Using static endpoints.")
        """

        logger.info(f"Discovered {len(endpoints)} REST endpoints")
        return endpoints

    def discover_websocket_channels(self) -> List[Dict[str, Any]]:
        """
        Discover Bitget WebSocket channels and message formats.

        Bitget WebSocket API Documentation:
        - URL: wss://ws.bitget.com/spot/v1/stream
        - Connection limit: 100 connections per IP
        - Subscription limit: 240 times per hour
        - Requires ping every 30 seconds to keep connection alive

        Implementation Strategy:
        1. Map public WebSocket channels from Bitget documentation
        2. Include subscribe/unsubscribe message formats (Bitget uses op/args format)
        3. Document message types and schemas based on Bitget API
        4. Note authentication requirements (login required for private channels)

        Returns:
            List of WebSocket channel dictionaries
        """
        logger.info("Discovering Bitget WebSocket channels")

        channels = []

        # ============================================================================
        # 1. MARKET DATA CHANNELS (Public)
        # ============================================================================

        # Ticker channel
        channels.append({
            "channel_name": "ticker",
            "authentication_required": False,
            "description": "Real-time ticker updates for trading pairs",
            "subscribe_format": {
                "op": "subscribe",
                "args": [{
                    "instType": "sp",
                    "channel": "ticker",
                    "instId": "<symbol>"  # Replace <symbol> with actual pair like "BTCUSDT"
                }]
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": [{
                    "instType": "sp",
                    "channel": "ticker",
                    "instId": "<symbol>"
                }]
            },
            "message_types": ["snapshot", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Push action (snapshot)"},
                    "arg": {
                        "type": "object",
                        "properties": {
                            "instType": {"type": "string", "description": "Instrument type (sp)"},
                            "channel": {"type": "string", "description": "Channel name"},
                            "instId": {"type": "string", "description": "Instrument ID"}
                        }
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "instId": {"type": "string", "description": "Instrument ID"},
                                "last": {"type": "string", "description": "Latest traded price"},
                                "open24h": {"type": "string", "description": "Open price in past 24h"},
                                "high24h": {"type": "string", "description": "Highest price in past 24h"},
                                "low24h": {"type": "string", "description": "Lowest price in past 24h"},
                                "bestBid": {"type": "string", "description": "Best bid price"},
                                "bestAsk": {"type": "string", "description": "Best ask price"},
                                "baseVolume": {"type": "string", "description": "24h base coin volume"},
                                "quoteVolume": {"type": "string", "description": "24h quote coin volume"},
                                "ts": {"type": "integer", "description": "Timestamp in milliseconds"},
                                "bidSz": {"type": "string", "description": "Best bid size"},
                                "askSz": {"type": "string", "description": "Best ask size"}
                            }
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "sp:ticker:{}",
                "supports_multiple_symbols": True,
                "update_frequency": "real-time",
                "rate_limit": "20 requests per second"
            }
        })

        # Order book channels (multiple depth levels)
        # Bitget supports books5 (top 5), books15 (top 15), and books (full)
        depth_channels = [
            {
                "channel_name": "books5",
                "authentication_required": False,
                "description": "Top 5 levels of order book (snapshot)",
                "subscribe_format": {
                    "op": "subscribe",
                    "args": [{
                        "instType": "sp",
                        "channel": "books5",
                        "instId": "<symbol>"
                    }]
                },
                "unsubscribe_format": {
                    "op": "unsubscribe",
                    "args": [{
                        "instType": "sp",
                        "channel": "books5",
                        "instId": "<symbol>"
                    }]
                },
                "message_types": ["snapshot", "subscription"],
                "message_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "description": "Push action (snapshot)"},
                        "arg": {
                            "type": "object",
                            "properties": {
                                "instType": {"type": "string"},
                                "channel": {"type": "string"},
                                "instId": {"type": "string"}
                            }
                        },
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "asks": {
                                        "type": "array",
                                        "items": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "minItems": 2,
                                            "maxItems": 2
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
                                    "ts": {"type": "string", "description": "Timestamp"},
                                    "checksum": {"type": "integer", "description": "CRC32 checksum"}
                                }
                            }
                        }
                    }
                },
                "vendor_metadata": {
                    "channel_pattern": "sp:books5:{}",
                    "levels": 5,
                    "update_type": "snapshot",
                    "checksum_verification": True
                }
            },
            {
                "channel_name": "books15",
                "authentication_required": False,
                "description": "Top 15 levels of order book (snapshot)",
                "subscribe_format": {
                    "op": "subscribe",
                    "args": [{
                        "instType": "sp",
                        "channel": "books15",
                        "instId": "<symbol>"
                    }]
                },
                "unsubscribe_format": {
                    "op": "unsubscribe",
                    "args": [{
                        "instType": "sp",
                        "channel": "books15",
                        "instId": "<symbol>"
                    }]
                },
                "message_types": ["snapshot", "subscription"],
                "message_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "arg": {"type": "object"},
                        "data": {"type": "array"}
                    }
                },
                "vendor_metadata": {
                    "channel_pattern": "sp:books15:{}",
                    "levels": 15,
                    "update_type": "snapshot"
                }
            }
        ]
        channels.extend(depth_channels)

        # Trade channel
        channels.append({
            "channel_name": "trade",
            "authentication_required": False,
            "description": "Real-time trade execution updates",
            "subscribe_format": {
                "op": "subscribe",
                "args": [{
                    "instType": "sp",
                    "channel": "trade",
                    "instId": "<symbol>"
                }]
            },
            "unsubscribe_format": {
                "op": "unsubscribe",
                "args": [{
                    "instType": "sp",
                    "channel": "trade",
                    "instId": "<symbol>"
                }]
            },
            "message_types": ["trade", "subscription"],
            "message_schema": {
                "type": "object",
                "properties": {
                    "arg": {
                        "type": "object",
                        "properties": {
                            "instType": {"type": "string"},
                            "channel": {"type": "string"},
                            "instId": {"type": "string"}
                        }
                    },
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ts": {"type": "string", "description": "Filled time in milliseconds"},
                                "px": {"type": "string", "description": "Trade price"},
                                "sz": {"type": "string", "description": "Trade size"},
                                "side": {"type": "string", "description": "Trade direction (buy/sell)"}
                            }
                        }
                    }
                }
            },
            "vendor_metadata": {
                "channel_pattern": "sp:trade:{}",
                "trade_type": "individual",
                "update_frequency": "real-time on trade"
            }
        })

        # Candlestick channels (multiple intervals)
        candle_intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "6h", "12h", "1D", "3D", "1W", "1M"]

        for interval in candle_intervals:
            channel_name = f"candle{interval}"
            channels.append({
                "channel_name": channel_name,
                "authentication_required": False,
                "description": f"Real-time {interval} candlestick updates",
                "subscribe_format": {
                    "op": "subscribe",
                    "args": [{
                        "instType": "sp",
                        "channel": channel_name,
                        "instId": "<symbol>"
                    }]
                },
                "unsubscribe_format": {
                    "op": "unsubscribe",
                    "args": [{
                        "instType": "sp",
                        "channel": channel_name,
                        "instId": "<symbol>"
                    }]
                },
                "message_types": ["candle", "subscription"],
                "message_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "arg": {"type": "object"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 7,
                                "maxItems": 7,
                                "description": "[ts, open, high, low, close, baseVol, quoteVol]"
                            }
                        }
                    }
                },
                "vendor_metadata": {
                    "channel_pattern": f"sp:{channel_name}:{{}}",
                    "interval": interval,
                    "update_frequency": f"every {interval}"
                }
            })

        # ============================================================================
        # 2. HEARTBEAT/CONNECTION MANAGEMENT
        # ============================================================================

        # Connection management (ping/pong)
        channels.append({
            "channel_name": "ping",
            "authentication_required": False,
            "description": "Connection heartbeat - send 'ping' string, expect 'pong' response",
            "subscribe_format": {
                "manual": True,
                "description": "Send string 'ping' every 30 seconds"
            },
            "unsubscribe_format": {
                "manual": True,
                "description": "Connection close"
            },
            "message_types": ["pong"],
            "message_schema": {
                "type": "string",
                "description": "Expected response: 'pong'"
            },
            "vendor_metadata": {
                "keepalive_interval": 30000,
                "auto_reconnect": True,
                "ping_required": True,
                "timeout_seconds": 120
            }
        })

        # ============================================================================
        # 3. AUTHENTICATED CHANNELS (Phase 3 - Optional)
        # ============================================================================

        """
        channels.append({
            "channel_name": "account",
            "authentication_required": True,
            "description": "Account updates (balance changes, orders, etc.)",
            "subscribe_format": {
                "type": "auth",
                "method": "LOGIN",
                "params": ["api_key", "signature", "timestamp"]
            },
            "message_types": ["outboundAccountInfo", "executionReport", "balanceUpdate"],
            "message_schema": {"type": "object"},
            "vendor_metadata": {
                "requires_signature": True,
                "update_types": ["balance", "order", "trade"]
            }
        })
        """

        logger.info(f"Discovered {len(channels)} WebSocket channels")
        return channels

    def discover_products(self) -> List[Dict[str, Any]]:
        """
        Discover Bitget trading products/symbols from live API.

        IMPORTANT: This method MUST make live API calls to fetch actual products.
        Fetch from Bitget's product endpoint: /api/v2/spot/public/symbols

        Implementation Steps:
        1. Call Bitget's products endpoint
        2. Parse the response to extract symbol information
        3. Map to our standard product format
        4. Handle status mapping (online, gray, offline)
        5. Implement error handling and retry logic

        Returns:
            List of product dictionaries in standard format
        """
        logger.info("Discovering Bitget products from live API")

        try:
            # ========================================================================
            # 1. FETCH PRODUCTS FROM BITGET API
            # ========================================================================

            # Bitget's product endpoint for spot trading
            products_url = f"{self.base_url}/api/v2/spot/public/symbols"

            logger.debug(f"Fetching products from: {products_url}")

            # Make the API request
            response = self.http_client.get(products_url)

            # ========================================================================
            # 2. PARSE RESPONSE BASED ON BITGET FORMAT
            # ========================================================================

            products = []

            # Bitget response format: {"code": "00000", "msg": "success", "requestTime": ..., "data": [...]}
            if 'data' not in response:
                logger.error(f"Unexpected response format from Bitget: {response}")
                raise Exception("No 'data' field in Bitget API response")

            symbols_data = response['data']

            # Ensure we have an iterable
            if not isinstance(symbols_data, list):
                logger.error(f"Unexpected response format: {type(symbols_data)}")
                raise Exception(f"Unexpected response format from Bitget")

            # ========================================================================
            # 3. PROCESS EACH SYMBOL/PRODUCT
            # ========================================================================

            for symbol_info in symbols_data:
                try:
                    # Extract fields from Bitget v2 API format
                    symbol = symbol_info.get('symbol')  # e.g., "LUMIAUSDT"
                    base_currency = symbol_info.get('baseCoin')  # e.g., "LUMIA"
                    quote_currency = symbol_info.get('quoteCoin')  # e.g., "USDT"

                    # Status mapping: online, gray, offline
                    status_raw = symbol_info.get('status', '').lower()
                    if status_raw == 'online':
                        status = 'online'
                    elif status_raw == 'gray':
                        status = 'online'  # Gray typically means limited trading
                    elif status_raw == 'offline':
                        status = 'offline'
                    else:
                        status = 'offline'  # Default if unknown

                    # Trading limits (available as strings in Bitget response)
                    min_order_size = None
                    max_order_size = None
                    price_increment = None

                    # Min/Max trade amounts
                    min_trade_amount = symbol_info.get('minTradeAmount')
                    max_trade_amount = symbol_info.get('maxTradeAmount')

                    if min_trade_amount:
                        try:
                            min_order_size = float(min_trade_amount)
                        except ValueError:
                            logger.debug(f"Could not parse minTradeAmount: {min_trade_amount}")

                    if max_trade_amount:
                        try:
                            max_order_size = float(max_trade_amount)
                        except ValueError:
                            logger.debug(f"Could not parse maxTradeAmount: {max_trade_amount}")

                    # Price increment from pricePrecision (decimal places)
                    price_precision = symbol_info.get('pricePrecision')
                    if price_precision:
                        try:
                            # pricePrecision indicates number of decimal places
                            # e.g., pricePrecision="4" means 0.0001 increment
                            scale = int(price_precision)
                            price_increment = 10 ** (-scale)
                        except ValueError:
                            logger.debug(f"Could not parse pricePrecision: {price_precision}")

                    # Create product dictionary
                    product = {
                        "symbol": symbol,
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                        "status": status,
                        "min_order_size": min_order_size,
                        "max_order_size": max_order_size,
                        "price_increment": price_increment,
                        "vendor_metadata": symbol_info  # Store full raw data
                    }

                    # Validate required fields
                    if not all([product["symbol"], product["base_currency"], product["quote_currency"]]):
                        logger.warning(f"Skipping product with missing required fields: {symbol_info}")
                        continue

                    products.append(product)

                except Exception as e:
                    logger.warning(f"Failed to parse product {symbol_info.get('symbol', 'unknown')}: {e}")
                    continue

            # ========================================================================
            # 4. VALIDATE AND RETURN RESULTS
            # ========================================================================

            if not products:
                logger.error("No products discovered from API response")
                raise Exception("No products found in Bitget API response")

            logger.info(f"Discovered {len(products)} products from Bitget")

            return products

        except Exception as e:
            logger.error(f"Failed to discover Bitget products: {e}")
            # Re-raise to ensure discovery run is marked as failed
            raise Exception(f"Product discovery failed for Bitget: {e}")

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
