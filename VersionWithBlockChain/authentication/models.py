from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy ( );

class UserRole ( database.Model ):
    id      = database.Column ( database.Integer, primary_key = True, autoincrement=True );
    user_id = database.Column ( database.Integer, database.ForeignKey ( "user.id" ), nullable = False );
    role_id = database.Column ( database.Integer, database.ForeignKey ( "role.id" ), nullable = False );

    def __init__ ( self, user_id, role_id ):
        self.user_id  = user_id
        self.role_id      = role_id


class User ( database.Model ):
    id       = database.Column ( database.Integer, primary_key = True, autoincrement=True);
    email    = database.Column ( database.String ( 256 ), nullable = False, unique = True );
    password = database.Column ( database.String(256), nullable = False );
    forename = database.Column ( database.String(256), nullable = False );
    surname  = database.Column ( database.String(256), nullable = False );

    roles = database.relationship ( "Role", secondary = UserRole.__table__, back_populates = "users" );

    def __init__ ( self, email, password, forename, surname ):
        self.email  = email
        self.password      = password
        self.forename     = forename
        self.surname   = surname

    def __repr__(self):
        return str(self.id) + " " + self.email + " " + self.password + " " + self.forename + " " + self.surname

class Role ( database.Model ):
    id   = database.Column ( database.Integer, primary_key = True, autoincrement=True );
    name = database.Column ( database.String ( 256 ), nullable = False );

    users = database.relationship ( "User", secondary = UserRole.__table__, back_populates = "roles" );

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return str(self.id) + " " + self.name
