from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_s3_notifications as s3_notifications,
    aws_iam as iam,
    aws_s3_deployment as s3_deployment,
    RemovalPolicy,
    aws_apigateway as apigateway,
    CfnOutput,
)
from constructs import Construct
import json
import os

class TextractProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for User Uploads
        self.uploads_bucket = s3.Bucket(
            self,
            "TextractUploadsBucket",
            bucket_name="textract-uploads-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # S3 Bucket for Frontend Hosting
        self.frontend_bucket = s3.Bucket(
            self,
            "TextractFrontendBucket",
            bucket_name="textract-frontend-bucket",
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ACLS,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Lambda Function to Process Files
        textract_lambda = _lambda.Function(
            self,
            "TextractProcessingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset("lambda"),
        )

        # Grant Permissions to Lambda
        self.uploads_bucket.grant_read(textract_lambda)
        textract_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["textract:*"],
                resources=["*"]
            )
        )

        # Trigger Lambda on S3 Object Upload
        self.uploads_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(textract_lambda)
        )

        # API Gateway to Expose Lambda
        api = apigateway.LambdaRestApi(
            self,
            "TextractAPI",
            handler=textract_lambda,
            proxy=True,
            default_cors_preflight_options={
                "allow_origins": apigateway.Cors.ALL_ORIGINS,
                "allow_methods": apigateway.Cors.ALL_METHODS,
            }
        )

        # Dynamically Generate Config.json
        config = {
            "UPLOAD_BUCKET": f"https://{self.uploads_bucket.bucket_name}.s3.amazonaws.com/",
            "API_URL": api.url
        }
        config_path = "./frontend/config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as config_file:
            json.dump(config, config_file)

        # Deploy Frontend Files
        s3_deployment.BucketDeployment(
            self,
            "DeployFrontendFiles",
            sources=[s3_deployment.Source.asset("./frontend")],
            destination_bucket=self.frontend_bucket,
        )

        # Outputs
        CfnOutput(
            self,
            "FrontendBucketURL",
            value=self.frontend_bucket.bucket_website_url,
            description="URL for the hosted front-end website"
        )
        CfnOutput(
            self,
            "APIGatewayURL",
            value=api.url,
            description="The dynamically generated API Gateway URL"
        )
