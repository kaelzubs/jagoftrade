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
        s3_bucket = "https://jagoftrade-bucket.s3.amazonaws.com"

        csp_policy = (
            # Default fallback
            f"default-src 'self' {cloudfront_domain}; "

            # Scripts: GTM, AdSense, Google Ads, Analytics, CDNs
            f"script-src 'self' {cloudfront_domain} "
            f"https://www.googletagmanager.com "
            f"https://www.google-analytics.com "
            f"https://pagead2.googlesyndication.com "
            f"https://googleads.g.doubleclick.net "
            f"https://www.gstatic.com "
            f"https://code.jquery.com "
            f"https://cdn.jsdelivr.net "
            f"https://stackpath.bootstrapcdn.com "
            f"https://cdnjs.cloudflare.com "
            f"https://connect.facebook.net "
            f"https://platform.twitter.com "
            f"https://accounts.google.com/gsi/client "
            f"https://ep2.adtrafficquality.google "
            f"'unsafe-inline' 'unsafe-eval' strict-dynamic; "

            # Script src elem (inline scripts)
            f"script-src-elem 'self' {cloudfront_domain} "
            f"https://www.googletagmanager.com/gtm.js "
            f"https://www.googletagmanager.com/gtag/js "
            f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js "
            f"https://code.jquery.com/jquery-3.5.1.slim.min.js "
            f"https://cdn.jsdelivr.net/npm/popper.js "
            f"https://cdn.jsdelivr.net/npm/bootstrap "
            f"https://ep2.adtrafficquality.google/sodar/sodar2.js "
            f"https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js "
            f"https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js "
            f"https://pagead2.googlesyndication.com "
            f"https://googleads.g.doubleclick.net "
            f"https://www.jagoftrade.com "
            f"'unsafe-inline'; "

            # Styles: Fonts, CDNs, AdSense
            f"style-src 'self' {cloudfront_domain} {s3_bucket} "
            f"https://fonts.googleapis.com "
            f"https://cdn.jsdelivr.net "
            f"https://stackpath.bootstrapcdn.com "
            f"https://cdnjs.cloudflare.com "
            f"https://pagead2.googlesyndication.com "
            f"'unsafe-inline'; "

            # Fonts
            f"font-src 'self' {cloudfront_domain} {s3_bucket} "
            f"https://fonts.gstatic.com "
            f"https://cdnjs.cloudflare.com "
            f"data:; "

            # Images: AdSense, Analytics, S3, CloudFront
            f"img-src 'self' {cloudfront_domain} {s3_bucket} "
            f"https://tpc.googlesyndication.com "
            f"https://pagead2.googlesyndication.com "
            f"https://googleads.g.doubleclick.net "
            f"https://www.googletagmanager.com "
            f"https://www.google-analytics.com "
            f"https://ssl.gstatic.com "
            f"https://www.gstatic.com "
            f"https://stats.g.doubleclick.net "
            f"https://ad.doubleclick.net "
            f"https://www.facebook.com "
            f"https://platform.twitter.com "
            f"https://ep1.adtrafficquality.google "
            f"https://www.jagoftrade.com "
            f"data: blob:; "

            # Media
            f"media-src 'self' {cloudfront_domain} {s3_bucket} "
            f"https://pagead2.googlesyndication.com; "

            # Connections: XHR, fetch, WebSocket for ads, analytics, GTM
            f"connect-src 'self' {cloudfront_domain} {s3_bucket} "
            f"https://www.googletagmanager.com "
            f"https://pagead2.googlesyndication.com "
            f"https://googleads.g.doubleclick.net "
            f"https://www.google-analytics.com "
            f"https://www.google-analytics.com/g/collect "
            f"https://analytics.google.com "
            f"https://region1.analytics.google.com "
            f"https://region2.analytics.google.com "
            f"https://www.google.com "
            f"https://accounts.google.com "
            f"https://accounts.google.com/gsi/client "
            f"https://apis.google.com "
            f"https://ep1.adtrafficquality.google "
            f"https://ep2.adtrafficquality.google "
            f"https://cdn.jsdelivr.net "
            f"https://api.github.com "
            f"https://connect.facebook.net "
            f"https://graph.instagram.com "
            f"wss: https:; "

            # Frames: Ad iframes, Google Sign-In, GTM
            f"frame-src 'self' "
            f"https://googleads.g.doubleclick.net "
            f"https://tpc.googlesyndication.com "
            f"https://pagead2.googlesyndication.com "
            f"https://accounts.google.com/gsi "
            f"https://accounts.google.com "
            f"https://www.google.com/recaptcha/ "
            f"https://recaptcha.net/recaptcha/ "
            f"https://www.youtube.com "
            f"https://youtube.com "
            f"https://www.facebook.com "
            f"https://platform.twitter.com "
            f"https://ep2.adtrafficquality.google; "
            

            # Strict restrictions
            f"object-src 'none'; "
            f"frame-ancestors 'self'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
            f"upgrade-insecure-requests; "
        )

        response["Content-Security-Policy"] = csp_policy
        response["Content-Security-Policy-Report-Only"] = csp_policy
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=(), '
            'accelerometer=()'
        )
        
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