"""Ponto de entrada de produção para o Gunicorn."""

from backend_server import app, initialize_runtime


initialize_runtime()
