from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    BundlingOptions,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_s3_notifications as s3n,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)
from constructs import Construct
import os


def make_lambda(scope, id, entry, env, timeout, memory=128):
    # package Lambda using Docker and install dependencies from requirements.txt
    return lambda_.Function(
        scope, id,
        runtime=lambda_.Runtime.PYTHON_3_11,
        handler="index.lambda_handler",
        code=lambda_.Code.from_asset(
            entry,
            bundling=BundlingOptions(
                image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                command=[
                    "bash", "-c",
                    "pip install -r requirements.txt -t /asset-output --platform manylinux2014_x86_64 --only-binary=:all: && cp -r . /asset-output"
                ],
            ),
        ),
        environment=env,
        timeout=timeout,
        memory_size=memory,
    )


class ComputeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        table: dynamodb.Table,
        gsi_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_root = os.path.join(os.path.dirname(__file__), "..", "lambda")

        bucket = s3.Bucket(
            self, "TestBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # size-tracking Lambda
        size_tracking_fn = make_lambda(
            self, "SizeTrackingFunction",
            entry=os.path.join(lambda_root, "size_tracking"),
            env={
                "BUCKET_NAME": bucket.bucket_name,
                "TABLE_NAME":  table.table_name,
            },
            timeout=Duration.seconds(30),
        )
        bucket.grant_read(size_tracking_fn)
        table.grant_write_data(size_tracking_fn)

        # trigger Lambda on S3 object create and delete events
        dest = s3n.LambdaDestination(size_tracking_fn)
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED, dest)
        bucket.add_event_notification(s3.EventType.OBJECT_REMOVED, dest)

        # plotting Lambda
        plotting_fn = make_lambda(
            self, "PlottingFunction",
            entry=os.path.join(lambda_root, "plotting"),
            env={
                "BUCKET_NAME": bucket.bucket_name,
                "TABLE_NAME":  table.table_name,
                "GSI_NAME":    gsi_name,
            },
            timeout=Duration.seconds(60),
            memory=512,
        )
        bucket.grant_read_write(plotting_fn)
        table.grant_read_data(plotting_fn)

        # expose a REST API for the plotting Lambda
        api = apigw.LambdaRestApi(
            self, "PlottingApi",
            handler=plotting_fn,
            proxy=True,
        )

        # driver Lambda
        driver_fn = make_lambda(
            self, "DriverFunction",
            entry=os.path.join(lambda_root, "driver"),
            env={
                "BUCKET_NAME":  bucket.bucket_name,
                "PLOTTING_API": api.url,
            },
            timeout=Duration.seconds(60),
        )
        bucket.grant_read_write(driver_fn)