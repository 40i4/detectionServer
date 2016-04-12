import os
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from flask.ext.cors import CORS
import uuid
import json

from algo.algoReceipts import runz

from PIL import Image
from io import BytesIO
import base64


UPLOAD_FOLDER = "static"
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg']

app = Flask(__name__)
app.debug = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/test", methods=['POST', 'OPTIONS'])
def upload_file():

    print request.files
    if 'file' in request.files:
        img = request.files['file']

        name = uuid.uuid4().hex
        print name
        new_filename = "%s.%s" % (name, img.filename.split('.')[-1].lower())
        print new_filename
        save_path = os.path.join(BASE_PATH, UPLOAD_FOLDER, new_filename)
        img.save(save_path)
        print "save path: " + str(save_path)
        print "save path only static: " + str(save_path.split('/',-2)[0])

        # run algo
        file_processed, succeeded = runz(save_path)

        if not succeeded:
            return json.dumps({'error': "not succeeded"})
        new_filename = file_processed

        newFileNameWithoutPath = new_filename.split('/')[-1]
        print "aargh " + str(new_filename.split('/')[-1])
        return json.dumps({'img_path': "/static/%s" % newFileNameWithoutPath})

    else:
        print "no img in request.files"

    print request.data

    return 'nope'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
