import sqlite3
import hmac
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_jwt import JWT, jwt_required
from flask_mail import Mail, Message
import datetime

app = Flask(__name__)
CORS(app)

# fetching the data from my database
def fetch_user():
    with sqlite3.connect('product.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[2], data[3]))
    return new_data


# DOM manipulation for users
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# User authentication
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

# DOM manipulation for products
class Products(object):
    def __init__(self, product_id, name, price, category, description):
        self.product_id = product_id
        self.product_name = name
        self.product_price = price
        self.product_category = category
        self.product_description = description

# DOM manipulation for database
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


# made the registration page the index of the project
@app.route("/")
def index():
    return render_template("register.html")


# creating my register table
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


# creating my products table
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

# registration page
@app.route('/adding-users/', methods=['POST'])
def add_users():
    try:
        names = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        with sqlite3.connect('product.db') as con:
            cursor = con.cursor()
            cursor.execute("INSERT INTO user (name, username, password, email) VALUES (?, ?, ?, ?)", (names, username, password, email))
            con.commit()
            msg = username + " was added to the database"
    except Exception as e:
        con.rollback()
        msg = "Error occurred in adding user to the database" + str(e)
    finally:
        con.close()
    return jsonify(msg=msg)


# login page
@app.route('/login/', methods=['POST'])
def login_user():
    try:
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('product.db') as con:
            cursor = con.cursor()
            cursor.execute("SELECT * FROM user where username=? and password=?", (username, password))
            con.commit()
            msg = username + " is logged in!"
    except Exception as e:
            con.rollback()
            msg = "Error occurred while trying to log in:" + str(e)
    finally:
        con.close()
    return jsonify(msg=msg)


# this code allows the user to view their profile
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


# creating products page
@app.route('/create-product/', methods=["POST"])
@jwt_required()
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

# this code allows you to view the products
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

# this code allows you to delete products using its id
@app.route('/delete-products/<int:product_id>/')
# @jwt_required()
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


# this code allows you to edit elements in the product
@app.route('/update/<int:product_id>/', methods=["PUT"])
# @jwt_required()
def updating_products(product_id):
    response = {}
    try:
        if request.method == "PUT":
            with sqlite3.connect('product.db') as conn:
                print(request.json)
                incoming_data = dict(request.json)
                put_data = {}

                # editing name of the product
                if incoming_data.get("name") is not None:
                    put_data["name"] = incoming_data.get("name")

                    with sqlite3.connect('product.db') as connection:
                        cursor = connection.cursor()
                        cursor.execute("UPDATE items SET name =? WHERE product_id=?",
                                       (put_data["name"], product_id))
                        conn.commit()
                        response['message'] = "Update was successfully updated"

                # editing the price of the product
                elif incoming_data.get("price") is not None:
                    put_data["price"] = incoming_data.get("price")

                    with sqlite3.connect('product.db') as connection:
                        cursor = connection.cursor()
                        cursor.execute("UPDATE items SET price =? WHERE product_id=?",
                                       (put_data["price"], product_id))
                        conn.commit()
                        response['message'] = "Update was successfully"

                # editing the products category
                elif incoming_data.get("category") is not None:
                    put_data["category"] = incoming_data.get("category")

                    with sqlite3.connect('product.db') as connection:
                        cursor = connection.cursor()
                        cursor.execute("UPDATE items SET category =? WHERE product_id=?",
                                       (put_data["category"], product_id))
                        conn.commit()
                        response['message'] = "Update was successfully"

                # editing the description of the product
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


# configuration of sending emails
app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(seconds=4000)
CORS(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "huntermoonspear@gmail.com"
app.config['MAIL_PASSWORD'] = "dianadragonheart"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

jwt = JWT(app, authenticate, identity)


# code allows you to send emails
@app.route('/send_mail/<email>', methods=['GET'])
@jwt_required()
def email_sending(email):
    mail = Mail(app)

    msg = Message('Hello Message', sender='lifechoicesemail@gmail.com', recipients=[email])
    msg.body = "This is my emails body"
    mail.send(msg)

    return "sent"


if __name__ == "__main__":
    app.debug = True
    app.run(port=5001)
