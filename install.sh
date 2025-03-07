#!/bin/bash

# Installation script for Lezo LGU System on Ubuntu 24.04 LTS
# Updated for all features with proper permissions and dependencies

set -e

echo "Starting installation of Lezo LGU System..."

# Update package list and install dependencies
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib gunicorn

# Drop existing databases for a clean start
echo "Dropping existing databases for a clean start..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS lezo_db;" 2>/dev/null || true
sudo -u postgres psql -c "DROP DATABASE IF EXISTS test_lezo_db;" 2>/dev/null || true

# Set up PostgreSQL user and database with lezo_user as owner
echo "Setting up PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER lezo_user WITH PASSWORD 'Lezo2025';" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER lezo_user CREATEDB;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE lezo_db OWNER lezo_user;" 2>/dev/null || true

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

# Create .env file with email settings (update with your credentials)
echo "Creating .env file..."
cat > .env << EOL
DB_NAME=lezo_db
DB_USER=lezo_user
DB_PASSWORD=Lezo2025
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=$SECRET_KEY
DEBUG=True
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EOL

# Create static directory
echo "Creating static directory..."
mkdir -p static/core
chmod -R 755 static

# Run database migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create startup script
echo "Creating start.sh..."
cat > start.sh << EOL
#!/bin/bash
source venv/bin/activate
gunicorn -b 0.0.0.0:8000 --workers 1 lezo_lgu.wsgi
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

# Set up daily backup cron job
echo "Setting up daily backup cron job..."
(crontab -l 2>/dev/null; echo "0 2 * * * pg_dump -U lezo_user lezo_db > /home/$(whoami)/lezo_backups/backup_\$(date +\%Y\%m\%d).sql") | crontab -
mkdir -p /home/$(whoami)/lezo_backups

echo "Installation completed successfully!"
echo "To start the application, run './start.sh' or double-click 'lezo-system.desktop'."
echo "The system will prompt you to create a superuser on first access."
