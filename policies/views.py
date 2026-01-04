from datetime import date
from django.shortcuts import render

# Create your views here.
def about(request):
    context = {
        "company_name": "JagofTrade",
        "mission_statement": "We empower shoppers in the US and beyond to make confident, value‑driven decisions.",
        "values_statement": "Integrity, clarity, and accessibility guide everything we publish.",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/about.html", context)

def privacy(request):
    context = {
        "company_name": "JagofTrade",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/privacy.html", context)

def terms(request):
    context = {
        "company_name": "JagofTrade",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/terms.html", context)

def affiliate(request):
    context = {
        "company_name": "JagofTrade",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/affiliate.html", context)

def editorial(request):
    context = {
        "company_name": "JagofTrade",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/editorial.html", context)

def advertising(request):
    context = {
        "company_name": "JagofTrade",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/advertising.html", context)

def user_content(request):
    context = {
        "company_name": "JagofTrade",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/user-content.html", context)

def accessibility(request):
    context = {
        "company_name": "JagofTrade",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/accessibility.html", context)

def faqs(request):
    context = {
        "company_name": "JagofTrade",
        "contact_email": "support@jagoftrade.com",
        "location": "Newark, Delaware, United States",
        "effective_date": date.today().strftime("%B %d, %Y"),
    }

    return render(request, "policies/faqs.html", context)