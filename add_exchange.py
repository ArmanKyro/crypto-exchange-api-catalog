#!/usr/bin/env python3
"""
add_exchange.py - Automation script for adding new cryptocurrency exchanges.

This script automates the boilerplate tasks required to add a new exchange
to the crypto-exchange-api-catalog project.

Usage:
    python add_exchange.py --name bitmart \
        --base-url https://api.bitmart.com \
        --ws-url wss://ws-manager-compress.bitmart.com \
        --docs https://developer-pro.bitmart.com/en/spot \
        --product-endpoint /spot/v1/symbols

Automates:
    1. Create adapter from template (src/adapters/{name}_adapter.py)
    2. Add to config/settings.py vendor configuration
    3. Register in spec_generator.py (import + adapter creation)
    4. Create empty linking method skeleton in spec_generator.py
    5. Generate mapping script template (src/scripts/create_{name}_mappings.py)
    6. Update TODO list status (AI-EXCHANGE-TODO-LIST.txt)
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExchangeAutomation:
    """Main class for automating exchange integration."""

    def __init__(self, exchange_name: str, base_url: str, ws_url: str,
                 docs_url: str, product_endpoint: str, display_name: Optional[str] = None):
        """
        Initialize exchange automation.

        Args:
            exchange_name: Lowercase exchange name (e.g., 'bitmart')
            base_url: REST API base URL
            ws_url: WebSocket URL
            docs_url: API documentation URL
            product_endpoint: Endpoint for fetching products
            display_name: Optional display name (defaults to capitalized exchange_name)
        """
        self.exchange_name = exchange_name.lower()
        self.exchange_class = f"{exchange_name.capitalize()}Adapter"
        self.base_url = base_url.rstrip('/')
        self.ws_url = ws_url
        self.docs_url = docs_url
        self.product_endpoint = product_endpoint
        self.display_name = display_name or f"{exchange_name.capitalize()} Exchange"

        # Project paths
        self.project_root = Path(__file__).parent
        self.template_path = self.project_root / "src" / "adapters" / "template_adapter.py"
        self.adapter_path = self.project_root / "src" / "adapters" / f"{self.exchange_name}_adapter.py"
        self.config_path = self.project_root / "config" / "settings.py"
        self.spec_gen_path = self.project_root / "src" / "discovery" / "spec_generator.py"
        self.mapping_script_path = self.project_root / "src" / "scripts" / f"create_{self.exchange_name}_mappings.py"
        self.todo_path = self.project_root / "AI-EXCHANGE-TODO-LIST.txt"

        # Validate paths exist
        self._validate_paths()

    def _validate_paths(self):
        """Validate that required files exist."""
        required_paths = [
            self.template_path,
            self.config_path,
            self.spec_gen_path,
            self.todo_path
        ]

        for path in required_paths:
            if not path.exists():
                raise FileNotFoundError(f"Required file not found: {path}")

    def run(self, dry_run: bool = False):
        """
        Run the full automation process.

        Args:
            dry_run: If True, only show what would be done without making changes
        """
        logger.info(f"Starting exchange automation for: {self.exchange_name}")
        if dry_run:
            logger.info("DRY RUN MODE - No changes will be made")

        steps = [
            ("Create adapter from template", self.create_adapter),
            ("Add to config/settings.py", self.update_config),
            ("Register in spec_generator.py", self.update_spec_generator),
            ("Create mapping script template", self.create_mapping_script),
            ("Update TODO list", self.update_todo_list),
        ]

        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            try:
                if dry_run:
                    logger.info(f"  [DRY RUN] Would execute: {step_name}")
                else:
                    step_func()
                    logger.info(f"  ✓ Completed: {step_name}")
            except Exception as e:
                logger.error(f"  ✗ Failed: {step_name} - {e}")
                if not dry_run:
                    raise

        logger.info(f"Exchange automation {'(dry run) ' if dry_run else ''}complete for {self.exchange_name}")
        if not dry_run:
            logger.info(f"\nNext steps:")
            logger.info(f"  1. Review and edit: {self.adapter_path}")
            logger.info(f"  2. Implement API-specific logic in adapter")
            logger.info(f"  3. Test: python main.py discover --vendor {self.exchange_name}")
            logger.info(f"  4. Create field mappings: {self.mapping_script_path}")

    def create_adapter(self):
        """Create adapter file from template."""
        if self.adapter_path.exists():
            raise FileExistsError(f"Adapter already exists: {self.adapter_path}")

        # Read template
        template_content = self.template_path.read_text()

        # Replace placeholders
        replacements = {
            "[EXCHANGE_NAME]": self.exchange_name.capitalize(),
            "[BASE_URL]": self.base_url,
            "[WEBSOCKET_URL]": self.ws_url,
            "[DOCUMENTATION_URL]": self.docs_url,
            "TemplateAdapter": self.exchange_class,
            "template_adapter": f"{self.exchange_name}_adapter",
            "# Template adapter for": f"# {self.exchange_name.capitalize()} Exchange API adapter",
            "This is a template": f"{self.exchange_name.capitalize()} Exchange API adapter.",
        }

        adapter_content = template_content
        for old, new in replacements.items():
            adapter_content = adapter_content.replace(old, new)

        # Add specific guidance for this exchange
        guidance = f"""# Implementation Notes for {self.exchange_name.capitalize()}:
