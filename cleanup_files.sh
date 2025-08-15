#!/bin/bash

echo "======================================"
echo "🧹 Cleaning Up Old Files"
echo "======================================"
echo ""

# Files to KEEP (new API service and essential files)
KEEP_FILES=(
    "printer_api_service.py"
    "start_api_service.sh"
    "setup_tunnel.sh"
    "setup_permanent_tunnel.sh"
    "test_api_client.py"
    "install_service.sh"
    "uninstall_service.sh"
    "cleanup_files.sh"
    "API_SETUP_GUIDE.md"
    "CLAUDE.md"
    "requirements.txt"
    ".gitignore"
)

# Files to REMOVE (old versions and test scripts)
REMOVE_FILES=(
    "virtual_printer.py"
    "virtual_printer_api.py"
    "virtual_printer_service.py"
    "send_test_receipt.py"
    "test_setup.py"
    "test_parser.py"
    "test_api.py"
    "analyze_receipts.py"
    "reprocess_receipts.py"
    "monitor.sh"
    "monitor.html"
    "run.sh"
    "watch_logs.sh"
    "manage_service.sh"
    "tdd.sh"
    "quick_tunnel.sh"
    "setup_cloudflare.sh"
    "cloudflare_setup.sh"
    "cloudflared-linux-amd64"
    "printer-faker.service"
    "service.log"
    "receipts.db"
    "pytest.ini"
    "README.md"
    "SERVICE_SETUP.md"
    "TEST_GUIDE.md"
    "API_USAGE.md"
)

echo "Step 1: Removing old Python files and scripts..."
echo "------------------------------------------------"

for file in "${REMOVE_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  Removing: $file"
        rm -f "$file"
    fi
done

echo ""
echo "Step 2: Cleaning output folder..."
echo "------------------------------------------------"

# Remove all raw binary files from output folder
if [ -d "output" ]; then
    file_count=$(find output -name "*.bin" | wc -l)
    if [ $file_count -gt 0 ]; then
        echo "  Removing $file_count raw data files..."
        rm -f output/*.bin
    fi
    
    # Remove output folder if empty
    if [ -z "$(ls -A output)" ]; then
        echo "  Removing empty output folder..."
        rmdir output
    fi
fi

echo ""
echo "Step 3: Cleaning old test folders..."
echo "------------------------------------------------"

# Remove tests folder if it exists
if [ -d "tests" ]; then
    echo "  Removing tests folder..."
    rm -rf tests
fi

# Remove static folder if it exists
if [ -d "static" ]; then
    echo "  Removing static folder..."
    rm -rf static
fi

echo ""
echo "Step 4: Keeping essential files..."
echo "------------------------------------------------"
echo "The following files are preserved:"
for file in "${KEEP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    fi
done

echo ""
echo "======================================"
echo "✅ Cleanup Complete!"
echo "======================================"
echo ""
echo "Remaining files:"
ls -la | grep -v "^d" | tail -n +2 | awk '{print "  " $9}'
echo ""
echo "To remove old system service, run:"
echo "  sudo ./uninstall_service.sh"