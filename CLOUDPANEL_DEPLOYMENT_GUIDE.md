# CloudPanel Django Deployment Guide

## 🚀 **Complete Guide to Deploy Django Inventory App on CloudPanel**

### **Prerequisites**
1. CloudPanel server setup with Python support
2. Domain name pointed to your CloudPanel server
3. SSH access to your CloudPanel server
4. Git installed on the server

### **Step 1: Prepare Your Local Project**

1. **Environment Configuration**
   - Copy `.env.example` to `.env` and update with your values
   - Ensure all sensitive data is in environment variables

2. **Test Local Build**
   ```bash
   python manage.py collectstatic --noinput
   python manage.py migrate
   ```

### **Step 2: CloudPanel Server Setup**

1. **Login to CloudPanel**
   - Access your CloudPanel at `https://your-server-ip:8443`
   - Login with your credentials

2. **Create New Site**
   - Go to "Sites" → "Add Site"
   - Choose "Python" as application type
   - Set your domain name
   - Select Python version 3.11+

3. **Configure Python Application**
   - Set Document Root: `/home/cloudpanel/htdocs/yourdomain.com/`
   - Set Python Path: `/home/cloudpanel/htdocs/yourdomain.com/`
   - Set Application Entry Point: `wsgi:application`

### **Step 3: Upload and Configure Your Application**

1. **Upload Project Files**
   ```bash
   # Via SCP/SFTP or Git clone
   cd /home/cloudpanel/htdocs/yourdomain.com/
   git clone your-repository-url .
   
   # Or upload via CloudPanel File Manager
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**
   - Create `.env` file with production values:
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Update the following values:
   ```
   DJANGO_SECRET_KEY=your-generated-secret-key
   DEBUG=False
   DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
   ```

### **Step 4: Database Configuration**

**Option A: PostgreSQL (Recommended for Production)**
1. Create PostgreSQL database in CloudPanel
2. Update `DATABASE_URL` in your `.env` file
3. Install psycopg2: `pip install psycopg2-binary`

**Option B: SQLite (Simple but not recommended for production)**
- Keep current SQLite configuration
- Ensure write permissions: `chmod 664 db.sqlite3`

### **Step 5: Application Configuration**

1. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

2. **Run Database Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

### **Step 6: Configure Web Server**

1. **Update ALLOWED_HOSTS**
   - Edit `python_server/settings.py`
   - Add your domain to `ALLOWED_HOSTS`

2. **Configure CloudPanel Application Settings**
   - In CloudPanel: Sites → Your Site → Settings
   - Set Application Entry Point: `python_server.wsgi:application`
   - Set Environment Variables in CloudPanel interface

### **Step 7: SSL Configuration**

1. **Enable SSL in CloudPanel**
   - Go to Sites → Your Site → SSL/TLS
   - Enable "Let's Encrypt" for free SSL
   - Force HTTPS redirect

2. **Update Django Settings for HTTPS**
   ```python
   # Add to settings.py for production
   if not DEBUG:
       SECURE_SSL_REDIRECT = True
       SESSION_COOKIE_SECURE = True
       CSRF_COOKIE_SECURE = True
   ```

### **Step 8: Configure Static Files Serving**

1. **Nginx Configuration**
   - CloudPanel will automatically serve static files
   - Static files location: `/home/cloudpanel/htdocs/yourdomain.com/staticfiles/`

2. **Media Files (If needed)**
   ```python
   # In settings.py
   MEDIA_URL = '/media/'
   MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
   ```

### **Step 9: Application Monitoring**

1. **Log Files**
   - Application logs: CloudPanel → Sites → Your Site → Logs
   - Python errors: Check CloudPanel error logs

2. **Process Management**
   - CloudPanel automatically manages Python processes
   - Restart application: Sites → Your Site → Restart

### **Step 10: Final Testing**

1. **Test Endpoints**
   - Visit: `https://yourdomain.com/`
   - Admin: `https://yourdomain.com/admin/`
   - API: `https://yourdomain.com/api/`

2. **Verify Functionality**
   - Test user registration/login
   - Check API endpoints
   - Verify static files loading

### **🔧 Troubleshooting Common Issues**

1. **500 Internal Server Error**
   - Check CloudPanel error logs
   - Verify `ALLOWED_HOSTS` includes your domain
   - Ensure all environment variables are set

2. **Static Files Not Loading**
   - Run `python manage.py collectstatic --noinput`
   - Check static files permissions
   - Verify `STATIC_ROOT` path

3. **Database Connection Issues**
   - Verify `DATABASE_URL` format
   - Check database credentials
   - Ensure database exists

4. **Permission Denied Errors**
   - Check file/directory permissions
   - Ensure CloudPanel user owns files

### **🚀 Deployment Script**

Use the provided `deploy.sh` script for automated deployment:

```bash
chmod +x deploy.sh
./deploy.sh
```

### **🔄 Updates and Maintenance**

1. **For Code Updates**
   ```bash
   git pull origin main
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   # Restart application in CloudPanel
   ```

2. **Backup Strategy**
   - Regular database backups via CloudPanel
   - Code backups via Git repository
   - Media files backup (if applicable)

### **📊 Performance Optimization**

1. **Caching** (Optional)
   - Configure Redis caching
   - Enable Django cache framework

2. **CDN** (Optional)
   - Use CloudFlare or similar for static files
   - Configure `STATIC_URL` for CDN

### **🔐 Security Checklist**

- ✅ `DEBUG=False` in production
- ✅ Strong `SECRET_KEY` set
- ✅ HTTPS enabled with SSL certificate
- ✅ `ALLOWED_HOSTS` properly configured
- ✅ Database credentials secured
- ✅ Static files served securely
- ✅ Regular backups configured

Your Django Inventory Application should now be successfully deployed on CloudPanel! 🎉