from markupsafe import escape
from flask import Flask ,make_response, render_template,redirect, url_for, flash
from flask import request
from werkzeug.utils import secure_filename
from jinja2 import Environment, PackageLoader, select_autoescape
from flask_cors import CORS
import os
'''
env = Environment(
    loader=PackageLoader("yourapp"),
    autoescape=select_autoescape())
'''

ALLOWED_EXTENSIONS = {'py'}
UPLOAD_FOLDER = '/Users/nagalikiths/Desktop/Easy Grade/easygrade-flask-server/src/static/upload-file'


def app_config():
    app = Flask(__name__,instance_relative_config=True)
    # The current Limit is 1MB
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1000 * 1000
    app.config['SECRET_KEY'] = 'Test'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/flasksql'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    return app

def create_app(test_config=None):

    app = app_config()
    CORS(app)
    if __name__ == '__init__':
        app.run(debug=True)

    @app.route('/')
    def index():
        return 'Index Page'

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'POST':
            print('Upload Started')
            print(request)
            # check if the post request has the file part
            if 'file' not in request.files:
                print('No file part')
                return redirect(request.url)
            submission = request.files['file']

            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            
            if submission.filename == '':
                print('No selected file')
                return redirect(request.url)
            
            if submission and allowed_file(submission.filename):
                filename = secure_filename(submission.filename)
                submission.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print("I am here")
                return redirect(url_for('upload_file', name=filename))
        return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form method=post enctype=multipart/form-data>
        <input type=file name=file>
        <input type=submit value=Upload>
        </form>
        '''

    # User Stuff
    @app.route("/me")
    def me_api():
        user = get_current_user()
        return {
            "username": user.username,
            "theme": user.theme,
            "image": url_for("user_image", filename=user.image),
        }

    #Errors
    @app.errorhandler(404)
    def not_found(error):
        resp = make_response(render_template('error.html'), 404)
        resp.headers['X-Something'] = 'A value'
        return resp
    app.run(ssl_context="adhoc")
    return app

# Upload a File
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS