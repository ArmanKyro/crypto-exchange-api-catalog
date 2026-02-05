#!/usr/bin/env python3
"""
Create Zaif WebSocket ticker field mappings to canonical fields.
Maps Zaif-specific field names to industry-standard canonical field names.
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


class ZaifTickerMapper:
    """
    Maps Zaif WebSocket ticker fields to canonical fields.
    """

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Initialize mapper with database path.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None
        self.exchange_name = "zaif"

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
        Get vendor ID for Zaif.

        Returns:
            Vendor ID or None if not found
        """
        self.connect()
        cursor = self.conn.execute(
            "SELECT vendor_id FROM vendors WHERE vendor_name = ?",
            ("zaif",)
        )
        result = cursor.fetchone()
        return result["vendor_id"] if result else None

    def get_websocket_channels(self, vendor_id: int) -> List[Dict]:
        """
        Get WebSocket channels for Zaif.

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
            # This depends on the actual Zaif WebSocket message format
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

    def get_rest_endpoints(self, vendor_id: int) -> List[Dict]:
        """
        Get REST endpoints for Zaif, specifically ticker and last_price endpoints.

        Args:
            vendor_id: Vendor ID

        Returns:
            List of endpoint dictionaries
        """
        cursor = self.conn.execute(
            """
            SELECT endpoint_id, path, method, response_schema
            FROM rest_endpoints
            WHERE vendor_id = ? AND method = 'GET'
              AND (path LIKE '%ticker%' OR path LIKE '%last_price%')
            """,
            (vendor_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def propose_mappings(self, vendor_id: int) -> List[Tuple[str, str, str]]:
        """
        Propose field mappings for Zaif.

        Based on Zaif REST API documentation:
        - /api/1/ticker/{currency_pair} returns fields: last, high, low, vwap, volume, bid, ask
        - /api/1/last_price/{currency_pair} returns fields: last_price
        - All values are floats

        Args:
            vendor_id: Vendor ID

        Returns:
            List of (vendor_field_path, canonical_field_name, transformation_rule) tuples
        """
        # Based on Zaif REST API documentation from zaif_adapter.py and actual API responses
        # Ticker endpoint (/api/1/ticker/{currency_pair}) returns:
        # {"last": 11351940.0, "high": 12050000.0, "low": 11000000.0, "vwap": 11595260.7666,
        #  "volume": 4.7503, "bid": 11307005.0, "ask": 11369995.0}

        # Last price endpoint (/api/1/last_price/{currency_pair}) returns:
        # {"last_price": 11351940.0}

        proposed_mappings = [
            # Ticker endpoint mappings
            ("last", "last_price", '{"type": "identity"}'),
            ("high", "high_24h", '{"type": "identity"}'),
            ("low", "low_24h", '{"type": "identity"}'),
            ("volume", "volume_24h", '{"type": "identity"}'),
            ("bid", "bid_price", '{"type": "identity"}'),
            ("ask", "ask_price", '{"type": "identity"}'),

            # Last price endpoint mapping
            ("last_price", "last_price", '{"type": "identity"}'),
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

        # Get REST endpoints - specifically ticker endpoints
        endpoints = self.get_rest_endpoints(vendor_id)
        if not endpoints:
            logger.warning(f"No REST ticker endpoints found for {self.exchange_name.capitalize()}")
            return

        # Find the main ticker endpoint (/api/1/ticker/{currency_pair})
        ticker_endpoint_id = None
        last_price_endpoint_id = None

        for endpoint in endpoints:
            if '/api/1/ticker/{currency_pair}' in endpoint['path']:
                ticker_endpoint_id = endpoint['endpoint_id']
                logger.info(f"Found ticker endpoint: {endpoint['path']} (id: {ticker_endpoint_id})")
            elif '/api/1/last_price/{currency_pair}' in endpoint['path']:
                last_price_endpoint_id = endpoint['endpoint_id']
                logger.info(f"Found last price endpoint: {endpoint['path']} (id: {last_price_endpoint_id})")

        if not ticker_endpoint_id:
            logger.warning(f"No ticker endpoint found for {self.exchange_name.capitalize()}")
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

                # Determine which endpoint this mapping belongs to
                endpoint_id = None
                if vendor_field == 'last_price':
                    # This field comes from the last_price endpoint
                    endpoint_id = last_price_endpoint_id
                else:
                    # All other fields come from the main ticker endpoint
                    endpoint_id = ticker_endpoint_id

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

                # Insert new mapping for REST endpoint
                self.conn.execute(
                    """
                    INSERT INTO field_mappings
                    (vendor_id, vendor_field_path, canonical_field_id, transformation_rule,
                     source_type, entity_type, endpoint_id)
                    VALUES (?, ?, ?, ?, 'rest', 'ticker', ?)
                    """,
                    (vendor_id, vendor_field, canonical_id, transform, endpoint_id)
                )
                created_count += 1
                logger.debug(f"Created mapping: {vendor_field} -> {canonical_field} (endpoint: {endpoint_id}, transform: {transform})")

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
        description=f"Create Zaif field mappings"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show proposed mappings without saving to database"
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create mappings in database (requires --dry-run false)"
    )

    args = parser.parse_args()

    # If --create is specified, --dry-run must be false
    if args.create:
        args.dry_run = False

    mapper = ZaifTickerMapper()

    try:
        if args.create:
            logger.info(f"Creating Zaif mappings...")
            mapper.create_mappings(dry_run=False)
        else:
            logger.info(f"Proposing Zaif mappings (dry run)...")
            mapper.create_mappings(dry_run=True)
    except Exception as e:
        logger.error(f"Failed to create mappings: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
