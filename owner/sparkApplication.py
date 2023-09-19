from functools import wraps

import requests
from flask import request, Response, jsonify, Flask, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, JWTManager, jwt_required, get_jwt_identity

import os
import subprocess

from sparkConf import Configuration
from pyspark.sql.functions import count, when, sum

import jwt
from pyspark.sql import SparkSession
from store.configuration import Configuration as ConfigurationDB, databaseUrl


application = Flask ( __name__ )
application.config.from_object ( Configuration )


def banned_check ( function ):
    @wraps(function)  # Preserve the original function's name and attributes
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
        if (roles[0] != "owner"):
            data = {
                "msg": "Missing Authorization Header"
            }
            response = jsonify(data)
            response.status_code = 401
            return response
        return function ( *args, **kwargs )


    return wrapper



@application.route ( "/update", methods=["POST"] )
@banned_check
def addProduct ( ):

    if 'file' not in request.files:
        data = {
            "message": "Field file is missing."
        }
        response = jsonify(data)
        response.status_code = 400
        return response

    # citanje iz fajla iz requesta
    file = request.files["file"]
    content = file.stream.read().decode()

    data = {
        "content": content
    }

    response = requests.post("http://owner:5004/update", data = data)

    flask_response = Response(response.content, status=response.status_code)
    return flask_response
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
    sum(when(orderOfCustomerframe["status"] == "CREATED", productOrderFrame["quantity"])).alias("cekanje_sum"),
    sum(when(orderOfCustomerframe["status"] == "COMPLETE", productOrderFrame["quantity"])).alias("izvrsena_sum")
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

@application.route("/category_statistics", methods=["GET"])
@banned_check
def categoryStatistics():

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

    categoryFrame = spark.read \
        .format("jdbc") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .option("url", f"jdbc:mysql://{databaseUrl}:3306/dbstore") \
        .option("dbtable", "dbstore.category") \
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

    productCategoryFrame = spark.read \
        .format("jdbc") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .option("url", f"jdbc:mysql://{databaseUrl}:3306/dbstore") \
        .option("dbtable", "dbstore.product_category") \
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

    result = categoryFrame.join(
        productCategoryFrame,
        productCategoryFrame["categoryId"] == categoryFrame["id"], "left"
    ).join(
        productsFrame,
        productsFrame["id"] == productCategoryFrame["productId"], "left"
    ).join(
        productOrderFrame,
        productOrderFrame["productId"] == productsFrame["id"], "left"
    ).join(
        orderOfCustomerframe,
        orderOfCustomerframe["id"] == productOrderFrame["orderId"], "left"
    ).groupBy(categoryFrame["id"], categoryFrame["name"]).agg(
        categoryFrame["name"].alias("categoryName"),
        sum(when(orderOfCustomerframe["status"] == "COMPLETE", productOrderFrame["quantity"]).otherwise(0)).alias("completedPerCategory"))

    result = result.orderBy(result["completedPerCategory"].desc(), result["categoryName"].asc())

    statisticsInTableFormat = result.select("categoryName", "completedPerCategory").collect()

    statistics = []
    for row in statisticsInTableFormat:
        statistics.append({
            "name": row.categoryName,
            "complete": row.completedPerCategory if row.completedPerCategory != None else 0
        })


    data = {
        "statistics": []
    }

    for cat in statistics:
        data["statistics"].append(cat["name"])
    response = jsonify(data)
    response.status_code = 200
    return response

jwtManager = JWTManager ( application )



if ( __name__ == "__main__" ):



    application.run ( debug = True, host="0.0.0.0", port=5001 )