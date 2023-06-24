from flask import request, Response, jsonify, Flask, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity


from store.configuration import Configuration
from store.models import database, Product, Category, ProductCategory
from redis import Redis


import jwt





application = Flask ( __name__ )

application.config.from_object ( Configuration )
database.init_app ( application )

def banned_check ( function ):
    @jwt_required ( )
    def wrapper ( *args, **kwargs ):
        jwt = request.headers.get('Authorization').split()[1]
        if ( jwt not in deleted ):
            return function ( *args, **kwargs )
        else:
            return "Invalid token"

    return wrapper


@application.route ( "/update", methods=["POST"] )
@banned_check
def addProduct ( ):
    token = request.headers.get('Authorization')
    if (token == None):
        data = {
            "message": "Missing Authorization header"
        }
        response = jsonify(data)
        response.status_code = 400
        return response


    #citanje iz fajla iz requesta
    file = request.files["file"]
    if (file == None):
        data = {
            "message" : "Field file is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    content = file.stream.read().decode()

    cnt = 0
    products = []
    categoriesForProducts = []
    for line in content.split("\n"):
        data = line.split(",");

        if (len(data) != 3):
            data = {
                "message": f"Incorrect number of values on line {cnt}.”"
            }
            response = jsonify(data)
            response.status_code = 400
            return response



        categories = data[0].split("|")
        name = data[1]
        price = data[2]

        if (float(price) <= 0):
            data = {
                "message": f"Incorrect price on line {cnt}.”"
            }
            response = jsonify(data)
            response.status_code = 400
            return response

        cnt += 1

        product = Product.query.filter(Product.name == name).first()
        if (product != None):
            data = {
                "message": f"Product {name} already exists"
            }
            response = jsonify(data)
            response.status_code = 400
            return response

        newProduct = Product(name, float(price))
        products.append(newProduct)
        categoriesForProducts.append(categories)

    #if all products are new, we will commit all of them
    for product, categoriesForProduct in zip(products, categoriesForProducts):
        database.session.add(product)
        database.session.commit()

        for category in categoriesForProduct:
            tmpCat = Category.query.filter(Category.name == category).first()
            idCat = 0
            if (tmpCat == None):
                newCategory = Category(category)
                database.session.add(newCategory)
                database.session.commit()
                idCat = newCategory.id
            else:
                idCat = tmpCat.id

            productCategory = ProductCategory(product.id, idCat)
            database.session.add(productCategory)
            database.session.commit()



    response = make_response()
    response.status_code = 200
    return response




jwtManager = JWTManager ( application )

deleted = [ ]

from redis import Redis
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





@application.route("/ispisiProizvode", methods=["GET"])
def ispisiProducte():
    return jsonify(employees=[str(product) for product in Product.query.all()])
@application.route("/ispisiKategorije", methods=["GET"])
def ispisiRole():
    return jsonify(employees=[str(role) for role in Category.query.all()])

from threading import Thread
if ( __name__ == "__main__" ):
    with Redis ( host = "redis", port = 6379, db = 0 ) as redis:
        list = redis.lrange ( "banned", 0, -1 )
        banned = [item.decode ( ) for item in list]

    Thread ( target = listener ).start ( )


    application.run ( debug = True, host="0.0.0.0", port=5003 )