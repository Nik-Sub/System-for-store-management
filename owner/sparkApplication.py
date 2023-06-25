from flask import request, Response, jsonify, Flask, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity

import os
import subprocess

from redis import Redis
from sparkConf import Configuration
from pyspark.sql.functions import count, when, sum

import jwt
from pyspark.sql import SparkSession
from store.configuration import Configuration as ConfigurationDB, databaseUrl


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

    builder = SparkSession.builder.appName("Statistics")
    spark = builder.getOrCreate()


    productsFrame = spark.read \
        .format("jdbc") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .option("url", f"jdbc:mysql://{databaseUrl}:3306/dbstore") \
        .option("dbtable", "dbstore.product") \
        .option("user", "root") \
        .option("password", "root") \
        .load()

    productOrderFrame = spark.read \
        .format("jdbc") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .option("url", f"jdbc:mysql://{databaseUrl}:3306/dbstore") \
        .option("dbtable", "dbstore.product_order") \
        .option("user", "root") \
        .option("password", "root") \
        .load()

    orderOfCustomerframe = spark.read \
        .format("jdbc") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .option("url", f"jdbc:mysql://{databaseUrl}:3306/dbstore") \
        .option("dbtable", "dbstore.order_of_customer") \
        .option("user", "root") \
        .option("password", "root") \
        .load()

    result = productsFrame.join(
        productOrderFrame,
        productOrderFrame["productId"] == productsFrame["id"]
    ).join(
        orderOfCustomerframe,
        orderOfCustomerframe["id"] == productOrderFrame["orderId"]
    ).groupBy(productsFrame["id"], productsFrame["name"]).agg(
    productsFrame["name"].alias("productName"),
    sum(when(orderOfCustomerframe["status"] == "cekanje", productOrderFrame["quantity"])).alias("cekanje_sum"),
    sum(when(orderOfCustomerframe["status"] == "izvrsena", productOrderFrame["quantity"])).alias("izvrsena_sum")
    )

    statisticsInTableFormat = result.select("productName", "cekanje_sum", "izvrsena_sum").collect()

    statistics = []
    for row in statisticsInTableFormat:

        statistics.append({
            "name": row.productName,
            "sold": row.izvrsena_sum if row.izvrsena_sum != None else 0,
            "waiting": row.cekanje_sum if row.cekanje_sum != None else 0

        })

    data = {
        "statistics": statistics
    }
    response = jsonify(data)
    response.status_code = 200
    return response





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