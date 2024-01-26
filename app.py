from flask import Flask

from application.models import *


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///database.sqlite3'
app.secret_key = 'super secret key'
db.init_app(app)
app.app_context().push()

with app.app_context():
    db.create_all()

from application.controllers import *


if __name__ == "__main__":
    app.run(debug = True)