from flask import request, Response, jsonify, Flask, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity

import os


from redis import Redis
from sparkConf import Configuration

import jwt
from pyspark.sql import SparkSession


application = Flask ( __name__ )
application.config.from_object ( Configuration )


def banned_check ( function ):
    @jwt_required ( )
    def wrapper ( *args, **kwargs ):
        jwt = request.headers.get('Authorization').split()[1]
        if ( jwt not in deleted ):
            return function ( *args, **kwargs )
        else:
            return "Invalid token"

    return wrapper


@application.route("/product_statistics", methods=["GET"])
@banned_check
def productStatistics():

    builder = SparkSession.builder.appName("Simple PySpark")

    spark = builder.getOrCreate()

    data = [
        "I love python",
        "I love Spark",
        "I hate Spark"
    ]

    rdd = spark.sparkContext.parallelize(data)

    result = rdd.filter(lambda item: "Spark" in item).collect()

    spark.stop()
    return jsonify(result)


jwtManager = JWTManager ( application )

deleted = [ ]
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

from threading import Thread
if ( __name__ == "__main__" ):
    with Redis ( host = "redis", port = 6379, db = 0 ) as redis:
        list = redis.lrange ( "banned", 0, -1 )
        banned = [item.decode ( ) for item in list]

    Thread ( target = listener ).start ( )


    application.run ( debug = True, host="0.0.0.0", port=5004 )