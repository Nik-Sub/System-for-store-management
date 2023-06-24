from datetime import timedelta;
import os;

databaseUrl = os.environ["DATABASE_URL"];

class Configuration ( ):
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/dbstore";
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta ( minutes = 15 );
    JWT_REFRESH_TOKEN_EXPIRES = timedelta ( days = 30 );
    # JWT_TOKEN_LOCATION = ["headers", "query_string"]
    # JWT_HEADER_NAME = "Authorization"
    # JWT_HEADER_TYPE = "Bearer"