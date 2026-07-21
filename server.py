import os
import sys
import logging
import subprocess
from flask import Flask, request, send_from_directory, send_file

# set the project root directory as the static folder, you can set others.
app = Flask(__name__)

@app.route('/screenshot')
def screenshot():
    subprocess.run('XAUTHORITY=`find /tmp -name Xauthority` xwd -root -silent | convert xwd:- png:/tmp/screenshot.png', shell=True)
    return send_file('/tmp/screenshot.png')

@app.route('/<path:filename>', methods=['GET', 'DELETE'])
def path_handler(filename):
    if request.method == 'GET':
        return send_from_directory('/downloads', filename)
    elif request.method == 'DELETE':
        os.unlink(os.path.join('/downloads', filename))
        return 'OK'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(sys.argv[1]))
