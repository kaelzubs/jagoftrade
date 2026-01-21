from django.http import HttpResponsePermanentRedirect


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
    
class ContentSecurityPolicyMiddleware:
    """
    Middleware that adds Content Security Policy headers to responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' https://accounts.google.com/gsi/client https://pagead2.googlesyndication.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://googleads.g.doubleclick.net https://pagead2.googlesyndication.com; "
            "font-src 'self'; "
            "connect-src 'self' https://accounts.google.com/gsi/ https://googleads.g.doubleclick.net; "
            "frame-src https://accounts.google.com/gsi/ https://googleads.g.doubleclick.net; "
        )
        response['Content-Security-Policy'] = csp_policy
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