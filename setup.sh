#!/bin/bash

# TiDB Custom MCP Server Setup Script

echo "Setting up TiDB Custom MCP Server..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy and edit the environment file:"
echo "   cp .env.example .env"
echo "   # Edit .env with your TiDB connection details"
echo ""
echo "2. Add the following to your Claude Desktop config:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "tidb-insight": {'
echo '      "command": "'$(pwd)'/venv/bin/python",'
echo '      "args": ["'$(pwd)'/server.py"]'
echo '    }'
echo '  }'
echo '}'