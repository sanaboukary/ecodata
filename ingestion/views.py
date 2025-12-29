import os
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .utils import run_ingestion_adapter

def health(request):
    return JsonResponse({"status": "ok"})

@csrf_exempt
def start_ingestion(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST expected")
    payload = {}
    try:
        import json
        payload = json.loads(request.body or "{}")
    except Exception:
        pass
    source = payload.get("source","brvm")
    count = run_ingestion_adapter(source, payload)
    return JsonResponse({"ok": True, "source": source, "upserted": count})
