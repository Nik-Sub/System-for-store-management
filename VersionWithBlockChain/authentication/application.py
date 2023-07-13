from flask import request, Response, jsonify, Flask, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy

from configuration import Configuration
from models import User, database, Role, UserRole

import jwt

import re




application = Flask ( __name__ )


#for authenticationDB
application.config.from_object ( Configuration )
database.init_app ( application )

@application.route ( "/register_customer", methods=["POST"] )
def registerCustomer ( ):

    email = request.json.get('email', None)
    password = request.json.get('password', None)
    forename = request.json.get('forename', None)
    surname = request.json.get('surname', None)

    user = User.query.filter(User.email == email).first()

    if (user != None):
        data = {
            "message" : "Email already exists."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (forename == None or len(forename) == 0):
        data = {
            "message": "Field forename is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (surname == None or len(surname) == 0):
        data = {
            "message": "Field surname is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (email == None or len(email) == 0):
        data = {
            "message": "Field email is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (password == None or len(password) == 0):
        data = {
            "message": "Field password is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response



    email = email.replace(" ", "")
    password = password.replace(" ", "")
    forename = forename.replace(" ", "")
    surname = surname.replace(" ", "")

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{3,}$'



    #check
    emailBad = len(email) == 0 or len(email) > 256 or not (re.match(email_pattern, email))
    passwordBad = len(password) <8 or len(password) > 256;
    forenameBad = len(forename) > 256;
    surnameBad = len(surname) > 256;


    if (emailBad):
        data = {
            "message": "Invalid email."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (passwordBad):
        data = {
            "message": "Invalid password."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (forenameBad):
        data = {
            "message": "Invalid forename."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (surnameBad):
        data = {
            "message": "Invalid surname."
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

    role = Role.query.filter ( Role.name == "customer" ).first ( )

    user_role = UserRole (
        user_id = new_user.id,
        role_id = role.id
    )

    database.session.add ( user_role )
    database.session.commit ( )

    data = {
        "message": "Created customer."
    }
    response = jsonify(data)
    response.status_code = 200
    return response

@application.route ( "/register_courier", methods=["POST"] )
def registerCourier ( ):
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    forename = request.json.get('forename', None)
    surname = request.json.get('surname', None)

    user = User.query.filter(User.email == email).first()

    if (user != None):
        data = {
            "message": "Email already exists."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (forename == None or len(forename) == 0):
        data = {
            "message": "Field forename is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (surname == None or len(surname) == 0):
        data = {
            "message": "Field surname is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    if (email == None or len(email) == 0):
        data = {
            "message": "Field email is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (password == None or len(password) == 0):
        data = {
            "message": "Field password is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response


    email = email.replace(" ", "")
    password = password.replace(" ", "")
    forename = forename.replace(" ", "")
    surname = surname.replace(" ", "")

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{3,}$'


    # check
    emailBad = len(email) == 0 or len(email) > 256 or not (re.match(email_pattern, email))
    passwordBad = len(password) < 8 or len(password) > 256;
    forenameBad = len(forename) > 256;
    surnameBad = len(surname) > 256;

    if (emailBad):
        data = {
            "message": "Invalid email."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (passwordBad):
        data = {
            "message": "Invalid password."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (forenameBad):
        data = {
            "message": "Invalid forename."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (surnameBad):
        data = {
            "message": "Invalid surname."
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
        "message": "Created customer."
    }
    response = jsonify(data)
    response.status_code = 200
    return response

jwtManager = JWTManager ( application )

@application.route ( "/login", methods = ["POST"] )
def login ( ):
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    if (email == None or len(email) == 0):
        data = {
            "message": "Field email is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response
    if (password == None or len(password) == 0):
        data = {
            "message": "Field password is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response


    # email = email.replace(" ", "")
    # password = password.replace(" ", "")

    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{3,}$'


    # check
    emailBad = len(email) == 0 or len(email) > 256 or not (re.match(email_pattern, email))




    if (emailBad):
        data = {
            "message": "Invalid email."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    user = User.query.filter(User.email == email, User.password == password).first()
    if (user == None):
        data = {
            "message": "Invalid credentials."
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

    accessToken  = create_access_token ( identity = user.email, additional_claims = claims )
    refresh_token = create_refresh_token ( identity = user.email, additional_claims = claims )

    return jsonify ( accessToken = accessToken)




def banned_check ( function ):
    def wrapper ( *args, **kwargs ):
        if ('Authorization' not in request.headers):
            data = {
                "msg": "Missing Authorization Header"
            }
            response = jsonify(data)
            response.status_code = 401
            return response

        return function ( *args, **kwargs )


    return wrapper


@application.route("/delete", methods=["POST"])
@banned_check
def brisanjeSvogNaloga():

    token = request.headers.get('Authorization').split()[1]

    decodedToken = jwt.decode(token,Configuration.JWT_SECRET_KEY,algorithms=["HS256"]);

    email = decodedToken.get("email");
    user = User.query.filter(User.email == email).first();
    if (user == None):
        data = {
            "message": "Unknown user."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    database.session.delete(user)
    database.session.commit()

    # update(token)

    response = make_response()
    response.status_code = 200
    return response


@application.route("/ispisiUsere", methods=["GET"])
def ispisiUsere():
    return jsonify(employees=[str(user) for user in User.query.all()])
@application.route("/ispisiRole", methods=["GET"])
def ispisiRole():
    return jsonify(employees=[str(role) for role in Role.query.all()])

from threading import Thread
if ( __name__ == "__main__" ):

    application.run ( debug = True, host="0.0.0.0", port=5000 )