#!/usr/bin/env python3
"""
REST Endpoint Mapping Demonstration Script

Demonstrates how to create canonical field mappings for REST API endpoints.
This shows mapping REST ticker endpoints for all 4 exchanges to canonical fields.
Some fields missing from WebSocket may be available via REST (e.g., volume_30d).

Usage:
  python create_rest_mappings_demo.py --dry-run    # Show what would be mapped
  python create_rest_mappings_demo.py --create     # Create actual mappings
  python create_rest_mappings_demo.py --verify     # Verify existing mappings
"""

import sqlite3
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


class RestTickerMapper:
    """
    Maps REST API ticker endpoints to canonical fields.

    Demonstrates how REST endpoints can provide fields that may be missing
    from WebSocket feeds (e.g., volume_30d, open_24h for Bitfinex).
    """

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize mapper with database path.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establish database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_vendor_id(self, vendor_name: str) -> Optional[int]:
        """
        Get vendor ID by name.

        Args:
            vendor_name: Vendor name (e.g., 'coinbase', 'binance')

        Returns:
            Vendor ID or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT vendor_id FROM vendors WHERE vendor_name = ?", (vendor_name,))
        row = cursor.fetchone()
        return row['vendor_id'] if row else None

    def get_endpoint_id(self, vendor_id: int, path: str, method: str = 'GET') -> Optional[int]:
        """
        Get REST endpoint ID by vendor and path.

        Args:
            vendor_id: Vendor ID
            path: Endpoint path (e.g., '/products/{product_id}/ticker')
            method: HTTP method (default: 'GET')

        Returns:
            Endpoint ID or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT endpoint_id FROM rest_endpoints
            WHERE vendor_id = ? AND path = ? AND method = ?
        """, (vendor_id, path, method))
        row = cursor.fetchone()
        return row['endpoint_id'] if row else None

    def get_canonical_field_id(self, field_name: str) -> Optional[int]:
        """
        Get canonical field ID by name.

        Args:
            field_name: Canonical field name (e.g., 'bid_price', 'volume_24h')

        Returns:
            Canonical field ID or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT canonical_field_id FROM canonical_fields
            WHERE field_name = ?
        """, (field_name,))
        row = cursor.fetchone()
        return row['canonical_field_id'] if row else None

    def create_field_mapping(
        self,
        vendor_id: int,
        canonical_field_id: int,
        vendor_field_path: str,
        endpoint_id: int,
        entity_type: str = 'ticker',
        transformation_rule: Optional[Dict] = None,
        priority: int = 0
    ) -> bool:
        """
        Create a REST field mapping entry.

        Args:
            vendor_id: Vendor ID
            canonical_field_id: Canonical field ID
            vendor_field_path: Vendor-specific field path (e.g., 'best_bid')
            endpoint_id: REST endpoint ID
            entity_type: Data type (ticker, order_book, trade, candle)
            transformation_rule: Optional transformation rules JSON
            priority: Mapping priority (higher = preferred)

        Returns:
            True if mapping created or already exists, False on error
        """
        cursor = self.conn.cursor()

        # Check if mapping already exists
        cursor.execute("""
            SELECT mapping_id FROM field_mappings
            WHERE vendor_id = ? AND canonical_field_id = ?
            AND vendor_field_path = ? AND endpoint_id = ?
            AND source_type = 'rest'
        """, (vendor_id, canonical_field_id, vendor_field_path, endpoint_id))

        if cursor.fetchone():
            logger.debug(f"REST mapping already exists: {vendor_field_path} -> {canonical_field_id}")
            return True

        try:
            # Serialize transformation rule
            transform_json = json.dumps(transformation_rule) if transformation_rule else None

            cursor.execute("""
                INSERT INTO field_mappings (
                    vendor_id,
                    canonical_field_id,
                    source_type,
                    entity_type,
                    vendor_field_path,
                    endpoint_id,
                    transformation_rule,
                    priority,
                    is_active
                ) VALUES (?, ?, 'rest', ?, ?, ?, ?, ?, TRUE)
            """, (
                vendor_id,
                canonical_field_id,
                entity_type,
                vendor_field_path,
                endpoint_id,
                transform_json,
                priority
            ))

            self.conn.commit()
            logger.info(f"Created REST mapping: {vendor_field_path} -> canonical field {canonical_field_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error creating REST mapping: {e}")
            self.conn.rollback()
            return False

    def map_coinbase_rest_ticker(self) -> int:
        """
        Map Coinbase REST ticker endpoint to canonical fields.

        Coinbase REST ticker endpoint: /products/{product_id}/ticker
        Provides similar fields to WebSocket but via REST.

        Returns:
            Number of mappings created
        """
        vendor_id = self.get_vendor_id('coinbase')
        if not vendor_id:
            logger.error("Coinbase vendor not found")
            return 0

        endpoint_id = self.get_endpoint_id(vendor_id, '/products/{product_id}/ticker')
        if not endpoint_id:
            logger.error("Coinbase ticker REST endpoint not found")
            return 0

        # Coinbase REST ticker fields (from API documentation)
        # Response includes: price, size, bid, ask, volume, open_24h, high_24h, low_24h
        # Note: REST might have different field names than WebSocket
        mappings = [
            # Format: (vendor_field_path, canonical_field_name, transformation_rule, entity_type)
            ('bid', 'bid_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('ask', 'ask_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('price', 'last_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('volume', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('high', 'high_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('low', 'low_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('open', 'open_24h', {'type': 'string_to_numeric'}, 'ticker'),
            # Note: Coinbase REST doesn't have volume_30d in ticker endpoint
            # Note: REST has 'trade_id' not in canonical ticker fields
        ]

        created_count = 0
        failed_count = 0

        for vendor_path, canonical_name, transform_rule, entity_type in mappings:
            canonical_field_id = self.get_canonical_field_id(canonical_name)
            if not canonical_field_id:
                logger.warning(f"Canonical field not found: {canonical_name}")
                failed_count += 1
                continue

            if self.create_field_mapping(
                vendor_id=vendor_id,
                canonical_field_id=canonical_field_id,
                vendor_field_path=vendor_path,
                endpoint_id=endpoint_id,
                entity_type=entity_type,
                transformation_rule=transform_rule
            ):
                created_count += 1
            else:
                failed_count += 1

        logger.info(f"Coinbase REST ticker mapping: {created_count} created, {failed_count} failed")
        return created_count

    def map_binance_rest_ticker(self) -> int:
        """
        Map Binance REST 24hr ticker endpoint to canonical fields.

        Binance REST ticker endpoint: /api/v3/ticker/24hr
        Provides comprehensive 24-hour statistics.

        Returns:
            Number of mappings created
        """
        vendor_id = self.get_vendor_id('binance')
        if not vendor_id:
            logger.error("Binance vendor not found")
            return 0

        endpoint_id = self.get_endpoint_id(vendor_id, '/api/v3/ticker/24hr')
        if not endpoint_id:
            logger.error("Binance 24hr ticker REST endpoint not found")
            return 0

        # Binance REST 24hr ticker fields
        # Response includes: symbol, priceChange, priceChangePercent,
        # weightedAvgPrice, prevClosePrice, lastPrice, lastQty, bidPrice,
        # bidQty, askPrice, askQty, openPrice, highPrice, lowPrice, volume,
        # quoteVolume, openTime, closeTime, firstId, lastId, count
        mappings = [
            ('bidPrice', 'bid_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('bidQty', 'best_bid_size', {'type': 'string_to_numeric'}, 'ticker'),
            ('askPrice', 'ask_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('askQty', 'best_ask_size', {'type': 'string_to_numeric'}, 'ticker'),
            ('lastPrice', 'last_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('highPrice', 'high_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('lowPrice', 'low_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('openPrice', 'open_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('volume', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('symbol', 'symbol', {'type': 'identity'}, 'ticker'),
            ('closeTime', 'timestamp', {'type': 'ms_to_datetime'}, 'ticker'),
            # Note: Binance REST has quoteVolume, priceChange, count which
            # don't have direct canonical equivalents
        ]

        created_count = 0
        failed_count = 0

        for vendor_path, canonical_name, transform_rule, entity_type in mappings:
            canonical_field_id = self.get_canonical_field_id(canonical_name)
            if not canonical_field_id:
                logger.warning(f"Canonical field not found: {canonical_name}")
                failed_count += 1
                continue

            if self.create_field_mapping(
                vendor_id=vendor_id,
                canonical_field_id=canonical_field_id,
                vendor_field_path=vendor_path,
                endpoint_id=endpoint_id,
                entity_type=entity_type,
                transformation_rule=transform_rule
            ):
                created_count += 1
            else:
                failed_count += 1

        logger.info(f"Binance REST ticker mapping: {created_count} created, {failed_count} failed")
        return created_count

    def map_kraken_rest_ticker(self) -> int:
        """
        Map Kraken REST ticker endpoint to canonical fields.

        Kraken REST ticker endpoint: /0/public/Ticker
        Provides array data similar to WebSocket but via REST.

        Returns:
            Number of mappings created
        """
        vendor_id = self.get_vendor_id('kraken')
        if not vendor_id:
            logger.error("Kraken vendor not found")
            return 0

        endpoint_id = self.get_endpoint_id(vendor_id, '/0/public/Ticker')
        if not endpoint_id:
            logger.error("Kraken ticker REST endpoint not found")
            return 0

        # Kraken REST ticker uses nested objects with arrays
        # Format: result.<PAIR>.a = [price, whole_lot_volume, lot_volume]
        # We'll use dot notation paths to extract from nested response
        mappings = [
            # Format: (vendor_field_path, canonical_field_name, transformation_rule, entity_type)
            # Note: In practice, would need to handle dynamic pair extraction
            # For demo, we'll use generic paths assuming pair extraction
            ('result.{pair}.a[0]', 'ask_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('result.{pair}.b[0]', 'bid_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('result.{pair}.c[0]', 'last_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('result.{pair}.h[1]', 'high_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('result.{pair}.l[1]', 'low_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('result.{pair}.o', 'open_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('result.{pair}.v[1]', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),
            # Kraken REST has 'p' = volume weighted average price (vwap)
            # Not in canonical set but could be useful
        ]

        created_count = 0
        failed_count = 0

        for vendor_path, canonical_name, transform_rule, entity_type in mappings:
            canonical_field_id = self.get_canonical_field_id(canonical_name)
            if not canonical_field_id:
                logger.warning(f"Canonical field not found: {canonical_name}")
                failed_count += 1
                continue

            if self.create_field_mapping(
                vendor_id=vendor_id,
                canonical_field_id=canonical_field_id,
                vendor_field_path=vendor_path,
                endpoint_id=endpoint_id,
                entity_type=entity_type,
                transformation_rule=transform_rule
            ):
                created_count += 1
            else:
                failed_count += 1

        logger.info(f"Kraken REST ticker mapping: {created_count} created, {failed_count} failed")
        return created_count

    def map_bitfinex_rest_ticker(self) -> int:
        """
        Map Bitfinex REST ticker endpoint to canonical fields.

        Bitfinex REST ticker endpoint: /v2/ticker/{symbol}
        May provide fields missing from WebSocket (like open_24h).

        Returns:
            Number of mappings created
        """
        vendor_id = self.get_vendor_id('bitfinex')
        if not vendor_id:
            logger.error("Bitfinex vendor not found")
            return 0

        endpoint_id = self.get_endpoint_id(vendor_id, '/v2/ticker/{symbol}')
        if not endpoint_id:
            logger.error("Bitfinex ticker REST endpoint not found")
            return 0

        # Bitfinex REST ticker returns array (positional fields)
        # According to documentation: [BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE,
        # DAILY_CHANGE_RELATIVE, LAST_PRICE, VOLUME, HIGH, LOW]
        # We'll map array indices to canonical fields
        mappings = [
            # Format: (vendor_field_path, canonical_field_name, transformation_rule, entity_type)
            ('[0]', 'bid_price', {'type': 'identity'}, 'ticker'),           # BID
            ('[1]', 'best_bid_size', {'type': 'identity'}, 'ticker'),      # BID_SIZE
            ('[2]', 'ask_price', {'type': 'identity'}, 'ticker'),          # ASK
            ('[3]', 'best_ask_size', {'type': 'identity'}, 'ticker'),      # ASK_SIZE
            ('[6]', 'last_price', {'type': 'identity'}, 'ticker'),         # LAST_PRICE
            ('[7]', 'volume_24h', {'type': 'identity'}, 'ticker'),         # VOLUME
            ('[8]', 'high_24h', {'type': 'identity'}, 'ticker'),           # HIGH
            ('[9]', 'low_24h', {'type': 'identity'}, 'ticker'),            # LOW
            # Note: Bitfinex REST has DAILY_CHANGE ([4]) and DAILY_CHANGE_RELATIVE ([5])
            # which don't have canonical equivalents
        ]

        created_count = 0
        failed_count = 0

        for vendor_path, canonical_name, transform_rule, entity_type in mappings:
            canonical_field_id = self.get_canonical_field_id(canonical_name)
            if not canonical_field_id:
                logger.warning(f"Canonical field not found: {canonical_name}")
                failed_count += 1
                continue

            if self.create_field_mapping(
                vendor_id=vendor_id,
                canonical_field_id=canonical_field_id,
                vendor_field_path=vendor_path,
                endpoint_id=endpoint_id,
                entity_type=entity_type,
                transformation_rule=transform_rule
            ):
                created_count += 1
            else:
                failed_count += 1

        logger.info(f"Bitfinex REST ticker mapping: {created_count} created, {failed_count} failed")
        return created_count

    def map_all_rest_tickers(self) -> Dict[str, int]:
        """
        Map REST ticker endpoints for all exchanges.

        Returns:
            Dictionary with mapping counts per exchange
        """
        results = {}

        logger.info("Starting REST ticker mapping for all exchanges...")

        # Coinbase
        coinbase_count = self.map_coinbase_rest_ticker()
        results['coinbase'] = coinbase_count

        # Binance
        binance_count = self.map_binance_rest_ticker()
        results['binance'] = binance_count

        # Kraken
        kraken_count = self.map_kraken_rest_ticker()
        results['kraken'] = kraken_count

        # Bitfinex
        bitfinex_count = self.map_bitfinex_rest_ticker()
        results['bitfinex'] = bitfinex_count

        total = sum(results.values())
        logger.info(f"Total REST ticker mappings created: {total}")

        return results

    def verify_mappings(self) -> Dict[str, Any]:
        """
        Verify existing REST mappings.

        Returns:
            Dictionary with verification statistics
        """
        cursor = self.conn.cursor()

        # Count total REST mappings
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM field_mappings
            WHERE source_type = 'rest'
        """)
        total_mappings = cursor.fetchone()['count']

        # Count by vendor
        cursor.execute("""
            SELECT v.vendor_name, COUNT(*) as count
            FROM field_mappings fm
            JOIN vendors v ON fm.vendor_id = v.vendor_id
            WHERE fm.source_type = 'rest'
            GROUP BY v.vendor_id
            ORDER BY v.vendor_name
        """)

        by_vendor = {}
        for row in cursor.fetchall():
            by_vendor[row['vendor_name']] = row['count']

        # Check coverage for ticker data type
        cursor.execute("""
            SELECT
                v.vendor_name,
                dt.data_type_name,
                COUNT(DISTINCT cf.canonical_field_id) as fields_defined,
                COUNT(DISTINCT fm.canonical_field_id) as fields_mapped,
                ROUND(COUNT(DISTINCT fm.canonical_field_id) * 100.0 /
                      COUNT(DISTINCT cf.canonical_field_id), 1) as coverage_percent
            FROM vendors v
            CROSS JOIN canonical_data_types dt
            JOIN data_type_fields dtf ON dt.data_type_id = dtf.data_type_id
            JOIN canonical_fields cf ON dtf.canonical_field_id = cf.canonical_field_id
            LEFT JOIN field_mappings fm ON v.vendor_id = fm.vendor_id
                AND cf.canonical_field_id = fm.canonical_field_id
                AND fm.is_active = TRUE
                AND fm.entity_type = dt.data_type_name
                AND fm.source_type = 'rest'
            WHERE dt.data_type_name = 'ticker'
            GROUP BY v.vendor_id, dt.data_type_id
            ORDER BY v.vendor_name
        """)

        coverage = []
        for row in cursor.fetchall():
            coverage.append(dict(row))

        return {
            'total_rest_mappings': total_mappings,
            'by_vendor': by_vendor,
            'ticker_coverage': coverage
        }

    def dry_run_display(self):
        """
        Display what would be mapped without creating actual entries.
        """
        print("REST ENDPOINT MAPPING DEMONSTRATION")
        print("=" * 70)
        print("This shows how REST endpoints can fill gaps in WebSocket coverage")
        print("Some fields missing from WebSocket may be available via REST")
        print()

        exchanges = [
            ('coinbase', '/products/{product_id}/ticker', [
                ('bid', 'bid_price', 'Direct mapping from REST field'),
                ('ask', 'ask_price', 'Direct mapping from REST field'),
                ('price', 'last_price', 'Direct mapping from REST field'),
                ('volume', 'volume_24h', 'Direct mapping from REST field'),
                ('high', 'high_24h', 'Direct mapping from REST field'),
                ('low', 'low_24h', 'Direct mapping from REST field'),
                ('open', 'open_24h', 'Direct mapping from REST field'),
            ]),

            ('binance', '/api/v3/ticker/24hr', [
                ('bidPrice', 'bid_price', 'Direct mapping from REST field'),
                ('bidQty', 'best_bid_size', 'Fills WebSocket gap (size available)'),
                ('askPrice', 'ask_price', 'Direct mapping from REST field'),
                ('askQty', 'best_ask_size', 'Fills WebSocket gap (size available)'),
                ('lastPrice', 'last_price', 'Direct mapping from REST field'),
                ('highPrice', 'high_24h', 'Direct mapping from REST field'),
                ('lowPrice', 'low_24h', 'Direct mapping from REST field'),
                ('openPrice', 'open_24h', 'Direct mapping from REST field'),
                ('volume', 'volume_24h', 'Direct mapping from REST field'),
                ('symbol', 'symbol', 'Direct mapping from REST field'),
                ('closeTime', 'timestamp', 'ms_to_datetime conversion'),
            ]),

            ('kraken', '/0/public/Ticker', [
                ('result.{pair}.a[0]', 'ask_price', 'Array extraction from REST'),
                ('result.{pair}.b[0]', 'bid_price', 'Array extraction from REST'),
                ('result.{pair}.c[0]', 'last_price', 'Array extraction from REST'),
                ('result.{pair}.h[1]', 'high_24h', 'Array extraction from REST'),
                ('result.{pair}.l[1]', 'low_24h', 'Array extraction from REST'),
                ('result.{pair}.o', 'open_24h', 'Direct mapping from REST'),
                ('result.{pair}.v[1]', 'volume_24h', 'Array extraction from REST'),
            ]),

            ('bitfinex', '/v2/ticker/{symbol}', [
                ('[0]', 'bid_price', 'Array index 0 (BID)'),
                ('[1]', 'best_bid_size', 'Array index 1 (BID_SIZE) - fills gap'),
                ('[2]', 'ask_price', 'Array index 2 (ASK)'),
                ('[3]', 'best_ask_size', 'Array index 3 (ASK_SIZE) - fills gap'),
                ('[6]', 'last_price', 'Array index 6 (LAST_PRICE)'),
                ('[7]', 'volume_24h', 'Array index 7 (VOLUME)'),
                ('[8]', 'high_24h', 'Array index 8 (HIGH)'),
                ('[9]', 'low_24h', 'Array index 9 (LOW)'),
            ]),
        ]

        total_potential = 0

        for vendor_name, endpoint_path, mappings in exchanges:
            print(f"\n{vendor_name.upper()} - {endpoint_path}")
            print("-" * 70)

            vendor_id = self.get_vendor_id(vendor_name)
            endpoint_id = self.get_endpoint_id(vendor_id, endpoint_path) if vendor_id else None

            status = "✓ Endpoint found" if endpoint_id else "✗ Endpoint not found"
            print(f"Status: {status}")

            for i, (vendor_path, canonical_name, description) in enumerate(mappings, 1):
                field_id = self.get_canonical_field_id(canonical_name)
                field_status = "✓ Field exists" if field_id else "✗ Field not found"

                print(f"  {i:2}. {vendor_path:25} → {canonical_name:20} | {description}")
                print(f"       {field_status}")

            total_potential += len(mappings)

        print(f"\n{'=' * 70}")
        print(f"Total potential REST mappings: {total_potential}")
        print("\nKey benefits of REST mappings:")
        print("1. Fill gaps in WebSocket coverage (e.g., bid/ask sizes)")
        print("2. Provide alternative data sources for redundancy")
        print("3. Enable hybrid WebSocket+REST data pipelines")
        print("4. Access historical data not available via WebSocket")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='REST Endpoint Mapping Demonstration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show what would be mapped (dry run)
  python create_rest_mappings_demo.py --dry-run

  # Create actual REST mappings
  python create_rest_mappings_demo.py --create

  # Verify existing REST mappings
  python create_rest_mappings_demo.py --verify

  # Create mappings and verify
  python create_rest_mappings_demo.py --create --verify
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be mapped without creating actual entries'
    )

    parser.add_argument(
        '--create',
        action='store_true',
        help='Create actual REST endpoint mappings'
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify existing REST mappings after creation'
    )

    args = parser.parse_args()

    if not any([args.dry_run, args.create, args.verify]):
        parser.print_help()
        return

    with RestTickerMapper() as mapper:
        if args.dry_run:
            mapper.dry_run_display()

        if args.create:
            print("\nCreating REST endpoint mappings...")
            print("=" * 70)

            results = mapper.map_all_rest_tickers()

            print("\nMapping Results:")
            print("-" * 70)
            for vendor, count in results.items():
                print(f"{vendor}: {count} mappings created")

            total = sum(results.values())
            print(f"\nTotal: {total} REST mappings created")

        if args.verify:
            print("\nVerifying REST mappings...")
            print("=" * 70)

            stats = mapper.verify_mappings()

            print(f"Total REST mappings: {stats['total_rest_mappings']}")

            if stats['by_vendor']:
                print("\nMappings by vendor:")
                for vendor, count in stats['by_vendor'].items():
                    print(f"  {vendor}: {count}")

            if stats['ticker_coverage']:
                print("\nREST Ticker Coverage:")
                for cov in stats['ticker_coverage']:
                    if cov['fields_mapped'] > 0:
                        print(f"  {cov['vendor_name']}: {cov['fields_mapped']}/{cov['fields_defined']} "
                              f"({cov['coverage_percent']}%)")


if __name__ == '__main__':
    main()
