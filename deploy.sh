#!/bin/bash

# CloudPanel Deployment Script for Django Application

echo "Starting deployment process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser (optional - uncomment if needed)
# echo "Creating superuser..."
# python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(email='admin@example.com').exists() else None"

echo "Deployment completed successfully!"