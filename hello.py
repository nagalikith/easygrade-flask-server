from markupsafe import escape
from flask import Flask
from flask import request
from werkzeug.utils import secure_filename
from flask import abort, redirect, url_for, flash
from flask import make_response
from flask import render_template
from jinja2 import Environment, PackageLoader, select_autoescape
'''
env = Environment(
    loader=PackageLoader("yourapp"),
    autoescape=select_autoescape())
'''

app = Flask(__name__)
# The current Limit is 1MB
app.config['MAX_CONTENT_LENGTH'] = 1 * 1000 * 1000
app.config['SECRET_KEY'] = 'Test'

ALLOWED_EXTENSIONS = {'py'}
UPLOAD_FOLDER = '/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if __name__ == '__hello__':
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

# Upload a File
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        flash('Upload Started')
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('download_file', name=filename))
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