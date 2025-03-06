#!/bin/bash

# Installation script for Lezo LGU System on Ubuntu 24.04 LTS
# Optimized for single command execution and error handling

set -e  # Exit on any error

echo "Starting installation of Lezo LGU System..."

# Update package list and install dependencies
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib gunicorn

# Set up PostgreSQL database
echo "Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE lezo_db;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER lezo_user WITH PASSWORD 'Lezo2025';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lezo_db TO lezo_user;" 2>/dev/null || true

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Generate a secret key
echo "Generating secret key..."
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Create .env file
echo "Creating .env file..."
cat > .env << EOL
DB_NAME=lezo_db
DB_USER=lezo_user
DB_PASSWORD=Lezo2025
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=$SECRET_KEY
DEBUG=True
EOL

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Run tests
echo "Running tests..."
python manage.py test

# Create startup script
echo "Creating start.sh..."
cat > start.sh << EOL
#!/bin/bash
source venv/bin/activate
gunicorn -b 0.0.0.0:8000 --workers 1 lezo_lgu.wsgi  # Single worker for 1GB RAM
EOL
chmod +x start.sh

# Create desktop launcher
echo "Creating desktop launcher..."
cat > lezo-system.desktop << EOL
[Desktop Entry]
Name=Lezo LGU System
Exec=/bin/bash -c 'cd $(pwd) && ./start.sh'
Type=Application
Terminal=true
EOL

echo "Installation completed successfully!"
echo "To start the application, run './start.sh' or double-click 'lezo-system.desktop'."