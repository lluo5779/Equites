from flask import Flask, make_response, request, jsonify

import random

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("somefile.jinja2")

if __name__ == '__main__':
    app.run(debug=True)