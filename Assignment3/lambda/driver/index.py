import boto3
import time
import urllib3
import os

BUCKET_NAME = os.environ["BUCKET_NAME"]
PLOTTING_API = os.environ["PLOTTING_API"]
SLEEP_SEC = 2

s3 = boto3.client("s3")

def put(key, body):
    s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=body.encode())
    print(f"[driver] PUT {key!r} ({len(body.encode())} bytes)")

def delete(key):
    s3.delete_object(Bucket=BUCKET_NAME, Key=key)
    print(f"[driver] DEL {key!r}")

def lambda_handler(event, context):
    # create assignment1.txt (19 bytes)
    put("assignment1.txt", "Empty Assignment 1")
    time.sleep(SLEEP_SEC)

    # create assignment1.txt (28 bytes)
    put("assignment1.txt", "Empty Assignment 2222222222")
    time.sleep(SLEEP_SEC)

    # delete assignment1.txt (0 bytes)
    delete("assignment1.txt")
    time.sleep(SLEEP_SEC)

    # create assignment2.txt (2 bytes)
    put("assignment2.txt", "33")
    time.sleep(SLEEP_SEC)

    # call plotting REST API
    http = urllib3.PoolManager()
    resp = http.request("GET", PLOTTING_API)
    print(f"[driver] plotting API: {resp.status} {resp.data.decode()}")

    return {"statusCode": 200, "body": "Driver finished."}