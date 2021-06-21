
import json
import os
import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path

import filelock
from flask import Flask, jsonify, redirect, request, send_from_directory

abspath = Path(os.path.abspath(__file__)).parents[1]


def _pyxell_command(*args):
    return ['python', str(abspath/'pyxell.py'), *args]


CODE_LENGTH_LIMIT = 5000
EXECUTION_TIME_LIMIT = 2

TMP_PATH = os.path.join(tempfile.gettempdir(), 'pyxell')
os.makedirs(TMP_PATH, mode=0o755, exist_ok=True)

subprocess.run(_pyxell_command('--precompile-header'), stdout=subprocess.PIPE)

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


@app.route('/run/', methods=['POST'])
def run():
    # https://stackoverflow.com/a/26654607
    # https://help.pythonanywhere.com/pages/WebAppClientIPAddresses/
    ip_address = request.headers.get('X-Real-IP', request.remote_addr)

    try:
        with filelock.FileLock(f'{ip_address}.lock', timeout=0):
            data = json.loads(request.data)
            code = data['code']
            opt_level = 2 if data.get('optimization') else 0

            if len(code) > CODE_LENGTH_LIMIT:
                return jsonify({'error': f"Code must not be longer than {CODE_LENGTH_LIMIT} characters."})

            with tempfile.NamedTemporaryFile(dir=TMP_PATH, suffix='.px', mode='w', delete=False) as file:
                file.write(code)

            process = subprocess.run(_pyxell_command(file.name, f'-O{opt_level}', f'-l{EXECUTION_TIME_LIMIT}'), input=data.get('input', ''), stdout=subprocess.PIPE, text=True)

            for ext in ['.cpp', '.exe']:
                with suppress(OSError):
                    os.remove(file.name.replace('.px', ext))

            if process.returncode == 0:
                result = {'output': process.stdout}
            elif process.returncode == 2:
                result = {'error': f"Program must not run for longer than {EXECUTION_TIME_LIMIT} seconds."}
            else:
                result = {'error': process.stdout}

            return jsonify(result)

    except filelock.Timeout:
        return jsonify({'error': "You cannot run several programs simultaneously."})


if __name__ == '__main__':
    app.run(debug=True)
