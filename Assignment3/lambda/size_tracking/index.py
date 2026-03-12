import boto3
import time
import os

BUCKET_NAME = os.environ["BUCKET_NAME"]
TABLE_NAME = os.environ["TABLE_NAME"]

s3  = boto3.client("s3")
ddb = boto3.client("dynamodb")

def lambda_handler(event, context):
    # list all objects in the bucket and compute total size and count
    resp = s3.list_objects_v2(Bucket=BUCKET_NAME)
    total_size = 0
    total_count = 0
    for obj in resp.get("Contents", []):
        total_size += obj["Size"]
        total_count += 1

    # timestamp
    ts = int(time.time())

    # write to DynamoDB
    ddb.put_item(
        TableName=TABLE_NAME,
        Item={
            "BucketName":       {"S": BUCKET_NAME},
            "Timestamp":        {"N": str(ts)},
            "TotalSizeBytes":   {"N": str(total_size)},
            "TotalObjectCount": {"N": str(total_count)},
            "GlobalPK":         {"S": "GLOBAL"},
        },
    )
    return {"statusCode": 200, "body": f"size={total_size}, count={total_count}"}