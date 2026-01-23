from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
import os

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
    """
    Custom CSP middleware that sets Content-Security-Policy headers
    to allow serving static/media files from CloudFront (S3).
    """

    def process_response(self, request, response):
        cloudfront_domain = "https://d1234567890.cloudfront.net"
        csp_policy = (
            f"default-src 'self' {cloudfront_domain}; "
            f"script-src 'self' {cloudfront_domain} "
            f"https://cdn.jsdelivr.net "
            f"https://ajax.googleapis.com "
            f"https://accounts.google.com/gsi/client "
            f"https://www.googletagmanager.com "
            f"https://pagead2.googlesyndication.com "
            f"https://code.jquery.com "
            f"https://ep2.adtrafficquality.google "
            f"'unsafe-inline'; "
            f"style-src 'self' {cloudfront_domain} https://fonts.googleapis.com https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com https://jagoftrade-bucket.s3.amazonaws.com 'unsafe-inline'; "
            f"font-src 'self' {cloudfront_domain} https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            f"img-src 'self' {cloudfront_domain} https://jagoftrade-bucket.s3.amazonaws.com data: https://pagead2.googlesyndication.com https://jagoftrade-bucket.s3.amazonaws.com ; "
            f"media-src 'self' {cloudfront_domain} https://jagoftrade-bucket.s3.amazonaws.com ; "
            f"connect-src 'self' {cloudfront_domain} https://accounts.google.com https://cdn.jsdelivr.net https://www.googletagmanager.com https://pagead2.googlesyndication.com https://ep1.adtrafficquality.google https://ep2.adtrafficquality.google https://www.google-analytics.com; "
            f"frame-src 'self' https://accounts.google.com/gsi/ https://googleads.g.doubleclick.net https://pagead2.googlesyndication.com <URL>; "
            f"object-src 'none'; "
            f"frame-ancestors 'self'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
        )
        
        # csp_policy = (
        #     f"default-src 'self' {cloudfront_domain}; "
        #     f"script-src 'self' {cloudfront_domain} https://cdn.jsdelivr.net https://ajax.googleapis.com https://accounts.google.com/gsi/client https://www.googletagmanager.com https://pagead2.googlesyndication.com https://code.jquery.com 'unsafe-inline'; "
        #     f"https://accounts.google.com/gsi/client https://www.googletagmanager.com "
        #     f"https://pagead2.googlesyndication.com https://code.jquery.com 'unsafe-inline'; "
        #     f"style-src 'self' {cloudfront_domain} https://fonts.googleapis.com https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://jagoftrade-bucket.s3.amazonaws.com https://cdnjs.cloudflare.com 'unsafe-inline'; "
        #     f"https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com 'unsafe-inline'; "
        #     f"font-src 'self' {cloudfront_domain} https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        #     f"img-src 'self' {cloudfront_domain} https://jagoftrade-bucket.s3.amazonaws.com data: https://pagead2.googlesyndication.com; "
        #     f"https://pagead2.googlesyndication.com; "
        #     f"media-src 'self' {cloudfront_domain} https://jagoftrade-bucket.s3.amazonaws.com; "
        #     f"connect-src 'self' {cloudfront_domain} https://accounts.google.com https://cdn.jsdelivr.net https://www.googletagmanager.com https://pagead2.googlesyndication.com https://accounts.google.com https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com; "
        #     f"https://www.googletagmanager.com https://pagead2.googlesyndication.com "
        #     f"https://ep1.adtrafficquality.google https://www.google-analytics.com; "
        #     f"frame-src 'self' https://accounts.google.com/gsi/ https://googleads.g.doubleclick.net https://pagead2.googlesyndication.com; "
        #     f"https://pagead2.googlesyndication.com; "
        #     f"object-src 'none'; "
        #     f"frame-ancestors 'self'; "
        #     f"base-uri 'self'; "
        #     f"form-action 'self'; "
        # )
    
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