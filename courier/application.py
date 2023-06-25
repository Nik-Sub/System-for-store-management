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


@application.route ( "/orders_to_deliver", methods=["get"] )
@banned_check
def ordersForDelivery():

    undeliveredOrders = OrderOfCustomer.query.filter(OrderOfCustomer.status == "cekanje").all()

    orders = []
    for undOrder in undeliveredOrders:
        orders.append({
            "id" : undOrder.id,
            "email" : undOrder.userEmail
        })

    data = {
        "orders": orders
    }
    response = jsonify(data)
    response.status_code = 200
    return response

@application.route ( "/pick_up_order", methods=["post"] )
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

    if (idOrder <= 0 or OrderOfCustomer.query.filter(OrderOfCustomer.id == idOrder).first() == None or OrderOfCustomer.query.filter(OrderOfCustomer.status == "cekanje", OrderOfCustomer.id == idOrder).first() == None):
        data = {
            "message" : "Invalid order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    order = OrderOfCustomer.query.get(idOrder)
    order.status = "naPutu"
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


    application.run ( debug = True, host="0.0.0.0", port=5003 )