import flask
from flask import Flask ,make_response, render_template,redirect, url_for
from flask_cors import CORS

ALLOWED_EXTENSIONS = {'py'}
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

    app.register_blueprint(rec.bp)

    if __name__ == '__init__':
        app.run(debug=True)

    @app.route('/')
    def index():
        return 'Index Page'


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
    return app


if __name__ == "__main__":
  app = app_config()
  create_app(app)
  app.run(debug=True)
