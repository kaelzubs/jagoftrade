import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from paapi.service import PaapiService
from paapi.exceptions import PaapiError, PaapiRateLimitError, PaapiRequestError

service = PaapiService()

@require_GET
def paapi_search(request):
    keywords = request.GET.get("q", "").strip()
    count = request.GET.get("count", "10")
    try:
        item_count = max(1, min(10, int(count)))  # Amazon allows up to 10 per request for PAAPI v5
    except ValueError:
        item_count = 10

    if not keywords:
        return JsonResponse({"error": "q (keywords) is required"}, status=400)

    try:
        items = service.search(keywords=keywords, item_count=item_count)
        return JsonResponse({"items": items}, status=200)
    except PaapiRateLimitError as e:
        return JsonResponse({"error": str(e)}, status=429)
    except PaapiRequestError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except PaapiError as e:
        return JsonResponse({"error": str(e)}, status=502)


@require_GET
def paapi_get_items(request):
    asins = request.GET.get("asins", "")
    asin_list = [a.strip() for a in asins.split(",") if a.strip()]
    if not asin_list:
        return JsonResponse({"error": "asins (comma-separated) is required"}, status=400)

    try:
        items = service.get_items(asin_list)
        return JsonResponse({"items": items}, status=200)
    except PaapiRateLimitError as e:
        return JsonResponse({"error": str(e)}, status=429)
    except PaapiRequestError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except PaapiError as e:
        return JsonResponse({"error": str(e)}, status=502)