from functools import wraps

from flask import g, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from database import Session
from models import AuditLog


def authenticated(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        g.user_id = int(get_jwt_identity())
        return fn(*args, **kwargs)
    return wrapper


def company_required(fn):
    @wraps(fn)
    @authenticated
    def wrapper(*args, **kwargs):
        value = request.headers.get("X-Company-ID")
        if not value or not value.isdigit():
            return {"error": "X-Company-ID header is required"}, 400
        g.company_id = int(value)
        return fn(*args, **kwargs)
    return wrapper


def audit(action, entity, entity_id=None, details=""):
    Session.add(AuditLog(
        user_id=getattr(g, "user_id", None), company_id=getattr(g, "company_id", None),
        action=action, entity_type=entity, entity_id=entity_id, details=details
    ))
