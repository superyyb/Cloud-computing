from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class StorageStack(Stack):
    GSI_NAME = "GSI_GlobalMax"

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB table to store S3 object size history
        self.table = dynamodb.Table(
            self, "S3ObjectSizeHistory",
            partition_key=dynamodb.Attribute(
                name="BucketName", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="Timestamp", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # GSI for querying the global maximum bucket size
        self.table.add_global_secondary_index(
            index_name=self.GSI_NAME,
            partition_key=dynamodb.Attribute(
                name="GlobalPK", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="TotalSizeBytes", type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        self.gsi_name = self.GSI_NAME