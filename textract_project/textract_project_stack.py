from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_s3_notifications as s3_notifications,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct

class TextractProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        self.bucket = s3.Bucket(
            self,
            "Group2_TextractBucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,  # Use RemovalPolicy directly
            auto_delete_objects=True  # Deletes objects with the bucket
        )
        textract_lambda = _lambda.Function(
            self,
            "Group2_TextractProcessor",
            runtime=_lambda.Runtime.PYTHON_3_9,  # Lambda runtime
            handler="lambda_function.handler",  # Entry point in the Lambda code
            code=_lambda.Code.from_asset("lambda"),  # Path to the Lambda code
        )
        self.bucket.grant_read(textract_lambda)

        # Grant the Lambda function permission to use Textract
        textract_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["textract:*"],  # Allow all Textract actions
                resources=["*"],  # Scope down permissions in a real-world project
            )
        )

        # Set up S3 bucket to trigger Lambda on object creation
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,  # Trigger on file uploads
            s3_notifications.LambdaDestination(textract_lambda)
        )

        # example resource
        # queue = sqs.Queue(
        #     self, "TextractProjectQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
