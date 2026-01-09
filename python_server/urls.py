"""
URL configuration for python_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


# Simple home view
def home_view(request):
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>United Fins - Inventory Management</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                text-align: center;
                padding: 2rem;
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 1rem;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
            p {
                font-size: 1.2rem;
                margin-bottom: 2rem;
            }
            .api-links {
                display: flex;
                gap: 1rem;
                justify-content: center;
                flex-wrap: wrap;
            }
            .api-link {
                padding: 10px 20px;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s;
            }
            .api-link:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hello United Fins!</h1>
            <p>Welcome to the Inventory Management System</p>
            <div class="api-links">
                <a href="/api/" class="api-link">📊 API Documentation</a>
                <a href="/swagger/" class="api-link">📚 Swagger UI</a>
                <a href="/admin/" class="api-link">🔧 Admin Panel</a>
                <a href="/api/categories/" class="api-link">📋 Categories API</a>
                <a href="/api/vendors/" class="api-link">🏢 Vendors API</a>
            </div>
        </div>
    </body>
    </html>
    """)

# API Documentation view
def api_docs_view(request):
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Documentation - United Fins Inventory</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
                background: #f5f5f5;
                color: #333;
            }
            .header {
                text-align: center;
                margin-bottom: 2rem;
                padding: 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
            }
            .endpoint {
                background: white;
                padding: 1.5rem;
                margin: 1rem 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .method {
                display: inline-block;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                margin-right: 0.5rem;
            }
            .get { background: #28a745; }
            .post { background: #007bff; }
            .put { background: #ffc107; color: #333; }
            .delete { background: #dc3545; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 United Fins Inventory API</h1>
            <p>RESTful API for Inventory Management System</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span>/api/categories/</h3>
            <p>Get all product categories</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span>/api/vendors/</h3>
            <p>Get all vendors</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span>/api/users/</h3>
            <p>Get user information (requires authentication)</p>
        </div>
        
        <div style="text-align: center; margin-top: 2rem;">
            <a href="/swagger/" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">📚 Full Swagger Documentation</a>
            <a href="/" style="padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 5px; margin-left: 1rem;">🏠 Home</a>
        </div>
    </body>
    </html>
    """)

# drf-spectacular imports
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    
    # API endpoints with /api/ prefix
    path('api/', api_docs_view, name='api-docs'),
    path('api/vendors/', include('vendors.urls')),
    path('api/users/', include('users.urls')),
    path('api/categories/', include('categories.urls')),
    
    # API Documentation endpoints
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
