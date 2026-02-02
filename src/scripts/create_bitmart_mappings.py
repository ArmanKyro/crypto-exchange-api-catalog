#!/usr/bin/env python3
"""
Create BitMart WebSocket ticker field mappings to canonical fields.
Maps BitMart-specific field names to industry-standard canonical field names.
"""

import argparse
import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import DATABASE_PATH
from src.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


class BitmartTickerMapper:
    """
    Maps BitMart WebSocket ticker fields to canonical fields.
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

    def get_vendor_id(self, vendor_name: str = 'bitmart') -> Optional[int]:
        """
        Get vendor ID for BitMart.

        Args:
            vendor_name: Vendor name (default: 'bitmart')

        Returns:
            vendor_id or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT vendor_id FROM vendors WHERE vendor_name = ?",
            (vendor_name,)
        )
        row = cursor.fetchone()
        return row['vendor_id'] if row else None

    def get_websocket_channel_id(self, vendor_id: int, channel_name: str = 'spot/ticker') -> Optional[int]:
        """
        Get WebSocket channel ID for ticker channel.

        Args:
            vendor_id: Vendor ID
            channel_name: Channel name (default: 'spot/ticker')

        Returns:
            channel_id or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT channel_id FROM websocket_channels WHERE vendor_id = ? AND channel_name = ?",
            (vendor_id, channel_name)
        )
        row = cursor.fetchone()
        return row['channel_id'] if row else None

    def get_canonical_field_id(self, field_name: str) -> Optional[int]:
        """
        Get canonical field ID by field name.

        Args:
            field_name: Canonical field name (e.g., 'bid_price')

        Returns:
            canonical_field_id or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT canonical_field_id FROM canonical_fields WHERE field_name = ?",
            (field_name,)
        )
        row = cursor.fetchone()
        return row['canonical_field_id'] if row else None

    def create_field_mapping(
        self,
        vendor_id: int,
        canonical_field_id: int,
        vendor_field_path: str,
        channel_id: int,
        entity_type: str = 'ticker',
        transformation_rule: Optional[Dict] = None,
        priority: int = 0
    ) -> bool:
        """
        Create a field mapping entry.

        Args:
            vendor_id: Vendor ID
            canonical_field_id: Canonical field ID
            vendor_field_path: Vendor-specific field path (e.g., 'data[].last_price')
            channel_id: WebSocket channel ID
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
            AND vendor_field_path = ? AND channel_id = ?
        """, (vendor_id, canonical_field_id, vendor_field_path, channel_id))

        if cursor.fetchone():
            logger.debug(f"Mapping already exists: {vendor_field_path} -> {canonical_field_id}")
            return True

        try:
            cursor.execute("""
                INSERT INTO field_mappings (
                    vendor_id, canonical_field_id, source_type,
                    entity_type, vendor_field_path, channel_id,
                    transformation_rule, priority, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vendor_id,
                canonical_field_id,
                'websocket',  # source_type
                entity_type,
                vendor_field_path,
                channel_id,
                json.dumps(transformation_rule) if transformation_rule else None,
                priority,
                True
            ))
            logger.info(f"Created mapping: {vendor_field_path} -> canonical field {canonical_field_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to create mapping for {vendor_field_path}: {e}")
            return False

    def map_bitmart_ticker_fields(self):
        """
        Map BitMart WebSocket ticker fields to canonical fields.

        Based on BitMart WebSocket ticker format from bitmart_adapter.py:
        {
            "table": "spot/ticker",
            "data": [
                {
                    "symbol": "BTC_USDT",
                    "last_price": "50000.00",
                    "quote_volume_24h": "1000000.00",
                    "base_volume_24h": "20.00",
                    "high_24h": "51000.00",
                    "low_24h": "49000.00",
                    "open_24h": "49500.00",
                    "close_24h": "50000.00",
                    "best_ask": "50001.00",
                    "best_ask_size": "1.5",
                    "best_bid": "49999.00",
                    "best_bid_size": "2.0",
                    "fluctuation": "0.01",
                    "url": "...",
                    "timestamp": 1234567890000
                }
            ]
        }

        Returns:
            Number of mappings created
        """
        logger.info("Starting BitMart ticker field mapping...")

        # Get vendor and channel IDs
        vendor_id = self.get_vendor_id('bitmart')
        if not vendor_id:
            logger.error("BitMart vendor not found")
            return 0

        channel_id = self.get_websocket_channel_id(vendor_id, 'spot/ticker')
        if not channel_id:
            logger.error("BitMart spot/ticker channel not found")
            return 0

        # Define mappings: (vendor_field_path, canonical_field_name, transformation_rule, entity_type)
        # Note: Using data[].field_name for array element mapping
        mappings = [
            # Symbol field
            ('data[].symbol', 'symbol', {'type': 'identity'}, 'ticker'),

            # Price fields (string to numeric conversion)
            ('data[].last_price', 'last_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('data[].best_bid', 'bid_price', {'type': 'string_to_numeric'}, 'ticker'),
            ('data[].best_ask', 'ask_price', {'type': 'string_to_numeric'}, 'ticker'),

            # Size fields (string to numeric conversion)
            ('data[].best_bid_size', 'best_bid_size', {'type': 'string_to_numeric'}, 'ticker'),
            ('data[].best_ask_size', 'best_ask_size', {'type': 'string_to_numeric'}, 'ticker'),

            # High/Low/Open fields (string to numeric conversion)
            ('data[].high_24h', 'high_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('data[].low_24h', 'low_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('data[].open_24h', 'open_24h', {'type': 'string_to_numeric'}, 'ticker'),

            # Volume fields (string to numeric conversion) - using quote volume for volume_24h
            ('data[].quote_volume_24h', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),
            ('data[].base_volume_24h', 'volume_24h', {'type': 'string_to_numeric'}, 'ticker'),  # Alternative mapping

            # Timestamp field (integer to datetime conversion)
            ('data[].timestamp', 'timestamp', {'type': 'integer_to_datetime'}, 'ticker'),

            # Close price can map to last_price as alternative
            ('data[].close_24h', 'last_price', {'type': 'string_to_numeric'}, 'ticker'),  # Alternative mapping
        ]

        created_count = 0
        failed_count = 0

        for vendor_path, canonical_name, transform_rule, entity_type in mappings:
            # Get canonical field ID
            canonical_field_id = self.get_canonical_field_id(canonical_name)
            if not canonical_field_id:
                logger.warning(f"Canonical field not found: {canonical_name}")
                failed_count += 1
                continue

            # Create mapping
            if self.create_field_mapping(
                vendor_id=vendor_id,
                canonical_field_id=canonical_field_id,
                vendor_field_path=vendor_path,
                channel_id=channel_id,
                entity_type=entity_type,
                transformation_rule=transform_rule,
                priority=10  # High priority for direct mappings
            ):
                created_count += 1
            else:
                failed_count += 1

        # Commit all mappings
        self.conn.commit()

        logger.info(f"BitMart ticker mapping complete: {created_count} created, {failed_count} failed")
        return created_count

    def verify_mappings(self) -> Dict[str, int]:
        """
        Verify created mappings by querying the database.

        Returns:
            Dictionary with verification statistics
        """
        cursor = self.conn.cursor()

        # Get vendor and channel IDs
        vendor_id = self.get_vendor_id('bitmart')
        channel_id = self.get_websocket_channel_id(vendor_id, 'spot/ticker')

        # Count total mappings for BitMart ticker
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM field_mappings fm
            JOIN canonical_fields cf ON fm.canonical_field_id = cf.canonical_field_id
            WHERE fm.vendor_id = ? AND fm.channel_id = ?
        """, (vendor_id, channel_id))

        total_mappings = cursor.fetchone()['count']

        # Count by entity type
        cursor.execute("""
            SELECT fm.entity_type, COUNT(*) as count
            FROM field_mappings fm
            WHERE fm.vendor_id = ? AND fm.channel_id = ?
            GROUP BY fm.entity_type
        """, (vendor_id, channel_id))

        by_entity_type = {row['entity_type']: row['count'] for row in cursor.fetchall()}

        # Get coverage statistics
        cursor.execute("""
            SELECT * FROM vendor_coverage_view
            WHERE vendor_name = 'bitmart' AND data_type_name = 'ticker'
        """)

        coverage = cursor.fetchone()

        return {
            'total_mappings': total_mappings,
            'by_entity_type': by_entity_type,
            'coverage': dict(coverage) if coverage else {}
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Map BitMart WebSocket ticker fields to canonical fields",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create BitMart ticker mappings
  python create_bitmart_mappings.py

  # Create mappings and verify results
  python create_bitmart_mappings.py --verify

  # Dry run (show what would be mapped without actually creating)
  python create_bitmart_mappings.py --dry-run
        """
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify mappings after creation'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be mapped without creating actual entries'
    )

    args = parser.parse_args()

    with BitmartTickerMapper() as mapper:
        if args.dry_run:
            print("Dry run mode - would map the following fields:")
            print("=" * 60)

            # Get vendor and channel IDs for display
            vendor_id = mapper.get_vendor_id('bitmart')
            channel_id = mapper.get_websocket_channel_id(vendor_id, 'spot/ticker')

            print(f"Vendor: bitmart (id={vendor_id})")
            print(f"Channel: spot/ticker (id={channel_id})")
            print()

            # Show what would be mapped
            mappings = [
                ('data[].symbol', 'symbol', 'ticker'),
                ('data[].last_price', 'last_price', 'ticker'),
                ('data[].best_bid', 'bid_price', 'ticker'),
                ('data[].best_ask', 'ask_price', 'ticker'),
                ('data[].best_bid_size', 'best_bid_size', 'ticker'),
                ('data[].best_ask_size', 'best_ask_size', 'ticker'),
                ('data[].high_24h', 'high_24h', 'ticker'),
                ('data[].low_24h', 'low_24h', 'ticker'),
                ('data[].open_24h', 'open_24h', 'ticker'),
                ('data[].quote_volume_24h', 'volume_24h', 'ticker'),
                ('data[].base_volume_24h', 'volume_24h', 'ticker'),
                ('data[].close_24h', 'last_price', 'ticker'),
                ('data[].timestamp', 'timestamp', 'ticker'),
            ]

            for vendor_path, canonical_name, entity_type in mappings:
                field_id = mapper.get_canonical_field_id(canonical_name)
                status = "✓" if field_id else "✗ (field not found)"
                print(f"{vendor_path:35} → {canonical_name:20} [{entity_type:10}] {status}")

            print()
            print("Total: 13 potential mappings")

        else:
            # Create mappings
            created = mapper.map_bitmart_ticker_fields()

            if created > 0:
                print(f"\n✓ Created {created} BitMart ticker field mappings")

                if args.verify:
                    print("\nVerification results:")
                    print("=" * 60)

                    stats = mapper.verify_mappings()

                    print(f"Total mappings: {stats['total_mappings']}")

                    if stats['by_entity_type']:
                        print("\nBy entity type:")
                        for entity_type, count in stats['by_entity_type'].items():
                            print(f"  {entity_type}: {count}")

                    if stats.get('coverage'):
                        cov = stats['coverage']
                        print(f"\nCoverage for ticker data type:")
                        print(f"  Fields defined: {cov['fields_defined']}")
                        print(f"  Fields mapped: {cov['fields_mapped']}")
                        print(f"  Coverage: {cov['coverage_percent']}%")

                    print()
            else:
                print("\n✗ No mappings were created")
                sys.exit(1)


if __name__ == '__main__':
    main()
