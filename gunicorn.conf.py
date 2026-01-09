# Gunicorn Configuration File for CloudPanel Deployment

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = 3
worker_class = "sync"
worker_connections = 1000

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "inventory_app"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Application settings
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# Debug settings
reload = False