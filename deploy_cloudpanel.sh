#!/bin/bash

# CloudPanel Deployment Script for dev.inventory.iniserve.com
# Run this script on your CloudPanel server

echo "🚀 Starting deployment for dev.inventory.iniserve.com..."

# Set variables
DOMAIN="dev.inventory.iniserve.com"
USER="iniserve-dev-inventory"
ROOT_DIR="/home/${USER}/htdocs/${DOMAIN}"
PYTHON_PATH="/usr/bin/python3.11"  # Adjust if needed
PIP_PATH="/usr/bin/pip3.11"        # Adjust if needed

# Navigate to project directory
cd ${ROOT_DIR}

echo "📁 Current directory: $(pwd)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating .env file from example..."
    cp .env.example .env
    echo "⚠️ Please edit .env file with your actual configuration values!"
fi

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Set correct permissions
echo "🔐 Setting correct file permissions..."
chown -R ${USER}:${USER} ${ROOT_DIR}
chmod -R 755 ${ROOT_DIR}
chmod 664 db.sqlite3 2>/dev/null || true

# Create logs directory
mkdir -p logs
chmod 755 logs

echo "✅ Deployment completed successfully!"
echo "🌐 Your site should be available at: https://${DOMAIN}"
echo "🔧 Admin panel: https://${DOMAIN}/admin/"
echo "📊 API documentation: https://${DOMAIN}/api/schema/swagger/"

echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your production values"
echo "2. Create a superuser: python manage.py createsuperuser"
echo "3. Configure SSL certificate in CloudPanel"
echo "4. Test your application"