#!/usr/bin/env python3
"""
Script to query database for exchange coverage statistics.

This script connects to the SQLite database at data/specifications.db
and generates comprehensive statistics about exchange integration,
field mapping coverage, and database contents.

Usage:
    python update_status.py [--update-md] [--output-file FILE]

Options:
    --update-md     Update IMPLEMENTATION-STATUS.md with current statistics
    --output-file   Write statistics to specified file (JSON format)
    --help          Show this help message
"""

import sqlite3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

class ExchangeStatsCollector:
    """Collects and analyzes exchange coverage statistics from the database."""

    def __init__(self, db_path: str = "data/specifications.db"):
        """Initialize the collector with database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self) -> bool:
        """Connect to the SQLite database."""
        try:
            if not Path(self.db_path).exists():
                print(f"Error: Database file not found: {self.db_path}")
                return False

            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def get_total_exchanges(self) -> int:
        """Get total number of exchanges in the database."""
        self.cursor.execute("SELECT COUNT(*) FROM vendors;")
        return self.cursor.fetchone()[0]

    def get_exchange_products(self) -> List[Tuple[str, int]]:
        """Get product count for each exchange."""
        query = """
        SELECT v.vendor_name, COUNT(p.product_id) as product_count
        FROM vendors v
        LEFT JOIN products p ON v.vendor_id = p.vendor_id
        GROUP BY v.vendor_name
        ORDER BY product_count DESC;
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_exchange_mappings(self) -> List[Tuple[str, int]]:
        """Get field mapping count for each exchange."""
        query = """
        SELECT v.vendor_name, COUNT(fm.mapping_id) as mapping_count
        FROM vendors v
        LEFT JOIN field_mappings fm ON v.vendor_id = fm.vendor_id
        GROUP BY v.vendor_name
        ORDER BY mapping_count DESC;
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_total_canonical_ticker_fields(self) -> int:
        """Get total number of canonical fields for ticker data type."""
        query = """
        SELECT COUNT(*)
        FROM canonical_fields cf
        JOIN data_type_fields dtf ON cf.canonical_field_id = dtf.canonical_field_id
        JOIN canonical_data_types cdt ON dtf.data_type_id = cdt.data_type_id
        WHERE cdt.data_type_name = 'ticker';
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def get_exchange_ticker_coverage(self) -> List[Tuple[str, int, float]]:
        """Get ticker field coverage for each exchange."""
        total_ticker_fields = self.get_total_canonical_ticker_fields()
        if total_ticker_fields == 0:
            return []

        query = """
        SELECT v.vendor_name, COUNT(fm.mapping_id) as ticker_mappings
        FROM vendors v
        LEFT JOIN field_mappings fm ON v.vendor_id = fm.vendor_id AND fm.entity_type = 'ticker'
        GROUP BY v.vendor_name
        ORDER BY ticker_mappings DESC;
        """
        self.cursor.execute(query)

        results = []
        for vendor_name, ticker_mappings in self.cursor.fetchall():
            coverage_percent = (ticker_mappings / total_ticker_fields * 100) if total_ticker_fields > 0 else 0
            results.append((vendor_name, ticker_mappings, round(coverage_percent, 1)))

        return results

    def get_total_products(self) -> int:
        """Get total number of products across all exchanges."""
        self.cursor.execute("SELECT COUNT(*) FROM products;")
        return self.cursor.fetchone()[0]

    def get_total_field_mappings(self) -> int:
        """Get total number of field mappings across all exchanges."""
        self.cursor.execute("SELECT COUNT(*) FROM field_mappings;")
        return self.cursor.fetchone()[0]

    def get_coverage_leaders(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get exchanges with highest ticker coverage."""
        coverage_data = self.get_exchange_ticker_coverage()
        # Sort by coverage percentage (index 2), descending
        coverage_data.sort(key=lambda x: x[2], reverse=True)
        return [(vendor, coverage) for vendor, _, coverage in coverage_data[:limit]]

    def get_average_ticker_coverage(self) -> float:
        """Calculate average ticker coverage across all exchanges."""
        coverage_data = self.get_exchange_ticker_coverage()
        if not coverage_data:
            return 0.0

        total_coverage = sum(coverage for _, _, coverage in coverage_data)
        return round(total_coverage / len(coverage_data), 1)

    def get_database_stats(self) -> Dict[str, Any]:
        """Collect all statistics into a dictionary."""
        if not self.connect():
            return {}

        try:
            stats = {
                "total_exchanges": self.get_total_exchanges(),
                "total_products": self.get_total_products(),
                "total_field_mappings": self.get_total_field_mappings(),
                "total_canonical_ticker_fields": self.get_total_canonical_ticker_fields(),
                "average_ticker_coverage": self.get_average_ticker_coverage(),
                "exchange_products": dict(self.get_exchange_products()),
                "exchange_mappings": dict(self.get_exchange_mappings()),
                "exchange_ticker_coverage": {
                    vendor: {
                        "mappings": mappings,
                        "coverage_percent": coverage
                    }
                    for vendor, mappings, coverage in self.get_exchange_ticker_coverage()
                },
                "coverage_leaders": dict(self.get_coverage_leaders()),
            }
            return stats
        finally:
            self.disconnect()

    def print_statistics(self):
        """Print statistics in a human-readable format."""
        stats = self.get_database_stats()
        if not stats:
            print("No statistics available.")
            return

        print("\n" + "="*60)
        print("CRYPTO EXCHANGE API CATALOG - DATABASE STATISTICS")
        print("="*60)

        print(f"\n📊 OVERVIEW:")
        print(f"  • Total exchanges: {stats['total_exchanges']}")
        print(f"  • Total products: {stats['total_products']:,}")
        print(f"  • Total field mappings: {stats['total_field_mappings']}")
        print(f"  • Average ticker coverage: {stats['average_ticker_coverage']}%")
        print(f"  • Canonical ticker fields: {stats['total_canonical_ticker_fields']}")

        print(f"\n🏆 COVERAGE LEADERS:")
        for i, (exchange, coverage) in enumerate(stats['coverage_leaders'].items(), 1):
            print(f"  {i}. {exchange}: {coverage}% coverage")

        print(f"\n📈 EXCHANGE PRODUCT COUNTS (Top 10):")
        sorted_products = sorted(stats['exchange_products'].items(), key=lambda x: x[1], reverse=True)
        for exchange, count in sorted_products[:10]:
            print(f"  • {exchange}: {count:,} products")

        if len(sorted_products) > 10:
            print(f"  ... and {len(sorted_products) - 10} more exchanges")

        print(f"\n🔄 EXCHANGE MAPPING COUNTS (Top 10):")
        sorted_mappings = sorted(stats['exchange_mappings'].items(), key=lambda x: x[1], reverse=True)
        for exchange, count in sorted_mappings[:10]:
            coverage_info = stats['exchange_ticker_coverage'].get(exchange, {})
            coverage = coverage_info.get('coverage_percent', 0) if coverage_info else 0
            print(f"  • {exchange}: {count} mappings ({coverage}% ticker coverage)")

        print(f"\n📋 DETAILED TICKER COVERAGE:")
        print("  Exchange                | Mappings | Coverage")
        print("  " + "-"*45)
        coverage_items = [
            (exchange, data['mappings'], data['coverage_percent'])
            for exchange, data in stats['exchange_ticker_coverage'].items()
        ]
        coverage_items.sort(key=lambda x: x[2], reverse=True)

        for exchange, mappings, coverage in coverage_items:
            exchange_display = exchange.ljust(20)
            mappings_display = str(mappings).rjust(8)
            coverage_display = f"{coverage}%".rjust(9)
            print(f"  {exchange_display} | {mappings_display} | {coverage_display}")

        print("\n" + "="*60)
        print(f"Statistics generated from: {self.db_path}")
        print("="*60)

    def update_implementation_status(self, md_file: str = "IMPLEMENTATION-STATUS.md") -> bool:
        """
        Update the IMPLEMENTATION-STATUS.md file with current statistics.

        This updates the coverage statistics table in the markdown file.
        """
        stats = self.get_database_stats()
        if not stats:
            return False

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.readlines()

            # Find the coverage table section
            start_line = -1
            end_line = -1
            in_table = False

            for i, line in enumerate(content):
                if "| Exchange | Ticker Coverage |" in line:
                    start_line = i
                    in_table = True
                elif in_table and line.strip() and not line.strip().startswith("|"):
                    # Found end of table (line that's not part of markdown table)
                    end_line = i
                    break

            if start_line == -1:
                print(f"Warning: Could not find coverage table in {md_file}")
                return False

            # Build new table rows
            new_table_lines = []
            new_table_lines.append("| Exchange | Ticker Coverage | Mappings | Entity Types |\n")
            new_table_lines.append("|----------|----------------|----------|--------------|\n")

            # Get all exchanges with their coverage data
            coverage_items = []
            for exchange, data in stats['exchange_ticker_coverage'].items():
                mappings = data['mappings']
                coverage = data['coverage_percent']
                coverage_items.append((exchange, coverage, mappings))

            # Add exchanges that might not have coverage data yet
            for exchange in stats['exchange_products']:
                if exchange not in stats['exchange_ticker_coverage']:
                    coverage_items.append((exchange, 0.0, 0))

            # Sort by coverage descending
            coverage_items.sort(key=lambda x: x[1], reverse=True)

            # Create table rows
            for exchange, coverage, mappings in coverage_items:
                # Determine entity types (simplified - could be enhanced)
                entity_types = "ticker"
                if mappings > 10:  # Arbitrary threshold
                    entity_types = "ticker, trade"

                coverage_display = f"{coverage:.1f}% ({int(mappings)}/{stats['total_canonical_ticker_fields']})"
                new_table_lines.append(f"| {exchange} | {coverage_display} | {mappings} | {entity_types} |\n")

            # Calculate total mappings
            total_mappings = stats['total_field_mappings']
            new_table_lines.append(f"\n**Total Mappings**: {total_mappings} field mappings across all {stats['total_exchanges']} exchanges\n")

            # Replace the old table section
            if end_line == -1:
                end_line = len(content)

            new_content = content[:start_line] + new_table_lines + content[end_line:]

            # Write back to file
            with open(md_file, 'w', encoding='utf-8') as f:
                f.writelines(new_content)

            print(f"✓ Updated {md_file} with current statistics")
            return True

        except Exception as e:
            print(f"Error updating {md_file}: {e}")
            return False

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Query database for exchange coverage statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--update-md",
        action="store_true",
        help="Update IMPLEMENTATION-STATUS.md with current statistics"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Write statistics to specified file (JSON format)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/specifications.db",
        help="Path to SQLite database file (default: data/specifications.db)"
    )

    args = parser.parse_args()

    # Initialize collector
    collector = ExchangeStatsCollector(args.db_path)

    # Check if database exists
    if not Path(args.db_path).exists():
        print(f"Error: Database file not found: {args.db_path}")
        print("Please ensure the database exists or specify a different path with --db-path")
        return 1

    # Print statistics
    collector.print_statistics()

    # Update markdown file if requested
    if args.update_md:
        if not collector.update_implementation_status():
            print("Warning: Failed to update IMPLEMENTATION-STATUS.md")

    # Write to output file if requested
    if args.output_file:
        stats = collector.get_database_stats()
        if stats:
            try:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=2)
                print(f"\n✓ Statistics written to {args.output_file}")
            except Exception as e:
                print(f"Error writing to {args.output_file}: {e}")

    return 0

if __name__ == "__main__":
    exit(main())
