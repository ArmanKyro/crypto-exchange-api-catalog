#!/usr/bin/env python3
"""
Create Korbit WebSocket ticker field mappings to canonical fields.
Maps Korbit-specific field names to industry-standard canonical field names.

Based on Korbit WebSocket API documentation:
- Message format includes: last, bid, ask, open, high, low, volume, timestamp, currency_pair
- Field values are strings that need conversion to numeric/datetime
- Currency pair format: "btc_krw" (lowercase with underscore) needs transformation to "BTC-KRW"
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


class KorbitTickerMapper:
    """
    Maps Korbit WebSocket ticker fields to canonical fields.
    """

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize mapper with database path.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None
        self.exchange_name = "korbit"

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
            logger.debug("Database connection closed")

    def get_vendor_id(self) -> Optional[int]:
        """
        Get vendor ID for Korbit.

        Returns:
            Vendor ID or None if not found
        """
        self.connect()
        cursor = self.conn.execute(
            "SELECT vendor_id FROM vendors WHERE vendor_name = ?",
            ("korbit",)
        )
        result = cursor.fetchone()
        return result["vendor_id"] if result else None

    def get_websocket_channels(self, vendor_id: int) -> List[Dict]:
        """
        Get WebSocket channels for Korbit.

        Args:
            vendor_id: Vendor ID

        Returns:
            List of channel dictionaries
        """
        cursor = self.conn.execute(
            """
            SELECT channel_id, channel_name, message_schema
            FROM websocket_channels
            WHERE vendor_id = ? AND channel_name LIKE '%ticker%'
            """,
            (vendor_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def extract_fields_from_schema(self, message_schema: str) -> List[str]:
        """
        Extract field names from message schema JSON.

        Args:
            message_schema: JSON string of message schema

        Returns:
            List of field paths
        """
        try:
            schema = json.loads(message_schema)
            # TODO: Implement schema traversal to extract field paths
            # This depends on the actual Korbit WebSocket message format
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message schema: {e}")
            return []

    def get_canonical_field_id(self, field_name: str) -> Optional[int]:
        """
        Get canonical field ID by field name.

        Args:
            field_name: Canonical field name

        Returns:
            Canonical field ID or None if not found
        """
        cursor = self.conn.execute(
            "SELECT canonical_field_id FROM canonical_fields WHERE field_name = ?",
            (field_name,)
        )
        result = cursor.fetchone()
        return result["canonical_field_id"] if result else None

    def propose_mappings(self, vendor_id: int) -> List[Tuple[str, str, str]]:
        """
        Propose field mappings for Korbit.

        Args:
            vendor_id: Vendor ID

        Returns:
            List of (vendor_field_path, canonical_field_name, transformation_rule) tuples
        """
        # Based on Korbit WebSocket ticker API documentation from korbit_adapter.py
        # Message schema includes: last, bid, ask, open, high, low, volume, timestamp, currency_pair
        # Field values are strings that need conversion to numeric/datetime
        proposed_mappings = [
            # Price fields (string to numeric)
            ("last", "last_price", '{"type": "string_to_numeric"}'),
            ("bid", "bid_price", '{"type": "string_to_numeric"}'),
            ("ask", "ask_price", '{"type": "string_to_numeric"}'),
            ("open", "open_24h", '{"type": "string_to_numeric"}'),
            ("high", "high_24h", '{"type": "string_to_numeric"}'),
            ("low", "low_24h", '{"type": "string_to_numeric"}'),

            # Volume field (string to numeric)
            ("volume", "volume_24h", '{"type": "string_to_numeric"}'),

            # Timestamp field (milliseconds to datetime)
            ("timestamp", "timestamp", '{"type": "ms_to_datetime"}'),

            # Symbol/currency pair field
            # Note: Korbit uses "btc_krw" format, normalization engine should handle conversion
            ("currency_pair", "symbol", '{"type": "identity"}'),

            # Additional fields that might be available (commented out as placeholders)
            # ("trade_id", "trade_id", '{"type": "identity"}'),
            # ("side", "side", '{"type": "identity"}'),
            # ("size", "size", '{"type": "string_to_numeric"}'),
        ]
        return proposed_mappings

    def create_mappings(self, dry_run: bool = True):
        """
        Create field mappings in database.

        Args:
            dry_run: If True, only show proposed mappings without saving
        """
        vendor_id = self.get_vendor_id()
        if not vendor_id:
            logger.error(f"Vendor '{self.exchange_name}' not found in database")
            return

        logger.info(f"Creating mappings for {self.exchange_name.capitalize()} (vendor_id: {vendor_id})")

        # Get WebSocket channels - specifically ticker channel
        channels = self.get_websocket_channels(vendor_id)
        if not channels:
            logger.warning(f"No WebSocket channels found for {self.exchange_name.capitalize()}")
            return

        # Get ticker channel ID (assume first ticker channel)
        ticker_channel_id = None
        for channel in channels:
            if 'ticker' in channel['channel_name'].lower():
                ticker_channel_id = channel['channel_id']
                break

        if not ticker_channel_id:
            logger.warning(f"No ticker channel found for {self.exchange_name.capitalize()}")
            return

        # Propose mappings
        proposed_mappings = self.propose_mappings(vendor_id)

        if dry_run:
            logger.info("DRY RUN - Proposed mappings (not saved):")
            for vendor_field, canonical_field, transform in proposed_mappings:
                canonical_id = self.get_canonical_field_id(canonical_field)
                if canonical_id:
                    logger.info(f"  {vendor_field} -> {canonical_field} (id: {canonical_id}, transform: {transform})")
                else:
                    logger.warning(f"  {vendor_field} -> {canonical_field} (CANONICAL FIELD NOT FOUND, transform: {transform})")
            return

        # Create actual mappings
        created_count = 0
        for vendor_field, canonical_field, transform in proposed_mappings:
            try:
                canonical_id = self.get_canonical_field_id(canonical_field)
                if not canonical_id:
                    logger.warning(f"Canonical field '{canonical_field}' not found, skipping mapping for {vendor_field}")
                    continue

                # Check if mapping already exists
                cursor = self.conn.execute(
                    """
                    SELECT mapping_id FROM field_mappings
                    WHERE vendor_id = ? AND vendor_field_path = ? AND canonical_field_id = ?
                    """,
                    (vendor_id, vendor_field, canonical_id)
                )
                if cursor.fetchone():
                    logger.debug(f"Mapping already exists: {vendor_field} -> {canonical_field}")
                    continue

                # Insert new mapping
                self.conn.execute(
                    """
                    INSERT INTO field_mappings
                    (vendor_id, vendor_field_path, canonical_field_id, transformation_rule, source_type, entity_type, channel_id)
                    VALUES (?, ?, ?, ?, 'websocket', 'ticker', ?)
                    """,
                    (vendor_id, vendor_field, canonical_id, transform, ticker_channel_id)
                )
                created_count += 1
                logger.debug(f"Created mapping: {vendor_field} -> {canonical_field} (transform: {transform})")

            except Exception as e:
                logger.error(f"Failed to create mapping {vendor_field} -> {canonical_field}: {e}")

        self.conn.commit()
        logger.info(f"Created {created_count} mappings for {self.exchange_name.capitalize()}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description=f"Create Korbit field mappings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Show proposed mappings without saving to database (default: True)"
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create mappings in database (sets --dry-run to False)"
    )

    args = parser.parse_args()

    # If --create is specified, --dry-run must be false
    if args.create:
        args.dry_run = False

    mapper = KorbitTickerMapper()

    try:
        if args.create:
            logger.info(f"Creating Korbit mappings...")
            mapper.create_mappings(dry_run=False)
        else:
            logger.info(f"Proposing Korbit mappings (dry run)...")
            mapper.create_mappings(dry_run=True)
    except Exception as e:
        logger.error(f"Failed to create mappings: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
