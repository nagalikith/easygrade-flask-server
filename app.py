import flask
import json
import import_helper as ih

import route_assn_rel as rar
import route_exec_code as rec
import route_user_rel as rur
import route_sec_rel as rsr

def create_app():
  app = flask.Flask(__name__)
  app.secret_key = "7A{ghze1Tuse$r>l2Cynvpc%@9mjoI9&lQ*d>sxbxbdgPbbxPF<hiWlK\\1Za<,r%"
  app.register_blueprint(rec.bp)
  app.register_blueprint(rar.bp)
  app.register_blueprint(rur.bp)
  app.register_blueprint(rsr.bp)

  @app.route("/")
  @ih.handle_login
  def get_home_page(userid):
    
    pg_info = {}
    ih.libs["form_helper"].add_codes(flask.session, pg_info)

    link_names = ["My Account", "Sections"]
    links_flask = ["user_rel.get_account_page", "sec_rel.get_section_list_page"]

    if (ih.libs["user_auth"].is_admin(userid)):
      link_names.append("Users")
      links_flask.append("user_rel.get_users_page")
    
    pg_info["links"] = []

    for i in range(len(link_names)):
      name = link_names[i]
      src = flask.url_for(links_flask[i])
      pg_info["links"].append(
        {"name": name, "src": src}
      )
    return flask.render_template("home.html", pg_info=json.dumps(pg_info))

  return app

if __name__ == "__main__":
  app = create_app()
  app.run(host='0.0.0.0',port=5050, debug=True)
