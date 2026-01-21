"""
URL configuration for shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.conf.urls import handler404, handler500, handler403
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from shop.sitemaps import ProductSitemap, CategorySitemap, StaticViewSitemap

admin.site.site_header = "JagofTrade Administration"
admin.site.site_title = "JagofTrade Portal"
admin.site.index_title = "Welcome to JagofTrade Admin"

sitemaps_dict = {
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "static": StaticViewSitemap,
}

def custom_permission_denied(request, exception):
    return render(request, "errors/403.html", status=403)

def custom_page_not_found(request, exception):
    return render(request, "errors/404.html", status=404)

def custom_server_error(request):
    return render(request, "errors/500.html", status=500)

handler403 = custom_permission_denied
handler404 = custom_page_not_found
handler500 = custom_server_error

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core app at root
    path('', include('core.urls')),

    # Other apps
    path('catalog/', include('catalog.urls')),
    path('orders/', include('orders.urls')),
    path('policies/', include(('policies.urls', 'policies'), namespace="policies")),

    # Accounts (custom + allauth)
    path('accounts/', include(('accounts.urls', 'accounts'), namespace="accounts")),
    path('auth-accounts/', include('allauth.urls')),

    # Favicon
    path('favicon.ico/', RedirectView.as_view(url=staticfiles_storage.url('img/jagoftrade.png'))),

    # Sitemap
    path('sitemap.xml/', sitemap, {"sitemaps": sitemaps_dict}, name="django_sitemap"),
    
    path("ads.txt/", TemplateView.as_view(template_name="ads.txt", content_type="text/plain")),
    path("limit.txt/", TemplateView.as_view(template_name="limit.txt", content_type="text/plain")),

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    