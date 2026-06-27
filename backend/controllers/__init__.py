from flask import g, request
from sqlalchemy import String, cast, or_, select

from database import Session
from middleware import audit
from schemas import ValidationError, require


def list_entities(model):
    query = select(model).where(model.company_id == g.company_id)
    search = request.args.get("search", "").strip()
    if search:
        columns = [c for c in model.__table__.columns if isinstance(c.type, String)]
        query = query.where(or_(*[cast(c, String).ilike(f"%{search}%") for c in columns]))
    return {"items": [row.to_dict() for row in Session.scalars(query.order_by(model.id.desc())).all()]}


def create_entity(model, allowed, required=()):
    data = request.get_json(silent=True) or {}
    require(data, *required)
    entity = model(company_id=g.company_id, **{k: data[k] for k in allowed if k in data})
    Session.add(entity)
    Session.flush()
    audit("CREATE", model.__tablename__, entity.id)
    Session.commit()
    return entity.to_dict(), 201


def update_entity(model, entity_id, allowed):
    entity = Session.get(model, entity_id)
    if not entity or entity.company_id != g.company_id:
        return {"error": "Not found"}, 404
    data = request.get_json(silent=True) or {}
    for field in allowed:
        if field in data:
            setattr(entity, field, data[field])
    audit("UPDATE", model.__tablename__, entity.id)
    Session.commit()
    return entity.to_dict()


def delete_entity(model, entity_id):
    entity = Session.get(model, entity_id)
    if not entity or entity.company_id != g.company_id:
        return {"error": "Not found"}, 404
    audit("DELETE", model.__tablename__, entity.id)
    Session.delete(entity)
    Session.commit()
    return "", 204
