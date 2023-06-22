from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy ( );

class ProductCategory ( database.Model ):
    id      = database.Column ( database.Integer, primary_key = True, autoincrement=True );
    product_id = database.Column ( database.Integer, database.ForeignKey ( "product.id" ), nullable = False );
    category_id = database.Column ( database.Integer, database.ForeignKey ( "category.id" ), nullable = False );

    def __init__ ( self, product_id, category_id ):
        self.product_id  = product_id
        self.category_id = category_id


class Product ( database.Model ):
    id       = database.Column ( database.Integer, primary_key = True, autoincrement=True);
    name    = database.Column ( database.String ( 256 ), nullable = False, unique = True );
    price = database.Column ( database.Integer, nullable = False );

    categories = database.relationship ( "Category", secondary = ProductCategory.__table__, back_populates = "products" );

    def __init__ ( self, name, price):
        self.name  = name
        self.price = price

    def __repr__(self):
        return str(self.id) + " " + self.name + " " + str(self.price)

class Category ( database.Model ):
    id   = database.Column ( database.Integer, primary_key = True, autoincrement=True );
    name = database.Column ( database.String ( 256 ), nullable = False );

    products = database.relationship ( "Product", secondary = ProductCategory.__table__, back_populates = "categories" );

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return str(self.id) + " " + self.name
