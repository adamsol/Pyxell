
import json
import os
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_from_directory


CODE_LENGTH_LIMIT = 5000

TMP_PATH = os.path.join(tempfile.gettempdir(), 'pyxell')
os.makedirs(TMP_PATH, mode=0o755, exist_ok=True)

app = Flask(__name__)


@app.route('/')
def index():
    return redirect('/docs/')


@app.route('/docs/', defaults={'path': 'index.html'})
@app.route('/docs/<path:path>')
def serve_static(path):
    return send_from_directory('dist/', path)


@app.errorhandler(404)
def page_not_found(e):
    return serve_static('404.html'), 404


@app.route('/transpile/', methods=['POST'])
def run():
    data = json.loads(request.data)
    code = data['code']

    if len(code) > CODE_LENGTH_LIMIT:
        return jsonify({'error': f"Code must not be longer than {CODE_LENGTH_LIMIT} characters."})

    with tempfile.NamedTemporaryFile(dir=TMP_PATH, suffix='.px', mode='w', delete=False) as file:
        file.write(code)

    try:
        subprocess.check_output(['python', '../pyxell.py', file.name, '--standalone-cpp'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        result = {'error': e.output.decode()}
    else:
        cpp_filename = file.name.replace('.px', '.cpp')
        result = {'cpp_code': Path(cpp_filename).read_text()}
        os.remove(cpp_filename)

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
