import requests
from django.conf import settings

PAYSTACK_INITIALIZE_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/{}"


def sanitize_phone_number(phone):
    """
    Sanitize phone number for Paystack.
    Removes common formatting characters and ensures it starts with + or digit.
    """
    if not phone:
        return None
    
    # Remove common formatting characters
    phone = str(phone).strip()
    phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
    
    # Ensure it starts with + or a digit
    if phone and phone[0] not in ("+", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
        return None
    
    return phone if phone else None


def prepare_customer_metadata(full_name=None, phone_number=None):
    """
    Prepare customer metadata for Paystack API.
    Returns dict with sanitized customer information.
    """
    metadata = {}
    
    if full_name:
        full_name_str = str(full_name).strip()
        if full_name_str:
            metadata["full_name"] = full_name_str
            # Try to extract first and last name for Paystack integration
            parts = full_name_str.split()
            if len(parts) >= 1:
                metadata["first_name"] = parts[0]
                if len(parts) >= 2:
                    metadata["last_name"] = " ".join(parts[1:])
    
    if phone_number:
        sanitized = sanitize_phone_number(phone_number)
        if sanitized:
            metadata["phone_number"] = sanitized
    
    return metadata


def initialize_transaction(amount, email, reference=None, callback_url=None, full_name=None, phone_number=None):
    """
    Initialize a Paystack transaction.
    - amount: decimal/float amount in NGN (e.g. 2500.00)
    - email: customer's email
    - reference: optional unique reference
    - callback_url: optional callback URL
    - full_name: customer's full name (optional)
    - phone_number: customer's phone number (optional)
    Returns parsed JSON from Paystack or raises requests.HTTPError on failure.
    """
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        # Paystack expects amount in kobo (smallest currency unit)
        "amount": int(round(float(amount) * 100)),
    }
    if reference:
        payload["reference"] = reference
    if callback_url:
        payload["callback_url"] = callback_url
    
    # Add customer metadata if provided
    metadata = prepare_customer_metadata(full_name, phone_number)
    if metadata:
        payload["metadata"] = metadata

    resp = requests.post(PAYSTACK_INITIALIZE_URL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("status"):
        raise Exception(f"Paystack initialize failed: {data}")
    return data.get("data")


def verify_transaction(reference):
    """Verify a Paystack transaction by reference."""
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    url = PAYSTACK_VERIFY_URL.format(reference)
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("status"):
        raise Exception(f"Paystack verify failed: {data}")
    return data.get("data")
