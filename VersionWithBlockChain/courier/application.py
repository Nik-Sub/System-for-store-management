import os

from flask import request, Response, jsonify, Flask, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from web3 import Web3
from web3 import HTTPProvider
from web3 import Account
from web3.exceptions import ContractLogicError
from web3.exceptions import ContractCustomError

from store.configuration import Configuration
from store.models import database, Product, Category, ProductCategory, OrderOfCustomer, ProductOrder, Contract

from functools import wraps

import jwt
GAN = os.environ["GAN"];




application = Flask ( __name__ )
application.config.from_object ( Configuration )
database.init_app ( application )


jwtManager = JWTManager ( application )




def banned_check ( fn ):
    @wraps(fn)  # Preserve the original function's name and attributes
    def wrapper ( *args, **kwargs ):
        if 'Authorization' not in request.headers:
            data = {
                "msg": "Missing Authorization Header"
            }
            response = jsonify(data)
            response.status_code = 401
            return response
        token = request.headers.get('Authorization').split()[1]
        decoded_token = jwt.decode(token, Configuration.JWT_SECRET_KEY, algorithms=["HS256"])
        roles = decoded_token.get("roles")
        if (roles[0] != "courier"):
            data = {
                "msg": "Missing Authorization Header"
            }
            response = jsonify(data)
            response.status_code = 401
            return response
        return fn ( *args, **kwargs )


    return wrapper


@application.route ( "/orders_to_deliver", methods=["get"] )
@banned_check
def ordersForDelivery():

    undeliveredOrders = OrderOfCustomer.query.filter(OrderOfCustomer.status == "CREATED").all()

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


def isDigit(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

@application.route ( "/pick_up_order", methods=["post"] )
@banned_check
def collectOrder():
    idOrder = request.json.get('id', None)

    if (idOrder == None):
        data = {
            "message" : "Missing order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (not isDigit(idOrder) or idOrder <= 0 or OrderOfCustomer.query.filter(OrderOfCustomer.id == idOrder).first() == None or OrderOfCustomer.query.filter(OrderOfCustomer.status == "CREATED", OrderOfCustomer.id == idOrder).first() == None):
        data = {
            "message" : "Invalid order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    address = request.json.get('address', None)

    if (address == None or len(address) == 0):
        data = {
            "message": "Missing address."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    # Initialize a Web3 instance
    web3 = Web3(HTTPProvider(f"http://{GAN}:8545"))

    try:

        address = web3.to_checksum_address(address)

    except ValueError:
        data = {
            "message": "Invalid address."
        }
        response = jsonify(data)
        response.status_code = 400
        return response


    contractRow = Contract.query.filter(Contract.idOrder == idOrder).first()

    contractAddress = contractRow.address
    contractAbi = contractRow.abi

    contract = web3.eth.contract(address=contractAddress, abi=contractAbi)


    try:
        contract.functions.pickUpOrder(address).transact({
            "from": web3.eth.accounts[0]
        })
    except ContractLogicError as error:
        error_message = str(error)
        start_index = error_message.find("revert ") + len("revert ")
        transferMessage = error_message[start_index:]
        data = {
            "message": transferMessage
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    order = OrderOfCustomer.query.get(idOrder)
    order.status = "PENDING"
    database.session.commit()

    response = make_response()
    response.status_code = 200
    return response



if ( __name__ == "__main__" ):


    application.run ( debug = True, host="0.0.0.0", port=5003 )