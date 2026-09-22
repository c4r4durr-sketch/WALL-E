"""
Middleware HTTP que publica el request actual para los signals de
auditoría (ver infrastructure/contexto.py para el porqué).
"""

from ..infrastructure.contexto import request_actual


class RequestActualMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request_actual.set(request)
        try:
            return self.get_response(request)
        finally:
            request_actual.reset(token)
