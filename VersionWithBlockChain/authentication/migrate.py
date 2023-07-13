from flask import Flask;
from configuration import Configuration;
from flask_migrate import Migrate, init, migrate, upgrade;
from models import database, Role, UserRole, User;
from sqlalchemy_utils import database_exists, create_database;
import pymysql

application = Flask ( __name__ );
application.config.from_object ( Configuration );

migrateObject = Migrate ( );

if ( not database_exists ( application.config["SQLALCHEMY_DATABASE_URI"] ) ):
    create_database ( application.config["SQLALCHEMY_DATABASE_URI"] );

database.init_app ( application );
migrateObject.init_app(application, database)

with application.app_context ( ) as context:
    # init();
    # migrate(message="Production migration");
    # upgrade();
    database.create_all()

    ownerRole = Role ( name = "owner" );
    userRole = Role ( name = "customer" );
    courierRole = Role(name="courier");

    database.session.add ( ownerRole );
    database.session.commit ( );
    database.session.add ( userRole );
    database.session.commit ( );
    database.session.add(courierRole);
    database.session.commit ( );

    owner = User (
            email =  "onlymoney@gmail.com",
            password = "evenmoremoney",
            forename = "Scrooge",
            surname = "McDuck"
    );

    database.session.add ( owner );
    database.session.commit ( );

    userRole = UserRole (
            user_id = owner.id,
            role_id = ownerRole.id
    );

    #ja dodao
    database.session.add(userRole);
    database.session.commit();