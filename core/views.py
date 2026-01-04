from django.shortcuts import render, redirect
from catalog.models import Product
import json
from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.conf import settings

CONSENT_COOKIE_NAME = "cookie_consent"
CONSENT_MAX_AGE = 365 * 24 * 60 * 60  # one year

def home(request):
    products = Product.objects.prefetch_related('images').filter(is_active=True)[:40]
    return render(request, 'core/home.html', {'products': products})

def cookie_settings(request):
    """
    Render a cookie settings page and allow users to update their preferences.
    """
    if request.method == "POST":
        data = {
            "essential": True,  # always true; essential cookies cannot be disabled
            "analytics": bool(request.POST.get("analytics")),
            "marketing": bool(request.POST.get("marketing")),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": 1,
        }
        response = redirect("core:cookie_settings")
        response.set_cookie(
            CONSENT_COOKIE_NAME,
            json.dumps(data),
            max_age=CONSENT_MAX_AGE,
            secure=True,          # set True in production with HTTPS
            samesite="Lax",
            httponly=False        # must be readable by JS to gate scripts client-side
        )
        return response

    # Read current preferences if present
    raw = request.COOKIES.get(CONSENT_COOKIE_NAME)
    prefs = {"essential": True, "analytics": False, "marketing": False}
    if raw:
        try:
            prefs.update(json.loads(raw))
        except Exception:
            pass

    return render(request, "partials/cookie_settings.html", {"prefs": prefs})

def restricted_view(request):
    raise PermissionDenied

def robots_txt(request):
    if settings.DEBUG == True:
        # Block all crawlers in development/staging
        content = "User-agent: *\nDisallow: /"
    else:
        # Allow crawlers in production
        content = (
            "User-agent: *\n"
            "Disallow: /admin/\n"
            "Disallow: /cart/\n"
            "Disallow: /checkout/\n"
            "Allow: /\n"
            "Sitemap: https://jagoftrade.com/sitemap.xml\n"
        )
    return HttpResponse(content, content_type="text/plain")
