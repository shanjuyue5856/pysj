from config import Config
from src.api.routes import api_bp
from flask import Flask, render_template

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.config.from_object(Config)

    @app.route("/")
    def index():
        return render_template("index.html")

    app.register_blueprint(api_bp, url_prefix="/api")
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)