# 1. Update discover_rest_endpoints() with actual {self.exchange_name.capitalize()} API endpoints
# 2. Update discover_websocket_channels() with actual {self.exchange_name.capitalize()} channel formats
# 3. Update discover_products() to fetch from: {self.base_url}{self.product_endpoint}
# 4. Test with: python main.py discover --vendor {self.exchange_name}
"""

        # Insert guidance after the docstring
        lines = adapter_content.split('\n')
        for i, line in enumerate(lines):
            if '"""' in line and lines[i-1].strip().endswith('"""'):
                # Found end of class docstring
                lines.insert(i, guidance)
                break

        # Write adapter file
        self.adapter_path.parent.mkdir(parents=True, exist_ok=True)
        self.adapter_path.write_text('\n'.join(lines))

        logger.debug(f"Created adapter: {self.adapter_path}")

    def update_config(self):
        """Add vendor configuration to config/settings.py."""
        config_content = self.config_path.read_text()

        # Check if vendor already exists
        vendor_pattern = rf'"{self.exchange_name}":\s*{{'
        if re.search(vendor_pattern, config_content, re.IGNORECASE):
            raise ValueError(f"Vendor '{self.exchange_name}' already exists in config/settings.py")

        # Find the end of VENDORS dictionary (before the closing brace and DISCOVERY_CONFIG)
        vendors_end = config_content.find('}\n\n# Discovery process configuration')
        if vendors_end == -1:
            vendors_end = config_content.find('}\n\nDISCOVERY_CONFIG = {')

        if vendors_end == -1:
            raise ValueError("Could not find VENDORS dictionary end in config/settings.py")

        # Create vendor configuration
        vendor_config = f'''    "{self.exchange_name}": {{
        "enabled": True,
        "display_name": "{self.display_name}",
        "base_url": "{self.base_url}",
        "websocket_url": "{self.ws_url}",
        "documentation_url": "{self.docs_url}",
        "discovery_methods": ["live_api_probing"],
        "endpoints": {{
            "products": "{self.product_endpoint}",
            "time": "/api/v3/time",  # UPDATE: Replace with actual time endpoint
            "tickers": "/api/v3/ticker/24hr"  # UPDATE: Replace with actual ticker endpoint
        }},
        "rate_limits": {{
            "public": 20  # UPDATE: Set actual rate limit
        }},
        "authentication": {{
            "public_endpoints": True,
            "requires_api_key": False  # Phase 1: public only
        }}
    }},
}}'''

        # Insert before the closing brace
        new_config = config_content[:vendors_end] + vendor_config + config_content[vendors_end + 1:]

        # Write updated config
        self.config_path.write_text(new_config)

        logger.debug(f"Updated config/settings.py with {self.exchange_name} configuration")

    def update_spec_generator(self):
        """Update spec_generator.py with import and adapter registration."""
        spec_content = self.spec_gen_path.read_text()

        # 1. Add import
        import_pattern = r'from src\.adapters\.\w+_adapter import \w+Adapter'
        imports = list(re.finditer(import_pattern, spec_content))

        if not imports:
            raise ValueError("Could not find adapter imports in spec_generator.py")

        # Find the last import line
        last_import = imports[-1]
        import_end = last_import.end()

        # Add new import after the last one
        new_import = f'from src.adapters.{self.exchange_name}_adapter import {self.exchange_class}'

        # Check if import already exists
        if new_import not in spec_content:
            spec_content = spec_content[:import_end] + '\n' + new_import + spec_content[import_end:]

        # 2. Update _create_adapter method
        create_adapter_pattern = r'def _create_adapter\([\s\S]*?elif vendor_name == \'(\w+)\':[\s\S]*?else:'
        create_adapter_match = re.search(create_adapter_pattern, spec_content, re.DOTALL)

        if not create_adapter_match:
            raise ValueError("Could not find _create_adapter method in spec_generator.py")

        # Find the last elif before 'else:'
        adapter_method = create_adapter_match.group(0)

        # Check if this exchange is already in the method
        if f"vendor_name == '{self.exchange_name}'" in adapter_method:
            logger.warning(f"Adapter for {self.exchange_name} already registered in _create_adapter")
            return

        # Insert new elif before 'else:'
        new_elif = f'''        elif vendor_name == '{self.exchange_name}':
            return {self.exchange_class}(vendor_config)'''

        # Find the 'else:' line
        else_pos = adapter_method.rfind('else:')
        updated_method = adapter_method[:else_pos] + new_elif + '\n        ' + adapter_method[else_pos:]

        # Replace the method in the full content
        spec_content = spec_content.replace(adapter_method, updated_method)

        # 3. Update _link_product_feeds method to include new exchange
        link_feeds_pattern = r'def _link_product_feeds\([\s\S]*?elif vendor_name == \'(\w+)\':[\s\S]*?adapter[\s\S]*?\)'
        link_feeds_match = re.search(link_feeds_pattern, spec_content, re.DOTALL)

        if link_feeds_match:
            link_feeds_method = link_feeds_match.group(0)

            # Check if this exchange is already in the method
            if f"vendor_name == '{self.exchange_name}'" in link_feeds_method:
                logger.warning(f"Link method for {self.exchange_name} already exists in _link_product_feeds")
            else:
                # Add new elif before the method ends
                new_link_elif = f'''        elif vendor_name == '{self.exchange_name}':
            self._link_{self.exchange_name}_feeds(
                product_ids,
                endpoint_ids,
                channel_ids,
                adapter
            )'''

                # Find the end of the method (look for the next dedented line)
                lines = link_feeds_method.split('\n')
                for i, line in enumerate(lines):
                    if i > 10 and line.strip() and not line.startswith(' ' * 8):
                        # Found end of method
                        lines.insert(i, new_link_elif)
                        updated_link_method = '\n'.join(lines)
                        spec_content = spec_content.replace(link_feeds_method, updated_link_method)
                        break

        # 4. Add empty linking method stub at the end of the file (before the last line)
        linking_method_stub = f'''
    def _link_{self.exchange_name}_feeds(
        self,
        product_ids: Dict[str, int],
        endpoint_ids: Dict[str, int],
        channel_ids: Dict[str, int],
        adapter: BaseVendorAdapter
    ):
        """
        Link {self.exchange_name.capitalize()} products to their available endpoints and channels.

        Args:
            product_ids: Dictionary of symbol -> product_id
            endpoint_ids: Dictionary of endpoint key -> endpoint_id
            channel_ids: Dictionary of channel_name -> channel_id
            adapter: {self.exchange_class} instance
        """
        logger.info(f"Linking {{len(product_ids)}} {self.exchange_name.capitalize()} products to feeds")

        # TODO: Implement {self.exchange_name.capitalize()}-specific linking logic
        # Example pattern (update based on actual API):
        # for symbol, product_id in product_ids.items():
        #     # REST endpoints
        #     ticker_key = "GET /api/v3/ticker/24hr"
        #     if ticker_key in endpoint_ids:
        #         self.repository.link_product_to_endpoint(
        #             product_id,
        #             endpoint_ids[ticker_key],
        #             'ticker'
        #         )
        #
        #     # WebSocket channels
        #     for channel_name, channel_id in channel_ids.items():
        #         self.repository.link_product_to_ws_channel(
        #             product_id,
        #             channel_id
        #         )
        pass
'''

        # Insert before the last line (which should be the end of the class)
        if f"def _link_{self.exchange_name}_feeds" not in spec_content:
            # Find the last method in the class
            class_end = spec_content.rfind('\n\n')
            spec_content = spec_content[:class_end] + linking_method_stub + spec_content[class_end:]

        # Write updated spec_generator.py
        self.spec_gen_path.write_text(spec_content)

        logger.debug(f"Updated spec_generator.py with {self.exchange_name} support")

    def create_mapping_script(self):
        """Create mapping script template."""
        if self.mapping_script_path.exists():
            logger.warning(f"Mapping script already exists: {self.mapping_script_path}")
            return

        # Template for mapping script
        mapping_template = f'''#!/usr/bin/env python3
"""
Create {self.exchange_name.capitalize()} WebSocket ticker field mappings to canonical fields.
Maps {self.exchange_name.capitalize()}-specific field names to industry-standard canonical field names.
"""

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


class {self.exchange_name.capitalize()}TickerMapper:
    """
    Maps {self.exchange_name.capitalize()} WebSocket ticker fields to canonical fields.
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
            logger.info(f"Connected to database: {{self.db_path}}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("Database connection closed")

    def get_vendor_id(self) -> Optional[int]:
        """
        Get vendor ID for {self.exchange_name.capitalize()}.

        Returns:
            Vendor ID or None if not found
        """
        self.connect()
        cursor = self.conn.execute(
            "SELECT vendor_id FROM vendors WHERE vendor_name = ?",
            ("{self.exchange_name}",)
        )
        result = cursor.fetchone()
        return result["vendor_id"] if result else None

    def get_websocket_channels(self, vendor_id: int) -> List[Dict]:
        """
        Get WebSocket channels for {self.exchange_name.capitalize()}.

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
            # This depends on the actual {self.exchange_name.capitalize()} WebSocket message format
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message schema: {{e}}")
            return []

    def propose_mappings(self, vendor_id: int) -> List[Tuple[str, str, str]]:
        """
        Propose field mappings for {self.exchange_name.capitalize()}.

        Args:
            vendor_id: Vendor ID

        Returns:
            List of (vendor_field_path, canonical_field_id, transformation) tuples
        """
        # TODO: Implement based on actual {self.exchange_name.capitalize()} WebSocket API
        # Example mappings (update with actual fields):
        proposed_mappings = [
            # ("last", "last_price", "float"),
            # ("bid", "best_bid_price", "float"),
            # ("ask", "best_ask_price", "float"),
            # ("volume", "volume_24h", "float"),
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
            logger.error(f"Vendor '{{self.exchange_name}}' not found in database")
            return

        logger.info(f"Creating mappings for {{self.exchange_name.capitalize()}} (vendor_id: {{vendor_id}})")

        # Get WebSocket channels
        channels = self.get_websocket_channels(vendor_id)
        if not channels:
            logger.warning(f"No WebSocket channels found for {{self.exchange_name.capitalize()}}")
            return

        # Propose mappings
        proposed_mappings = self.propose_mappings(vendor_id)

        if dry_run:
            logger.info("DRY RUN - Proposed mappings (not saved):")
            for vendor_field, canonical_field, transform in proposed_mappings:
                logger.info(f"  {{vendor_field}} -> {{canonical_field}} ({{transform}})")
            return

        # Create actual mappings
        created_count = 0
        for vendor_field, canonical_field, transform in proposed_mappings:
            try:
                # TODO: Insert into field_mappings table
                # This requires the canonical_fields table to be populated first
                logger.info(f"Would create mapping: {{vendor_field}} -> {{canonical_field}}")
                created_count += 1
            except Exception as e:
                logger.error(f"Failed to create mapping {{vendor_field}} -> {{canonical_field}}: {{e}}")

        logger.info(f"Created {{created_count}} mappings for {{self.exchange_name.capitalize()}}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description=f"Create {self.exchange_name.capitalize()} field mappings"
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

    mapper = {self.exchange_name.capitalize()}TickerMapper()

    try:
        if args.create:
            logger.info(f"Creating {self.exchange_name.capitalize()} mappings...")
            mapper.create_mappings(dry_run=False)
        else:
            logger.info(f"Proposing {self.exchange_name.capitalize()} mappings (dry run)...")
            mapper.create_mappings(dry_run=True)
    except Exception as e:
        logger.error(f"Failed to create mappings: {{e}}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

        # Write mapping script
        self.mapping_script_path.parent.mkdir(parents=True, exist_ok=True)
        self.mapping_script_path.write_text(mapping_template)

        # Make it executable
        self.mapping_script_path.chmod(0o755)

        logger.debug(f"Created mapping script: {self.mapping_script_path}")

    def update_todo_list(self):
        """Update AI-EXCHANGE-TODO-LIST.txt with new exchange status."""
        todo_content = self.todo_path.read_text()

        # Check if exchange is already in the list
        if f"[ ] {self.exchange_name.capitalize()}" in todo_content or f"[→] {self.exchange_name.capitalize()}" in todo_content:
            logger.warning(f"{self.exchange_name.capitalize()} already in TODO list")
            return

        # Find the "High-Priority Exchanges to Add" section
        lines = todo_content.split('\n')

        for i, line in enumerate(lines):
            if "High-Priority Exchanges to Add" in line:
                # Look for the list items after this section
                for j in range(i + 1, min(i + 20, len(lines))):
                    if lines[j].strip().startswith("- [→]") or lines[j].strip().startswith("- [ ]"):
                        # Found the start of the list
                        # Insert new exchange at the beginning
                        new_line = f"- [→] {self.exchange_name.capitalize()} (in progress)"
                        lines.insert(j, new_line)
                        break
                else:
                    # If no list items found, add after the header
                    new_line = f"- [→] {self.exchange_name.capitalize()} (in progress)"
                    lines.insert(i + 2, new_line)
                break

        # Also update the count in the overview if found
        for i, line in enumerate(lines):
            if "Currently Integrated" in line and "(" in line and "/" in line:
                # Update count, e.g., "Currently Integrated (11/25)" -> "Currently Integrated (12/25)"
                count_match = re.search(r'\((\d+)/(\d+)\)', line)
                if count_match:
                    current = int(count_match.group(1))
                    total = int(count_match.group(2))
                    new_line = line.replace(f"({current}/{total})", f"({current + 1}/{total})")
                    lines[i] = new_line
                break

        # Write updated TODO list
        self.todo_path.write_text('\n'.join(lines))

        logger.debug(f"Updated TODO list with {self.exchange_name.capitalize()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automate adding new cryptocurrency exchange to the API catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add BitMart exchange
  python add_exchange.py --name bitmart \\
    --base-url https://api.bitmart.com \\
    --ws-url wss://ws-manager-compress.bitmart.com \\
    --docs https://developer-pro.bitmart.com/en/spot \\
    --product-endpoint /spot/v1/symbols

  # Add Crypto.com exchange
  python add_exchange.py --name crypto_com \\
    --base-url https://api.crypto.com/exchange/v1 \\
    --ws-url wss://stream.crypto.com/exchange/v1/market \\
    --docs https://exchange-docs.crypto.com/ \\
    --product-endpoint /public/get-instruments \\
    --display-name "Crypto.com Exchange"

  # Dry run (show what would be done)
  python add_exchange.py --name test --base-url http://test.com --ws-url ws://test.com \\
    --docs http://docs.test.com --product-endpoint /api/products --dry-run
"""
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Exchange name (lowercase, e.g., 'bitmart', 'crypto_com')"
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="REST API base URL (e.g., 'https://api.bitmart.com')"
    )
    parser.add_argument(
        "--ws-url",
        required=True,
        help="WebSocket URL (e.g., 'wss://ws-manager-compress.bitmart.com')"
    )
    parser.add_argument(
        "--docs",
        required=True,
        help="API documentation URL"
    )
    parser.add_argument(
        "--product-endpoint",
        required=True,
        help="Endpoint for fetching products (e.g., '/spot/v1/symbols')"
    )
    parser.add_argument(
        "--display-name",
        help="Display name for the exchange (defaults to capitalized name)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files if they exist"
    )

    args = parser.parse_args()

    try:
        # Create automation instance
        automation = ExchangeAutomation(
            exchange_name=args.name,
            base_url=args.base_url,
            ws_url=args.ws_url,
            docs_url=args.docs,
            product_endpoint=args.product_endpoint,
            display_name=args.display_name
        )

        # Run automation
        automation.run(dry_run=args.dry_run)

        if not args.dry_run:
            print(f"\n✅ Exchange automation complete for {args.name}")
            print(f"\nNext steps:")
            print(f"  1. Review and implement API logic in: src/adapters/{args.name}_adapter.py")
            print(f"  2. Test discovery: python main.py discover --vendor {args.name}")
            print(f"  3. Create field mappings: python src/scripts/create_{args.name}_mappings.py --dry-run")
            print(f"  4. Update TODO list status when complete")

    except Exception as e:
        logger.error(f"Exchange automation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
