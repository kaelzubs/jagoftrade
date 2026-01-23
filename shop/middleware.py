from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
import secrets

# myapp/middleware.py
class CSPReportOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy-Report-Only"] = (
            "script-src https://accounts.google.com/gsi/client; "
            "frame-src https://accounts.google.com/gsi/; "
            "connect-src https://accounts.google.com/gsi/;"
        )
        return response
    
class ForceWWWMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        # If request comes without www, redirect to www
        if not host.startswith("www."):
            new_url = request.build_absolute_uri().replace("://", "://www.", 1)
            return HttpResponsePermanentRedirect(new_url)
        return self.get_response(request)

class RemoveWWWMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host.startswith("www."):
            new_url = request.build_absolute_uri().replace("://www.", "://")
            return HttpResponsePermanentRedirect(new_url)
        return self.get_response(request)

class HTTPSRedirectMiddleware:
    """
    Middleware that redirects all HTTP requests to HTTPS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.is_secure():
            url = request.build_absolute_uri(request.get_full_path())
            secure_url = url.replace("http://", "https://")
            return HttpResponsePermanentRedirect(secure_url)
        response = self.get_response(request)
        return response
    
class HSTSMiddleware:
    """
    Middleware that adds HSTS headers to responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        return response
    
class SecurityHeadersMiddleware:
    """
    Middleware that adds various security headers to responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'same-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=()'
        return response

class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        cloudfront_domain = "https://d1234567890.cloudfront.net"

        csp_policy = (
            f"default-src 'self' {cloudfront_domain}; "

            # Scripts: GTM, Ads, jQuery, Popper, Bootstrap
            f"script-src 'self' {cloudfront_domain} "
            f"https://www.googletagmanager.com "
            f"https://pagead2.googlesyndication.com "
            f"https://code.jquery.com "
            f"https://cdn.jsdelivr.net "
            f"https://ep2.adtrafficquality.google "
            f"https://ep1.adtrafficquality.google "
            f"https://www.google-analytics.com "
            f"'unsafe-inline'; "

            # Styles
            f"style-src 'self' {cloudfront_domain} https://fonts.googleapis.com "
            f"https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com "
            f"https://cdnjs.cloudflare.com https://jagoftrade-bucket.s3.amazonaws.com "
            f"'unsafe-inline'; "

            # Fonts
            f"font-src 'self' {cloudfront_domain} https://fonts.gstatic.com https://cdnjs.cloudflare.com; "

            # Images
            f"img-src 'self' {cloudfront_domain} https://jagoftrade-bucket.s3.amazonaws.com "
            f"data: https://pagead2.googlesyndication.com; "

            # Media
            f"media-src 'self' {cloudfront_domain} https://jagoftrade-bucket.s3.amazonaws.com; "

            # Connections (XHR, fetch, analytics)
            f"connect-src 'self' {cloudfront_domain} "
            f"https://www.googletagmanager.com "
            f"https://pagead2.googlesyndication.com "
            f"https://cdn.jsdelivr.net "
            f"https://www.google-analytics.com "
            f"https://ep1.adtrafficquality.google "
            f"https://ep2.adtrafficquality.google; "

            # Frames (iframes for ads, GTM, Google)
            f"frame-src 'self' "
            f"https://googleads.g.doubleclick.net "
            f"https://pagead2.googlesyndication.com "
            f"https://ep2.adtrafficquality.google "
            f"https://www.google.com; "

            # Strong restrictions
            f"object-src 'none'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'; "
        )

        response["Content-Security-Policy"] = csp_policy
        return response

class ExpiredImageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/media/') or request.path.startswith('/static/'):
            if response.get('Content-Type', '').startswith('image/'):
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
                response['Pragma'] = 'no-cache'
        return response