// In base.html, after including cookie_banner.html
function loadAnalytics() {
    // Example: Google Analytics gtag
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID";
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('config', 'GA_MEASUREMENT_ID', { anonymize_ip: true });
}

function loadMarketing() {
    // Example placeholder for marketing pixel. Only load if consent.marketing === true.
    if (consent && consent.marketing === true) {
        // Example: Facebook Pixel placeholder
        !(function(f,b,e,v,n,t,s){
            if(f.fbq) return; n=f.fbq=function(){n.callMethod ?
            n.callMethod.apply(n,arguments) : n.queue.push(arguments)};
            if(!f._fbq) f._fbq=n; n.push=n; n.loaded=!0; n.version="2.0";
            n.queue=[]; t=b.createElement(e); t.async=!0;
            t.src=v; s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)
        })(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");

        fbq("init", "YOUR_PIXEL_ID");  
        fbq("track", "PageView");
        console.log("Marketing pixel loaded");
    } else {
        console.log("Marketing consent not given — pixel not loaded");
    }
}

// If consent cookie already exists, fire immediately; else banner will dispatch after user choice
window.addEventListener("cookie-consent-ready", function(e) {
    var consent = e.detail || {};
    if (consent.analytics) loadAnalytics();
    if (consent.marketing) loadMarketing();
});

// Example: Load analytics immediately if consent already given
var consent = getCookieConsent(); // Assume this function retrieves existing consent
if (consent) {
    if (consent.analytics) loadAnalytics();
    if (consent.marketing) loadMarketing();
}
