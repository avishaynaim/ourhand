"""
Authentication module for API endpoints.
Provides API key authentication decorator.
"""

import os
import logging
import secrets
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


def require_api_key(f):
    """
    Decorator to require API key authentication for endpoints.

    API key can be provided via:
    - X-API-Key header
    - api_key query parameter

    Same-origin requests from the dashboard are allowed without API key.
    Returns 401 Unauthorized if API key is missing or invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if API_KEY is configured
        expected_api_key = os.environ.get('API_KEY')

        # If no API key is configured, check environment
        if not expected_api_key:
            if os.environ.get('FLASK_ENV') == 'production':
                logger.error("SECURITY: API_KEY must be set in production!")
                return jsonify({
                    'error': 'Server misconfiguration - API key required',
                    'error_en': 'Server misconfiguration - API key required'
                }), 500
            logger.warning("API_KEY not configured - API endpoints are unprotected (dev mode)")
            return f(*args, **kwargs)

        # Allow same-origin dashboard requests without API key
        # Behind reverse proxies (Railway), host_url may be http:// while browser uses https://
        # Check both Referer and Origin headers, normalize protocol
        host = request.host_url.rstrip('/')
        host_http = host.replace('https://', 'http://')
        host_https = host.replace('http://', 'https://')
        hosts = {host, host_http, host_https}
        # Also check X-Forwarded-Host if behind proxy
        fwd_host = request.headers.get('X-Forwarded-Host', '')
        if fwd_host:
            hosts.add('http://' + fwd_host)
            hosts.add('https://' + fwd_host)

        referer = request.headers.get('Referer', '')
        origin = request.headers.get('Origin', '')
        if referer and any(referer.startswith(h) for h in hosts):
            return f(*args, **kwargs)
        if origin and origin.rstrip('/') in hosts:
            return f(*args, **kwargs)
        # Sec-Fetch-Site: same-origin is sent by modern browsers for same-origin fetch
        if request.headers.get('Sec-Fetch-Site') == 'same-origin':
            return f(*args, **kwargs)

        # Get API key from request
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not api_key:
            logger.warning(f"API key missing for {request.path} from {request.remote_addr}")
            return jsonify({
                'error': 'אין הרשאה - נדרש מפתח API',
                'error_en': 'Unauthorized - API key required'
            }), 401

        # Use constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(api_key, expected_api_key):
            logger.warning(f"Invalid API key for {request.path} from {request.remote_addr}")
            return jsonify({
                'error': 'מפתח API לא תקין',
                'error_en': 'Invalid API key'
            }), 401

        # API key is valid
        return f(*args, **kwargs)

    return decorated_function


def optional_api_key(f):
    """
    Decorator for endpoints that can work with or without authentication.
    If API key is provided, it must be valid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        expected_api_key = os.environ.get('API_KEY')

        if not expected_api_key:
            return f(*args, **kwargs)

        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        # If API key is provided, it must be valid (constant-time comparison)
        if api_key and not secrets.compare_digest(api_key, expected_api_key):
            logger.warning(f"Invalid API key for {request.path} from {request.remote_addr}")
            return jsonify({
                'error': 'מפתח API לא תקין',
                'error_en': 'Invalid API key'
            }), 401

        return f(*args, **kwargs)

    return decorated_function
