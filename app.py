import sqlite3
import hmac
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_jwt import JWT, jwt_required

app = Flask(__name__)
CORS(app)


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_user():
    with sqlite3.connect('register.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


def register_table():
    connect = sqlite3.connect('register.db')

    connect.execute('CREATE TABLE IF NOT EXISTS user (userid INTEGER PRIMARY KEY AUTOINCREMENT,'
                    'name TEXT NOT NULL,'
                    'username TEXT NOT NULL,'
                    'password TEXT NOT NULL, '
                    'email TEXT NOT NULL)')
    print("Table was created successfully")
    connect.close()


register_table()
users = fetch_user()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


@app.route('/adding-users/', methods=['POST'])
@jwt_required
def add_users():
    try:
        names = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if password == password:
            with sqlite3.connect('register.db') as con:
                cursor = con.cursor()
                cursor.execute("INSERT INTO user (name, username, password, email) VALUES (?, ?, ?, ?)", (names, username, password, email))
                con.commit()
                msg = username + " was added as a registered user"
    except Exception as e:
            con.rollback()
            msg = "Error occurred in insert" + str(e)
    finally:
        con.close()
    return jsonify(msg=msg)


@app.route('/authorize/')
def check_info():
    username = request.form['username']
    password = request.form['password']

    with sqlite3.connect('register.db') as con:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        for data in users:
            if data[2] == username and data[3] == password:
                print("yay")
            else:
                print("no yay")


@app.route("/")
def index():
    return render_template("register.html")


app.config['SECRET_KEY'] = 'super-secret'
jwt = JWT(app, authenticate, identity)



if __name__ == '__main__':
    app.debug = True
    app.run(port=5001)


