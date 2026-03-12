import os
import time
import json
import boto3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from boto3.dynamodb.conditions import Key

BUCKET_NAME = os.environ["BUCKET_NAME"]
TABLE_NAME = os.environ["TABLE_NAME"]
GSI_NAME = os.environ.get("GSI_NAME", "GSI_GlobalMax")

ddb = boto3.resource("dynamodb")
table = ddb.Table(TABLE_NAME)
s3 = boto3.client("s3")

def lambda_handler(event, context):
    now = int(time.time())
    start_ts = now - 10

    # Query last 10s for this bucket
    resp = table.query(
        KeyConditionExpression=Key("BucketName").eq(BUCKET_NAME)
            & Key("Timestamp").between(start_ts, now),
        ScanIndexForward=True,
    )
    items = resp.get("Items", [])
    xs = [int(it["Timestamp"]) for it in items]
    ys = [int(it.get("TotalSizeBytes", 0)) for it in items]

    # Query global max
    max_resp = table.query(
        IndexName=GSI_NAME,
        KeyConditionExpression=Key("GlobalPK").eq("GLOBAL"),
        ScanIndexForward=False, # in descending order
        Limit=1,
    )
    max_item = (max_resp.get("Items") or [{}])[0]
    global_max = int(max_item.get("TotalSizeBytes", 0))

    # plot
    plt.figure()
    if xs:
        plt.plot(xs, ys, marker="o")
    plt.axhline(y=global_max, linestyle="--", label=f"Global max: {global_max} B")
    plt.xlabel("Timestamp")
    plt.ylabel("Size (bytes)")
    plt.title(f"Bucket size last 10s: {BUCKET_NAME}")
    plt.legend()
    plt.tight_layout()

    out = "/tmp/plot.png"
    plt.savefig(out, dpi=150)
    plt.close()

    # upload to S3 bucket
    s3.upload_file(out, BUCKET_NAME, "plot", ExtraArgs={"ContentType": "image/png"})

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "bucket":          BUCKET_NAME,
            "plot_object":     "plot",
            "points":          len(xs),
            "global_max_bytes": global_max,
        }),
    }