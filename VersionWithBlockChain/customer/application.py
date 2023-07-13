import json
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


def isDigit(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


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
        if (roles[0] != "customer"):
            data = {
                "msg": "Missing Authorization Header"
            }
            response = jsonify(data)
            response.status_code = 401
            return response

        return fn ( *args, **kwargs )


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
    if (productName == None):
        productName = ""
    categoryName = request.args.get('category')
    if (categoryName == None):
        categoryName = ""

    if (categoryName != ""):
        categories = Category.query.filter(Category.name.like(f'%{categoryName}%')).all()
    else:
        categories = Category.query.all()
    categoriesWithProduct = []
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
    requests = request.json.get('requests', None)

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
    newOrder = OrderOfCustomer(0, "CREATED", userId, userEmail);
    cnt = 0
    for req in requests:
        if (req.get("id", None) == None):
            data = {
                "message": f"Product id is missing for request number {cnt}."
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        if (req.get("quantity", None) == None):
            data = {
                "message": f"Product quantity is missing for request number {cnt}."
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        if (not isDigit(req.get("id")) or int(req.get("id") <= 0)):
            data = {
                "message": f"Invalid product id for request number {cnt}."
            }
            response = jsonify(data)
            response.status_code = 400
            return response
        if (not isDigit(req.get("quantity")) or int(req.get("quantity")) <= 0):
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

    address = request.json.get('address', None)

    if (address == None or len(address) == 0):
        data = {
            "message": "Field address is missing."
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



    database.session.add(newOrder)
    database.session.commit()

    for productInOrder in productsInOrder:
        productInOrder.orderId = newOrder.id
        database.session.add(productInOrder)
        database.session.commit()

    #making contract

    def read_file(path):
        with open(path, "r") as file:
            return file.read()

    bytecode = read_file("./solidity/output/Naplata.bin")
    abi = read_file("./solidity/output/Naplata.abi")

    contract = web3.eth.contract(bytecode=bytecode, abi=abi)



    transaction_hash = contract.constructor(address, web3.to_int(int(newOrder.price))).transact({
        "from": web3.eth.accounts[0]
    })

    # i can get contract address from receipt
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)

    #contract = web3.eth.contract(address=receipt.contractAddress, abi=abi)

    contract = Contract(address=receipt.contractAddress, abi=abi, idOrder=newOrder.id)
    database.session.add(contract)
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
                #"id": product.id,
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
    idOrder = request.json.get('id', None)

    if (idOrder == None):
        data = {
            "message" : "Missing order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if ( not isDigit(idOrder) or idOrder <= 0 or OrderOfCustomer.query.filter(OrderOfCustomer.id == idOrder).first() == None or OrderOfCustomer.query.filter(OrderOfCustomer.status == "PENDING", OrderOfCustomer.id == idOrder).first() == None):
        data = {
            "message" : "Invalid order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    keys = request.json.get('keys', None)
    if (keys == None or len(keys) == 0):
        data = {
            "message": "Missing keys."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    passphrase = request.json.get('passphrase', None)

    if (passphrase == None or len(passphrase) == 0):
        data = {
            "message": "Missing passphrase."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    keys = keys.replace("'", "\"")

    keys = json.loads(keys)
    try:
        private_key = Account.decrypt(keys, passphrase).hex()
    except ValueError as e:
        data = {
            "message": "Invalid credentials."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    web3 = Web3(HTTPProvider(f"http://{GAN}:8545"))

    address = web3.to_checksum_address(keys["address"])

    contractRow = Contract.query.filter(Contract.idOrder == idOrder).first()

    contractAddress = contractRow.address
    contractAbi = contractRow.abi

    contract = web3.eth.contract(address=contractAddress, abi=contractAbi)

    #order = OrderOfCustomer.query.filter(OrderOfCustomer.id == idOrder).first()
    try:
        transaction = contract.functions.transferMoneyToOwnerAndCourier().build_transaction({
            "from": address,
            "nonce": web3.eth.get_transaction_count(address),
            "gasPrice": 21000
        })

        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
        transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
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
    order.status = "COMPLETE"
    database.session.commit()

    response = make_response()
    response.status_code = 200
    return response


@application.route ( "/pay", methods=["post"] )
@banned_check
def payOrder():
    idOrder = request.json.get('id', None)

    if (idOrder == None):
        data = {
            "message": "Missing order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (not isDigit(idOrder) or idOrder <= 0 or OrderOfCustomer.query.filter(
            OrderOfCustomer.id == idOrder).first() == None):
        data = {
            "message": "Invalid order id."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    keys = request.json.get('keys', None)
    if (keys == None or len(keys) == 0):
        data = {
            "message": "Missing keys."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    passphrase = request.json.get('passphrase', None)

    if ( passphrase == None or len(passphrase) == 0):
        data = {
            "message": "Missing passphrase."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    keys = json.loads(keys)

    try:
        private_key = Account.decrypt(keys, passphrase).hex()
    except ValueError as e:
        data = {
            "message": "Invalid credentials."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    web3 = Web3(HTTPProvider(f"http://{GAN}:8545"))

    address = web3.to_checksum_address(keys["address"])



    contractRow = Contract.query.filter(Contract.idOrder == idOrder).first()

    contractAddress = contractRow.address
    contractAbi = contractRow.abi

    contract = web3.eth.contract ( address = contractAddress, abi = contractAbi )



    order = OrderOfCustomer.query.filter(OrderOfCustomer.id == idOrder).first()

    balance = web3.eth.get_balance(address)
    if balance < web3.to_int(int(order.price)):
        data = {
            "message": "Insufficient funds."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    try:
        transaction = contract.functions.payCustomer().build_transaction({
            "from": address,
            "value" : web3.to_int(int(order.price)),
            "nonce": web3.eth.get_transaction_count(address),
            "gasPrice": 21000
        })

        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
        transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
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

    response = make_response()
    response.status_code = 200
    return response


if ( __name__ == "__main__" ):



    application.run ( debug = True, host="0.0.0.0", port=5002 )