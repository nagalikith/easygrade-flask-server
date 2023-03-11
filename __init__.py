from markupsafe import escape
from flask import Flask
from flask import request
from werkzeug.utils import secure_filename
from flask import abort, redirect, url_for, flash
from flask import make_response
from flask import render_template
from jinja2 import Environment, PackageLoader, select_autoescape
import os
'''
env = Environment(
    loader=PackageLoader("yourapp"),
    autoescape=select_autoescape())
'''

ALLOWED_EXTENSIONS = {'py', "svg"}
UPLOAD_FOLDER = '.'


def app_config():
    app = Flask(__name__,instance_relative_config=True)
    # The current Limit is 1MB
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
    app.config['SECRET_KEY'] = 'Test'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/flasksql'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    return app

def create_app(app=None, test_config=None): 

    if (app == None):
      app = app_config()
    if __name__ == '__init__':
        app.run(debug=True)

    @app.route('/')
    def index():
        return 'Index Page'

    @app.route('/hello')
    def hello():
        app.logger.debug('A value for debugging')
        app.logger.warning('A warning occurred (%d apples)', 42)
        return 'Hello, World'

    @app.route("/<name>")
    def name(name):
        return f"Hello, {escape(name)}!"

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'POST':
            print("Reuqest : {}".format(request))
            print('Upload Started')
            # check if the post request has the file part
            if 'file' not in request.files:
                print('No file part')
                return redirect(request.url)
            file = request.files['file']
            print("file : {}".format(file))
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                print('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print("I was successfull")
                return {"Upload Status": "Successfull"}
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

    @app.route("/users")
    def users_api():
        users = get_all_users()
        return [user.to_json() for user in users]

    #Errors
    @app.errorhandler(404)
    def not_found(error):
        resp = make_response(render_template('error.html'), 404)
        resp.headers['X-Something'] = 'A value'
        return resp
    
    return app

# Upload a File
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == "__main__":
  app = app_config()
  create_app(app)
  app.run(debug=True)
