#!/bin/bash

echo "======================================"
echo "☁️  Cloudflare Permanent Tunnel Setup"
echo "======================================"
echo ""
echo "This will create a permanent tunnel with your Cloudflare account"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    
    # Detect architecture
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    elif [ "$ARCH" = "aarch64" ]; then
        CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
    else
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
    fi
    
    wget -q "$CLOUDFLARED_URL" -O cloudflared
    chmod +x cloudflared
    sudo mv cloudflared /usr/local/bin/
    echo "✅ cloudflared installed"
fi

echo "======================================"
echo "Step 1: Login to Cloudflare"
echo "======================================"
echo "This will open a browser window to login..."
echo ""

cloudflared tunnel login

echo ""
echo "======================================"
echo "Step 2: Create Tunnel"
echo "======================================"
echo ""

# Create tunnel with a name
read -p "Enter a name for your tunnel (e.g., printer-api): " TUNNEL_NAME
TUNNEL_NAME=${TUNNEL_NAME:-printer-api}

echo "Creating tunnel: $TUNNEL_NAME"
cloudflared tunnel create $TUNNEL_NAME

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')

if [ -z "$TUNNEL_ID" ]; then
    echo "❌ Failed to create tunnel"
    exit 1
fi

echo "✅ Tunnel created with ID: $TUNNEL_ID"

echo ""
echo "======================================"
echo "Step 3: Configure Tunnel"
echo "======================================"

# Create config file
cat > ~/.cloudflared/config.yml <<EOF
tunnel: $TUNNEL_ID
credentials-file: /home/$USER/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: $TUNNEL_NAME.yourdomain.com
    service: http://localhost:5000
  - service: http_status:404
EOF

echo "Config file created at ~/.cloudflared/config.yml"
echo ""
echo "======================================"
echo "Step 4: Route DNS (Optional)"
echo "======================================"
echo ""
echo "If you have a domain in Cloudflare, you can route it to this tunnel:"
echo ""
echo "Option A: Use a subdomain (recommended)"
echo "  cloudflared tunnel route dns $TUNNEL_NAME printer-api.yourdomain.com"
echo ""
echo "Option B: Use Cloudflare's domain"
echo "  Your tunnel is accessible at:"
echo "  https://$TUNNEL_ID.cfargotunnel.com"
echo ""
read -p "Do you want to set up DNS routing? (y/n): " SETUP_DNS

if [ "$SETUP_DNS" = "y" ]; then
    read -p "Enter your domain (e.g., yourdomain.com): " DOMAIN
    read -p "Enter subdomain (e.g., printer-api): " SUBDOMAIN
    
    cloudflared tunnel route dns $TUNNEL_NAME $SUBDOMAIN.$DOMAIN
    
    echo "✅ DNS routing configured: https://$SUBDOMAIN.$DOMAIN"
    
    # Update config with actual hostname
    sed -i "s/$TUNNEL_NAME.yourdomain.com/$SUBDOMAIN.$DOMAIN/g" ~/.cloudflared/config.yml
else
    echo "Skipping DNS setup. You can access via:"
    echo "https://$TUNNEL_ID.cfargotunnel.com"
fi

echo ""
echo "======================================"
echo "Step 5: Run Tunnel"
echo "======================================"
echo ""
echo "To run the tunnel:"
echo "  cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo "To run as a service (auto-start on boot):"
echo "  sudo cloudflared service install"
echo "  sudo systemctl start cloudflared"
echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Your tunnel details:"
echo "  Name: $TUNNEL_NAME"
echo "  ID: $TUNNEL_ID"
echo ""
echo "To start the tunnel now, run:"
echo "  cloudflared tunnel run $TUNNEL_NAME"
echo ""