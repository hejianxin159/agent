# -*- coding: utf-8 -*-
import time

import flask

app = flask.Flask(__name__)


@app.route('/')
def index():
    return "Hello"


app.run(host="0.0.0.0", port=55535)
