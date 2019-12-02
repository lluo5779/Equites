from flask import render_template

import server

app = server.create_app().app

@app.errorhandler(404)
def page_not_found(error):
   return render_template('404.jinja2', title = '404'), 404

if __name__ == "__main__":
    app.run()
