#!/bin/bash
#
# Rebuild Script - Complete fresh build from scratch
# This script rebuilds the entire catalog system and discovers all exchanges
#

set -e  # Exit on error

echo "=========================================="
echo "Crypto Exchange API Catalog - Full Rebuild"
echo "=========================================="
echo ""

# Clean old data
echo "Step 1: Cleaning old data..."
if [ -d "data" ]; then
    echo "  Removing existing data directory..."
    rm -rf data
fi

if [ -d "output" ]; then
    echo "  Removing existing output directory..."
    rm -rf output
fi

echo "  ✓ Old data cleaned"
echo ""

# Initialize database
echo "Step 2: Initializing database..."
python3 main.py init
echo "  ✓ Database initialized"
echo ""

# Discover all enabled exchanges
echo "Step 3: Discovering exchanges..."
echo ""

echo "  Discovering Coinbase..."
python3 main.py discover --vendor coinbase
echo "  ✓ Coinbase complete"
echo ""

echo "  Discovering Binance..."
if python3 main.py discover --vendor binance; then
    echo "  ✓ Binance complete"
else
    echo "  ⚠ Binance failed (may be geo-restricted)"
fi
echo ""

echo "  Discovering Kraken..."
python3 main.py discover --vendor kraken
echo "  ✓ Kraken complete"
echo ""

echo "  Discovering Bitfinex..."
python3 main.py discover --vendor bitfinex
echo "  ✓ Bitfinex complete"
echo ""

# Export catalogs
echo "Step 4: Exporting JSON catalogs..."
mkdir -p output

echo "  Exporting Coinbase (snake_case)..."
python3 main.py export --vendor coinbase --output output/coinbase_catalog.json
echo "  ✓ output/coinbase_catalog.json"

echo "  Exporting Coinbase (camelCase)..."
python3 main.py export --vendor coinbase --format camelCase --output output/coinbase_catalog_camelCase.json
echo "  ✓ output/coinbase_catalog_camelCase.json"

echo "  Exporting Kraken (snake_case)..."
python3 main.py export --vendor kraken --output output/kraken_catalog.json
echo "  ✓ output/kraken_catalog.json"

echo "  Exporting Bitfinex (snake_case)..."
python3 main.py export --vendor bitfinex --output output/bitfinex_catalog.json
echo "  ✓ output/bitfinex_catalog.json"

if python3 main.py export --vendor binance --output output/binance_catalog.json 2>/dev/null; then
    echo "  ✓ output/binance_catalog.json"
else
    echo "  ⚠ Binance export skipped (no data)"
fi

echo ""

# Summary
echo "=========================================="
echo "Rebuild Complete!"
echo "=========================================="
echo ""
echo "Database: data/specifications.db"
echo "Catalogs: output/"
echo ""
echo "Run 'python3 main.py list-vendors' to see all vendors"
echo "Run 'python3 main.py query' to explore the data"
echo ""
