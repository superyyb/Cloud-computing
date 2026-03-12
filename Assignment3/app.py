import aws_cdk as cdk
from stacks.storage_stack import StorageStack
from stacks.compute_stack import ComputeStack

app = cdk.App()

storage = StorageStack(app, "StorageStack")

ComputeStack(
    app, "ComputeStack",
    table=storage.table,
    gsi_name=storage.gsi_name,
)

app.synth()