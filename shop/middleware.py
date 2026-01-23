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

            # Scripts: your domain, CloudFront, trusted CDNs, Google services
            f"script-src 'self' {cloudfront_domain} "
            f"https://cdn.jsdelivr.net "
            f"https://ajax.googleapis.com "
            f"https://accounts.google.com/gsi/client "
            f"https://www.googletagmanager.com "
            f"https://pagead2.googlesyndication.com "
            f"https://code.jquery.com "
            f"https://ep1.adtrafficquality.google "
            f"https://ep2.adtrafficquality.google "
            f"https://stackpath.bootstrapcdn.com "
            f"https://www.googletagmanager.com/gtm.js?id=GTM-P97LQVH5	report-only	script-src-elem	(index):457 "
            f"https://www.googletagmanager.com/gtag/js?id=G-6L8TZYJD37	report-only	script-src-elem	(index):0 "
            f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1000566373865046	report-only	script-src-elem	(index):0 "
            f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6411693288489882	report-only	script-src-elem	(index):0 "
            f"https://code.jquery.com/jquery-3.5.1.slim.min.js	report-only	script-src-elem	(index):0"
            f"https://pagead2.googlesyndication.com/pagead/managed/js/adsense/m202601200101/show_ads_impl_fy2021.js	report-only	script-src-elem	adsbygoogle.js?clien…6411693288489882:45 "
            f"https://www.googletagmanager.com/gtag/js?id=G-6L8TZYJD37&cx=c&gtm=4e61m0	report-only	script-src-elem	gtm.js?id=GTM-P97LQVH5:98 "
            f"https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js	report-only	script-src-elem	(index):0 "
            f"https://www.google-analytics.com/g/collect?v=2&tid=G-6L8TZYJD37&gtm=45je61m0v9239609278za200zb9239598399zd9239598399&_p=1769142958192&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=318251196.1769142959&ul=en-us&sr=360x740&uaa=&uab=64&uafvl=Google%2520Chrome%3B143.0.7499.193%7CChromium%3B143.0.7499.193%7CNot%2520A(Brand%3B24.0.0.0&uamb=1&uam=SM-G955U&uap=Android&uapv=8.0.0&uaw=0&are=1&frm=0&pscdl=noapi&_s=1&tag_exp=103116026~103200004~104527906~104528500~104684208~104684211~105391253~115938466~115938468~116682875~116992598~117041588~117099529~117223566&sid=1769142959&sct=1&seg=0&dl=https%3A%2F%2Fwww.jagoftrade.com%2F&dr=https%3A%2F%2Fwww.jagoftrade.com%2F&dt=JagofTrade%20%E2%80%93%20Affiliate%20Marketplace%20for%20Smarter%20Choices&en=page_view&_fv=1&_nsi=1&_ss=1&_ee=1&tfd=4945	report-only	connect-src	js?id=G-6L8TZYJD37:222 "
            f"https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js	report-only	script-src-elem	(index):0 "
            f"https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css.map	blocked	connect-src	(unknown) "
            f"https://googleads.g.doubleclick.net	report-only	frame-src	pagead2.googlesyndication.com/:0 "
            f"https://ep1.adtrafficquality.google/getconfig/sodar?sv=200&tid=gda&tv=r20260121&st=env&sjk=3012886076675421	report-only	connect-src	show_ads_impl_fy2021.js:106 "
            f"https://ep2.adtrafficquality.google/sodar/sodar2.js	report-only	script-src-elem	show_ads_impl_fy2021.js:105 "
            f"https://ep2.adtrafficquality.google	report-only	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://ep2.adtrafficquality.google	blocked	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://www.google.com	report-only	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://www.google.com "
            f"'unsafe-inline'; "

            # Styles: your domain, CloudFront, Google Fonts, Bootstrap, cdnjs, S3 bucket
            f"style-src 'self' {cloudfront_domain} "
            f"https://fonts.googleapis.com "
            f"https://cdn.jsdelivr.net "
            f"https://stackpath.bootstrapcdn.com "
            f"https://cdnjs.cloudflare.com "
            f"https://jagoftrade-bucket.s3.amazonaws.com "
            f"https://www.googletagmanager.com/gtm.js?id=GTM-P97LQVH5	report-only	script-src-elem	(index):457 "
            f"https://www.googletagmanager.com/gtag/js?id=G-6L8TZYJD37	report-only	script-src-elem	(index):0 "
            f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1000566373865046	report-only	script-src-elem	(index):0 "
            f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6411693288489882	report-only	script-src-elem	(index):0 "
            f"https://code.jquery.com/jquery-3.5.1.slim.min.js	report-only	script-src-elem	(index):0"
            f"https://pagead2.googlesyndication.com/pagead/managed/js/adsense/m202601200101/show_ads_impl_fy2021.js	report-only	script-src-elem	adsbygoogle.js?clien…6411693288489882:45 "
            f"https://www.googletagmanager.com/gtag/js?id=G-6L8TZYJD37&cx=c&gtm=4e61m0	report-only	script-src-elem	gtm.js?id=GTM-P97LQVH5:98 "
            f"https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js	report-only	script-src-elem	(index):0 "
            f"https://www.google-analytics.com/g/collect?v=2&tid=G-6L8TZYJD37&gtm=45je61m0v9239609278za200zb9239598399zd9239598399&_p=1769142958192&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=318251196.1769142959&ul=en-us&sr=360x740&uaa=&uab=64&uafvl=Google%2520Chrome%3B143.0.7499.193%7CChromium%3B143.0.7499.193%7CNot%2520A(Brand%3B24.0.0.0&uamb=1&uam=SM-G955U&uap=Android&uapv=8.0.0&uaw=0&are=1&frm=0&pscdl=noapi&_s=1&tag_exp=103116026~103200004~104527906~104528500~104684208~104684211~105391253~115938466~115938468~116682875~116992598~117041588~117099529~117223566&sid=1769142959&sct=1&seg=0&dl=https%3A%2F%2Fwww.jagoftrade.com%2F&dr=https%3A%2F%2Fwww.jagoftrade.com%2F&dt=JagofTrade%20%E2%80%93%20Affiliate%20Marketplace%20for%20Smarter%20Choices&en=page_view&_fv=1&_nsi=1&_ss=1&_ee=1&tfd=4945	report-only	connect-src	js?id=G-6L8TZYJD37:222 "
            f"https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js	report-only	script-src-elem	(index):0 "
            f"https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css.map	blocked	connect-src	(unknown) "
            f"https://googleads.g.doubleclick.net	report-only	frame-src	pagead2.googlesyndication.com/:0 "
            f"https://ep1.adtrafficquality.google/getconfig/sodar?sv=200&tid=gda&tv=r20260121&st=env&sjk=3012886076675421	report-only	connect-src	show_ads_impl_fy2021.js:106 "
            f"https://ep2.adtrafficquality.google/sodar/sodar2.js	report-only	script-src-elem	show_ads_impl_fy2021.js:105 "
            f"https://ep2.adtrafficquality.google	report-only	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://ep2.adtrafficquality.google	blocked	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://www.google.com	report-only	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://www.google.com "
            f"'unsafe-inline'; "

            # Fonts: your domain, CloudFront, Google Fonts, cdnjs
            f"font-src 'self' {cloudfront_domain} "
            f"https://fonts.gstatic.com "
            f"https://cdnjs.cloudflare.com; "

            # Images: your domain, CloudFront, S3 bucket, data URIs, Google Ads pixels
            f"img-src 'self' {cloudfront_domain} "
            f"https://jagoftrade-bucket.s3.amazonaws.com "
            f"data: "
            f"https://pagead2.googlesyndication.com; "

            # Media: your domain, CloudFront, S3 bucket
            f"media-src 'self' {cloudfront_domain} https://jagoftrade-bucket.s3.amazonaws.com; "

            # Connections: your domain, CloudFront, Google services, CDNs
            f"connect-src 'self' {cloudfront_domain} "
            f"https://accounts.google.com "
            f"https://cdn.jsdelivr.net "
            f"https://www.googletagmanager.com "
            f"https://pagead2.googlesyndication.com "
            f"https://ep1.adtrafficquality.google "
            f"https://ep2.adtrafficquality.google "
            f"https://www.google-analytics.com; "
            f"https://stackpath.bootstrapcdn.com; "
            f"https://www.googletagmanager.com/gtm.js?id=GTM-P97LQVH5	report-only	script-src-elem	(index):457 "
            f"https://www.googletagmanager.com/gtag/js?id=G-6L8TZYJD37	report-only	script-src-elem	(index):0 "
            f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1000566373865046	report-only	script-src-elem	(index):0 "
            f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6411693288489882	report-only	script-src-elem	(index):0 "
            f"https://code.jquery.com/jquery-3.5.1.slim.min.js	report-only	script-src-elem	(index):0"
            f"https://pagead2.googlesyndication.com/pagead/managed/js/adsense/m202601200101/show_ads_impl_fy2021.js	report-only	script-src-elem	adsbygoogle.js?clien…6411693288489882:45 "
            f"https://www.googletagmanager.com/gtag/js?id=G-6L8TZYJD37&cx=c&gtm=4e61m0	report-only	script-src-elem	gtm.js?id=GTM-P97LQVH5:98 "
            f"https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js	report-only	script-src-elem	(index):0 "
            f"https://www.google-analytics.com/g/collect?v=2&tid=G-6L8TZYJD37&gtm=45je61m0v9239609278za200zb9239598399zd9239598399&_p=1769142958192&gcd=13l3l3l3l1l1&npa=0&dma=0&cid=318251196.1769142959&ul=en-us&sr=360x740&uaa=&uab=64&uafvl=Google%2520Chrome%3B143.0.7499.193%7CChromium%3B143.0.7499.193%7CNot%2520A(Brand%3B24.0.0.0&uamb=1&uam=SM-G955U&uap=Android&uapv=8.0.0&uaw=0&are=1&frm=0&pscdl=noapi&_s=1&tag_exp=103116026~103200004~104527906~104528500~104684208~104684211~105391253~115938466~115938468~116682875~116992598~117041588~117099529~117223566&sid=1769142959&sct=1&seg=0&dl=https%3A%2F%2Fwww.jagoftrade.com%2F&dr=https%3A%2F%2Fwww.jagoftrade.com%2F&dt=JagofTrade%20%E2%80%93%20Affiliate%20Marketplace%20for%20Smarter%20Choices&en=page_view&_fv=1&_nsi=1&_ss=1&_ee=1&tfd=4945	report-only	connect-src	js?id=G-6L8TZYJD37:222 "
            f"https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/js/bootstrap.bundle.min.js	report-only	script-src-elem	(index):0 "
            f"https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css.map	blocked	connect-src	(unknown) "
            f"https://googleads.g.doubleclick.net	report-only	frame-src	pagead2.googlesyndication.com/:0 "
            f"https://ep1.adtrafficquality.google/getconfig/sodar?sv=200&tid=gda&tv=r20260121&st=env&sjk=3012886076675421	report-only	connect-src	show_ads_impl_fy2021.js:106 "
            f"https://ep2.adtrafficquality.google/sodar/sodar2.js	report-only	script-src-elem	show_ads_impl_fy2021.js:105 "
            f"https://ep2.adtrafficquality.google	report-only	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://ep2.adtrafficquality.google	blocked	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://www.google.com	report-only	frame-src	ep2.adtrafficquality.google/:0 "
            f"https://www.google.com "

            # Frames: allow Google Sign-In, Ads iframes
            f"frame-src 'self' "
            f"https://accounts.google.com/gsi/ "
            f"https://googleads.g.doubleclick.net "
            f"https://pagead2.googlesyndication.com; "
            f"https://accounts.google.com/gsi/ "
            f"https://ep2.adtrafficquality.google "
            f"https://stackpath.bootstrapcdn.com "
            f"https://www.google.com; "

            # Strong restrictions
            f"object-src 'none'; "
            f"frame-ancestors 'self'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
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