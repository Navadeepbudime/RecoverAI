def create_app(config_object=None):
    from flask import Flask
    from flask_cors import CORS

    from .config import Config
    from .extensions import db
    from .routes.api import api_bp

    config_object = config_object or Config
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    db.init_app(app)

    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()

    return app
