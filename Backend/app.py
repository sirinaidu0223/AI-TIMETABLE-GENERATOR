from flask import Flask, render_template
from flask_cors import CORS
from timetable_routes import bp
import os

base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')
CORS(app)
app.register_blueprint(bp)

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
