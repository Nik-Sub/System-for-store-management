from flask import request, Response, jsonify, Flask, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy

from store.configuration import Configuration
from store.models import database, Product, Category, ProductCategory, OrderOfCustomer, ProductOrder
from redis import Redis
from functools import wraps

import jwt





application = Flask ( __name__ )
application.config.from_object ( Configuration )
database.init_app ( application )


jwtManager = JWTManager ( application )

deleted = [ ]

def listener ( ):
    with Redis ( host = "redis", port = 6379, db = 0 ) as redis:
        pubsub = redis.pubsub ( )
        pubsub.subscribe ( "channel" )

        first = True
        for message in pubsub.listen ( ):
            if ( first ):
                first = False
                continue

            token = message["data"].decode ( )
            deleted.append ( token )


def banned_check ( fn ):
    @wraps(fn)  # Preserve the original function's name and attributes
    def wrapper ( *args, **kwargs ):
        token = request.headers.get('Authorization')
        if (token == None):
            data = {
                "message": "Missing Authorization header"
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        jwt = request.headers.get('Authorization').split()[1]
        if ( jwt not in deleted ):
            return fn ( *args, **kwargs )
        else:
            return "Invalid token"

    return wrapper



@application.route("/ispisiNarudzbine", methods=["GET"])
def ispisiProducte():
    return jsonify(employees=[str(product) for product in OrderOfCustomer.query.all()])
@application.route("/ispisiSadrzajNarudzbine", methods=["GET"])
def ispisiRole():
    return jsonify(employees=[str(role) for role in ProductOrder.query.all()])

@application.route ( "/search", methods=["get"] )
@banned_check
def searchProducts ( ):
    productName = request.args.get('name')
    categoryName = request.args.get('category')

    categories = Category.query.filter(Category.name.like(f'%{categoryName}%')).all()
    categoriesWithProduct = [];
    products = []

    for category in categories:
        for product in category.products:
            if (product.name.find(productName) != -1):
                if (category.name not in categoriesWithProduct):
                    categoriesWithProduct.append(category.name)
                if (product not in products):
                    products.append(product)

    #this will be return for products
    returnForProducts = []
    for product in products:
        dictProd = {
            "categories" : [category.name for category in product.categories],
            "id" : product.id,
            "name" : product.name,
            "price" : product.price
        }
        returnForProducts.append(dictProd)

    data = {
        "categories" : categoriesWithProduct,
        "products" : returnForProducts
    }
    response = jsonify(data)
    response.status_code = 200
    return response

@application.route ( "/order", methods=["post"] )
@banned_check
def makeOrder ( ):
    requests = request.json['requests']

    if (requests == None):
        data = {
            "message" : "Field requests is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    token = request.headers.get('Authorization').split()[1]
    decoded_token = jwt.decode(token, Configuration.JWT_SECRET_KEY, algorithms=["HS256"])
    userId = decoded_token.get("id")
    userEmail = decoded_token.get("email")
    productsInOrder = []
    newOrder = OrderOfCustomer(0, "cekanje", userId, userEmail);
    cnt = 0
    for req in requests:
        if (req["id"] == None):
            data = {
                "message": f"Product id is missing for request number {cnt}."
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        if (req["quantity"] == None):
            data = {
                "message": f"Product quantity is missing for request number {cnt}."
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        if (req["id"] <= 0):
            data = {
                "message": f"Invalid product id for request number {cnt}."
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        if (req["quantity"] <= 0):
            data = {
                "message": f"Invalid product quantity for request number {cnt}."
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        if (Product.query.filter(Product.id == req["id"]).first() == None):
            data = {
                "message": f"Invalid product for request number {cnt}."
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        newProductOrder = ProductOrder(req["id"], 0, req["quantity"])
        productsInOrder.append(newProductOrder)
        cnt += 1
        newOrder.price = newOrder.price + Product.query.filter(Product.id == req["id"]).first().price * req["quantity"]

    database.session.add(newOrder)
    database.session.commit()

    for productInOrder in productsInOrder:
        productInOrder.orderId = newOrder.id
        database.session.add(productInOrder)
        database.session.commit()

    data = {
        "id" : newOrder.id
    }
    response = jsonify(data)
    response.status_code = 200
    return response


@application.route ( "/status", methods=["get"] )
@banned_check
def seeYourOrder():
    token = request.headers.get('Authorization').split()[1]
    decoded_token = jwt.decode(token, Configuration.JWT_SECRET_KEY, algorithms=["HS256"])

    userId = decoded_token.get("id")

    orders = OrderOfCustomer.query.filter(OrderOfCustomer.userId == userId).all()

    ordersForData = []

    for order in orders:
        products = order.products
        productsInOrder = []
        for product in products:
            quantity = ProductOrder.query.filter(ProductOrder.orderId == order.id,
                                                 ProductOrder.productId == product.id).first().quantity
            dictProd = {
                "categories": [category.name for category in product.categories],
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "quantity": quantity
            }

            productsInOrder.append(dictProd)
        ordersForData.append({
            "products" : productsInOrder,
            "price" : order.price,
            "status": order.status,
            "timestamp":order.createdAt.strftime("%Y-%m-%dT%H:%M:%SZ")
        })

    data = {
        "orders" : ordersForData
    }
    response = jsonify(data)
    response.status_code = 200
    return response


@application.route ( "/delivered", methods=["post"] )
@banned_check
def collectOrder():
    idOrder = request.json['id']

    if (idOrder == None):
        data = {
            "message" : "Missing order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (idOrder <= 0 or OrderOfCustomer.query.filter(OrderOfCustomer.id == idOrder).first() == None or OrderOfCustomer.query.filter(OrderOfCustomer.status == "naPutu", OrderOfCustomer.id == idOrder).first() == None):
        data = {
            "message" : "Invalid order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    order = OrderOfCustomer.query.get(idOrder)
    order.status = "izvrsena"
    database.session.commit()

    response = make_response()
    response.status_code = 200
    return response



from threading import Thread
if ( __name__ == "__main__" ):
    with Redis ( host = "redis", port = 6379, db = 0 ) as redis:
        list = redis.lrange ( "banned", 0, -1 )
        banned = [item.decode ( ) for item in list]

    Thread ( target = listener ).start ( )


    application.run ( debug = True, host="0.0.0.0", port=5002 )