from flask import Flask
from config import Config
from src.logger_config import configure_logger
from src.routes import main_blueprint

app = Flask(__name__)
app.config.from_object(Config)

# Configurar el logger
logger = configure_logger(app)

# Registrar blueprint de rutas
app.register_blueprint(main_blueprint)

if __name__ == '__main__':
    app.run(debug=True)
