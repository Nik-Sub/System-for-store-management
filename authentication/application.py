from flask import request, Response, jsonify, Flask, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy

from configuration import Configuration
from models import User, database, Role, UserRole
from redis import Redis

import jwt





application = Flask ( __name__ )


#for authenticationDB
application.config.from_object ( Configuration )
database.init_app ( application )

@application.route ( "/register_customer", methods=["POST"] )
def registerCustomer ( ):

    email = request.json["email"]
    password = request.json["password"]
    forename = request.json["forename"]
    surname = request.json["surname"]

    user = User.query.filter(User.email == email).first()

    if (user != None):
        data = {
            "message" : "Email already exists"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (len(email) == 0):
        data = {
            "message": "Field email is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (len(password) == 0):
        data = {
            "message": "Field password is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (len(forename) == 0):
        data = {
            "message": "Field forename is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (len(surname) == 0):
        data = {
            "message": "Field surname is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    #check
    emailBad = len(email) == 0 or len(email) > 256;
    passwordBad = len(password) <8 or len(password) > 256;
    forenameBad = len(forename) <8 or len(forename) > 256;
    surnameBad = len(surname) <8 or len(surname) > 256;


    if (emailBad):
        data = {
            "message": "Invalid email"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (passwordBad):
        data = {
            "message": "Invalid password"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (forenameBad):
        data = {
            "message": "Invalid forename"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (surnameBad):
        data = {
            "message": "Invalid surname"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    new_user = User (
        email    = email,
        password = password,
        forename = forename,
        surname  = surname
    )

    database.session.add ( new_user )
    database.session.commit ( )

    role = Role.query.filter ( Role.name == "user" ).first ( )

    user_role = UserRole (
        user_id = new_user.id,
        role_id = role.id
    )

    database.session.add ( user_role )
    database.session.commit ( )

    data = {
        "message": "Created customer"
    }
    response = jsonify(data)
    response.status_code = 200
    return response

@application.route ( "/register_courier", methods=["POST"] )
def registerCourier ( ):
    email = request.json["email"]
    password = request.json["password"]
    forename = request.json["forename"]
    surname = request.json["surname"]

    user = User.query.filter(User.email == email).first()

    if (user != None):
        data = {
            "message": "Email already exists"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (len(email) == 0):
        data = {
            "message": "Field email is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (len(password) == 0):
        data = {
            "message": "Field password is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (len(forename) == 0):
        data = {
            "message": "Field forename is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (len(surname) == 0):
        data = {
            "message": "Field surname is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    # check
    emailBad = len(email) == 0 or len(email) > 256;
    passwordBad = len(password) < 8 or len(password) > 256;
    forenameBad = len(forename) < 8 or len(forename) > 256;
    surnameBad = len(surname) < 8 or len(surname) > 256;

    if (emailBad):
        data = {
            "message": "Invalid email"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (passwordBad):
        data = {
            "message": "Invalid password"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (forenameBad):
        data = {
            "message": "Invalid forename"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (surnameBad):
        data = {
            "message": "Invalid surname"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    new_user = User(
        email=email,
        password=password,
        forename=forename,
        surname=surname
    )

    database.session.add(new_user)
    database.session.commit()

    role = Role.query.filter(Role.name == "courier").first()

    user_role = UserRole(
        user_id=new_user.id,
        role_id=role.id
    )

    database.session.add(user_role)
    database.session.commit()

    data = {
        "message": "Created customer"
    }
    response = jsonify(data)
    response.status_code = 200
    return response

jwtManager = JWTManager ( application )

@application.route ( "/login", methods = ["POST"] )
def login ( ):
    email    = request.json["email"]
    password = request.json["password"]

    emailBad = len(email) == 0 or len(email) > 256;
    if (emailBad):
        data = {
            "message": "Invalid email"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (len(email) == 0):
        data = {
            "message": "Field email is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (len(password) == 0):
        data = {
            "message": "Field password is missing"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    user = User.query.filter(User.email == email, User.password == password).first()
    if (user == None):
        data = {
            "message": "Invalid credentials"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    claims = {
            "id" : user.id,
            "email" : user.email,
            "forename": user.forename,
            "surname": user.surname,
            "roles": [ role.name for role in user.roles ]
    }

    access_token  = create_access_token ( identity = user.email, additional_claims = claims )
    refresh_token = create_refresh_token ( identity = user.email, additional_claims = claims )

    return jsonify ( access_token = access_token, refresh_token = refresh_token );

#redis nam treba za cuvanje invalid tokena
def update ( token ):
    with Redis ( host = "redis", port = 6379, db = 0 ) as redis:
        redis.lpush ( "banned", token )
        redis.publish ( "channel", token )

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

def banned_check ( function ):
    @jwt_required ( )
    def wrapper ( *args, **kwargs ):
        jwt = request.headers.get('Authorization').split()[1]
        if ( jwt not in deleted ):
            return function ( *args, **kwargs )
        else:
            return "Invalid token"

    return wrapper


@application.route("/delete", methods=["GET"])
@banned_check
def brisanjeSvogNaloga():
    token = request.headers.get('Authorization')
    if (token == None):
        data = {
            "message": "Missing Authorization header"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    token = request.headers.get('Authorization').split()[1]

    decodedToken = jwt.decode(token,Configuration.JWT_SECRET_KEY,algorithms=["HS256"]);

    email = decodedToken.get("email");
    user = User.query.filter(User.email == email).first();
    if (user == None):
        data = {
            "message": "Unknown user"
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    database.session.delete(user)
    database.session.commit()

    update(token)

    response = make_response()
    response.status_code = 400
    return response


@application.route("/ispisiUsere", methods=["GET"])
def ispisiUsere():
    return jsonify(employees=[str(user) for user in User.query.all()])
@application.route("/ispisiRole", methods=["GET"])
def ispisiRole():
    return jsonify(employees=[str(role) for role in Role.query.all()])

from threading import Thread
if ( __name__ == "__main__" ):
    with Redis ( host = "redis", port = 6379, db = 0 ) as redis:
        list = redis.lrange ( "banned", 0, -1 )
        banned = [item.decode ( ) for item in list]

    Thread ( target = listener ).start ( )


    application.run ( debug = True, host="0.0.0.0", port=5002 )