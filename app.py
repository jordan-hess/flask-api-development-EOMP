import sqlite3
import hmac
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_jwt import JWT, jwt_required
import smtplib
from flask_mail import Mail, Message

app = Flask(__name__)
CORS(app)


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


class Products(object):
    def __init__(self, product_id, name, price, category, description, product_image):
        self.product_id = product_id
        self.product_name = name
        self.product_price = price
        self.product_category = category
        self.product_description = description
        self.product_image = product_image


class MyDatabase(object):
    def __init__(self):
        self.conn = sqlite3.connect('product.db')
        self.cursor = self.conn.cursor()

    def adding_product(self, value):
        query = "INSERT INTO items (product_id, name, price, category, description," \
                "product_image) VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(query, value)

    def deleting_product(self, value):
        query = "DELETE FROM items WHERE product_id='" + value + "'"
        self.cursor.execute(query, value)

    def updating_product(self, value):
        query = "UPDATE items SET product_id=?, name=?, price=?, category=?, description=?," \
                "product_image=?"
        self.cursor.execute(query, value)

    def see_product(self):
        self.cursor.execute("SELECT * FROM items")
        return self.cursor.fetchall()

    def commit(self):
        self.conn.commit()


db = MyDatabase()


@app.route("/")
def index():
    return render_template("register.html")


def fetch_user():
    with sqlite3.connect('product.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


def register_table():
    connect = sqlite3.connect('product.db')

    connect.execute('CREATE TABLE IF NOT EXISTS user (userid INTEGER PRIMARY KEY AUTOINCREMENT,'
                    'name TEXT NOT NULL,'
                    'username TEXT NOT NULL,'
                    'password TEXT NOT NULL, '
                    'email TEXT NOT NULL)')
    print("User table was created successfully")
    connect.close()


register_table()


def product_table():
    connect = sqlite3.connect('product.db')

    connect.execute('CREATE TABLE IF NOT EXISTS items(product_id INTEGER PRIMARY KEY AUTOINCREMENT,'
                    'name TEXT NOT NULL,'
                    'price TEXT NOT NULL,'
                    'category TEXT NOT NULL, '
                    'product_image TEXT NOT NULL,'
                    'description TEXT NOT NULL)')
    print("Product table was created successfully")
    connect.close()


product_table()

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


app.config['SECRET_KEY'] = 'super-secret'
jwt = JWT(app, authenticate, identity)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'lifechoicesemail@gmail.com'
app.config['MAIL_PASSWORD'] = 'lifechoices'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


@app.route('/adding-users/', methods=['POST'])
def add_users():
    try:
        names = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # if password == password:
        with sqlite3.connect('product.db') as con:
            cursor = con.cursor()
            cursor.execute("INSERT INTO user (name, username, password, email) VALUES (?, ?, ?, ?)", (names, username, password, email))
            con.commit()
            msg = username + "was added to the database"
    except Exception as e:
        con.rollback()
        msg = "Error occured in insert" + str(e)
    finally:
        con.close()
    return jsonify(msg=msg)


@app.route('/login/', methods=['POST'])
def login_user():
    try:
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('product.db') as con:
            cursor = con.cursor()
            cursor.execute("SELECT * FROM user where username={} and password={}".format(username, password))
            con.commit()
            msg = username + " is logged in!"
    except Exception as e:
            con.rollback()
            msg = "Error occurred while trying to log in:" + str(e)
    finally:
        con.close()
    return jsonify(msg=msg)


@app.route('/view_pro/<name>/', methods=["GET"])
def view_profile(name):
    response = {}
    if request.method == "GET":
        with sqlite3.connect("product.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user WHERE name='" + name + "'")
            data = cursor.fetchall()
            response['message'] = "welcome back " + str(name)
            response['data'] = data
        return response


# create products
@app.route('/create-product/', methods=["POST"])
def create_product():
    response = {}

    if request.method == "POST":
        pro_nm = request.form['name']
        price = request.form['price']
        category = request.form['category']
        desc = request.form['description']

        with sqlite3.connect('product.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO items("
                           "name,"
                           "price,"
                           "category,"
                           "description) VALUES(?, ?, ?, ?)", (pro_nm, price, category, desc))
            conn.commit()
            response['hurray!'] = "product successfully created"
        return response


# Returns the data in a dict
def dict_factory(cursor, row):
    d = {}
    for i, x in enumerate(cursor.description):
        d[x[0]] = row[i]
    return d


@app.route('/select-product/', methods=['GET'])
def select_product():
    products = []
    try:
        with sqlite3.connect('product.db') as connect:
            connect.row_factory = dict_factory
            cursor = connect.cursor()
            cursor.execute("SELECT * FROM items")
            products = cursor.fetchall()
    except Exception as e:
        connect.rollback()
        print("There was an error fetching results from the database: " + str(e))
    finally:
        connect.close()
        return jsonify(products)


@app.route('/delete-products/<int:product_id>/')
def delete_product(product_id):
    response = {}
    try:
        with sqlite3.connect('product.db') as con:
            cur = con.cursor()
            cur.execute("DELETE FROM items WHERE product_id=" + str(product_id))
            con.commit()
            response["msg"] = "A record was deleted successfully from the database."
    except Exception as e:
        con.rollback()
        response["msg"] = "Error occurred when deleting a product in the database: " + str(e)
    finally:
        con.close()
        return jsonify(response)


@app.route('/update/<int:product_id>/', methods=["PUT"])
def updating_products(product_id):
    response = {}
    try:
        if request.method == "PUT":
            with sqlite3.connect('product.db') as conn:
                print(request.json)
                incoming_data = dict(request.json)
                put_data = {}

                if incoming_data.get("name") is not None:
                    put_data["name"] = incoming_data.get("name")

                    with sqlite3.connect('product.db') as connection:
                        cursor = connection.cursor()
                        cursor.execute("UPDATE items SET name =? WHERE product_id=?",
                                       (put_data["name"], product_id))
                        conn.commit()
                        response['message'] = "Update was successfully updated"

                elif incoming_data.get("price") is not None:
                    put_data["price"] = incoming_data.get("price")

                    with sqlite3.connect('product.db') as connection:
                        cursor = connection.cursor()
                        cursor.execute("UPDATE items SET price =? WHERE product_id=?",
                                       (put_data["price"], product_id))
                        conn.commit()
                        response['message'] = "Update was successfully"

                elif incoming_data.get("category") is not None:
                    put_data["category"] = incoming_data.get("category")

                    with sqlite3.connect('product.db') as connection:
                        cursor = connection.cursor()
                        cursor.execute("UPDATE items SET category =? WHERE product_id=?",
                                       (put_data["category"], product_id))
                        conn.commit()
                        response['message'] = "Update was successfully"

                elif incoming_data.get("description") is not None:
                    put_data["description"] = incoming_data.get("description")

                    with sqlite3.connect('product.db') as connection:
                        cursor = connection.cursor()
                        cursor.execute("UPDATE items SET description =? WHERE product_id=?",
                                       (put_data["description"], product_id))
                        conn.commit()
                        response['message'] = "Update was successfully"
    except Exception as e:
        conn.rollback()
        response["msg"] = "Error occurred when updating a product in the database: " + str(e)
    finally:
        conn.close()
        return jsonify(response)


@app.route('/sendemail/<email>', methods=['GET'])
def email_sending(email):
    mail = Mail(app)

    msg = Message('Hello Message', sender='lifechoicesemail@gmail.com', recipients=[email])
    msg.body = "This is my emails body"
    mail.send(msg)

    return "sent"


if __name__ == "__main__":
    app.debug = True
    app.run(port=5001)