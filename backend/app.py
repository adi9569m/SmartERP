import os

from flask import Flask, request
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import IntegrityError

from config import Config
from database import Session, init_database
from routes import api
from schemas import ValidationError


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    init_database(app.config["DATABASE_URL"])
    JWTManager(app)
    app.register_blueprint(api)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    @app.after_request
    def cors(response):
        origin = request.headers.get("Origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Company-ID"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.before_request
    def options():
        if request.method == "OPTIONS":
            return "", 204

    @app.teardown_appcontext
    def cleanup(_error):
        Session.remove()

    @app.errorhandler(ValidationError)
    def validation_error(error):
        Session.rollback()
        return {"error": str(error)}, 400

    @app.errorhandler(IntegrityError)
    def integrity_error(_error):
        Session.rollback()
        return {"error": "Record conflicts with existing data or is still in use"}, 409

    @app.errorhandler(404)
    def not_found(_error):
        return {"error": "Not found"}, 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
