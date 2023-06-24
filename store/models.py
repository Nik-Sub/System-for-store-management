from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from datetime import datetime
database = SQLAlchemy ( );

class ProductCategory ( database.Model ):
    id      = database.Column ( database.Integer, primary_key = True, autoincrement=True );
    productId = database.Column ( database.Integer, database.ForeignKey ( "product.id" ), nullable = False );
    categoryId = database.Column ( database.Integer, database.ForeignKey ( "category.id" ), nullable = False );

    def __init__ ( self, product_id, category_id ):
        self.productId  = product_id
        self.categoryId = category_id

class ProductOrder ( database.Model ):
    id      = database.Column ( database.Integer, primary_key = True, autoincrement=True );
    productId = database.Column ( database.Integer, database.ForeignKey ( "product.id" ), nullable = False );
    orderId = database.Column ( database.Integer, database.ForeignKey ( "order_of_customer.id" ), nullable = False );
    quantity = database.Column(database.Integer, nullable=False);
    def __init__ ( self, productId, orderId, quantity ):
        self.productId  = productId
        self.orderId = orderId
        self.quantity = quantity

class Product ( database.Model ):
    id       = database.Column ( database.Integer, primary_key = True, autoincrement=True);
    name    = database.Column ( database.String ( 256 ), nullable = False, unique = True );
    price = database.Column ( database.Float, nullable = False );

    categories = database.relationship ( "Category", secondary = ProductCategory.__table__, back_populates = "products" );
    orders = database.relationship("OrderOfCustomer", secondary=ProductOrder.__table__, back_populates="products");

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




class OrderOfCustomer (database.Model):
    id = database.Column(database.Integer, primary_key=True, autoincrement=True);
    price = database.Column(database.Float, nullable=False);
    status = database.Column ( database.String ( 256 ), nullable = False );
    createdAt = database.Column(database.DateTime)
    userId = database.Column ( database.Integer, database.ForeignKey ( "product.id" ), nullable = False );
    userEmail = database.Column ( database.String ( 256 ), nullable = False );
    products = database.relationship ( "Product", secondary = ProductOrder.__table__, back_populates = "orders" );

    def __init__ ( self, price, status, userId, email):
        self.price  = price
        self.status = status
        self.createdAt = datetime.utcnow()
        self.userId = userId
        self.userEmail = email

    def __repr__(self):
        return str(self.id) + " " + str(self.price) + " " + self.status + " " + self.createdAt.strftime("%Y-%m-%dT%H:%M:%SZ") + " " + str(self.userId) + self.userEmail

