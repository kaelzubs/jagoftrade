import mailchimp_marketing as MailchimpMarketing
from django.conf import settings
from mailchimp_marketing.api_client import ApiClientError
from mailchimp_marketing import Client

client = Client()
client.set_config({
    "api_key": settings.MAILCHIMP_API_KEY,
    "server": settings.MAILCHIMP_DATA_CENTER,  # e.g. "us20"
})

def subscribe_user(email, list_id=None):
    """
    Subscribe a user to a Mailchimp audience list.
    :param email: subscriber's email address
    :param list_id: optional Mailchimp list ID (defaults to settings.MAILCHIMP_AUDIENCE_ID)
    """
    if list_id is None:
        list_id = settings.MAILCHIMP_EMAIL_LIST_ID

    try:
        response = client.lists.add_list_member(
            list_id,
            {
                "email_address": email,
                "status": "subscribed",
            }
        )
        return {"success": True, "response": response}
    except ApiClientError as error:
        error_json = error.text or ""
        if "Member Exists" in error_json:
            return {"success": False, "reason": "exists"}
        elif "pending" in error_json.lower():
            return {"success": False, "reason": "pending"}
        else:
            return {"success": False, "reason": "other", "error": error_json}

