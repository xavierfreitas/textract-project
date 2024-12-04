from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3_deployment as s3_deployment,
    RemovalPolicy,
    aws_apigateway as apigateway,
    CfnOutput,
    Duration, 
    Duration,
)
from constructs import Construct
import json


'''
format: we define the project stack via python class with services, cdk deploy runs throug app.py, creates project stack

architecture: 
    - we can deploy with an s3 bucket, just need two buckets in this case, one for uploads and one for the frontend
    - lambda is set to trigger when an item enters the bucket, that item is sent to textract via its api

'''


class TextractProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # defined bucket for uploads
        # parameters for the constructor:
        #   scope: the scope in which this resource is defined.
        #   id: id of reseource
        #   bucket_name: name of buket
        #   versioned: TODO: versioning?
        #   removal_policy: set to remove on stack deletion
        #   auto_delete_objects: delete objects within the bucket when the bucket is deleted
        #   cors: Cross-Origin Resource Sharing (CORS) configuration
        #   block_public_access: public access settings for the bucket

        self.uploads_bucket = s3.Bucket(
            self,
            "TextractUploadsBucket",
            bucket_name="textract-uploads-bucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.PUT],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                )
            ],
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
        )

        # sets the policy for the bucket
        # NOTE: this might run into an issue with a precreated bucket but in this case,
        #       created dynamically
        self.uploads_bucket.add_to_resource_policy(
            # add iam statement
            # we want to allow PutObject to the s3 bucket
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.AnyPrincipal()],
                actions=["s3:PutObject"],
                resources=[self.uploads_bucket.arn_for_objects("*")],
                # NOTE: resources says what items the defined policy refers to
                #       in this case, all
                #       defualt naming scheme usually: arn:partition:service:region:account-id:resource
            )
        )


        # frontend bucket
        # see previous bucekt for parameters
        self.frontend_bucket = s3.Bucket(
            self,
            "TextractFrontendBucket",
            bucket_name="textract-frontend-bucket",
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )



        textract_lambda = _lambda.Function(
            self,
            "TextractProcessingLambda",             # id
            runtime=_lambda.Runtime.PYTHON_3_9,     # runtime
            handler="lambda_function.handler",      # handler
            code=_lambda.Code.from_asset("lambda"), # source code of lambda, assume directly sees folder name
            environment={                           # set env variable
                'UPLOAD_BUCKET': self.uploads_bucket.bucket_name
            },
            timeout=Duration.seconds(15)  # cancels after 15 seconds
        )

        
        # set policy statement for lambda
        # NOTE: arg defined right before
        self.uploads_bucket.grant_read(textract_lambda)
        textract_lambda.add_to_role_policy(
            # we are just setting to all for this polciy, other more specifics may break the code
            iam.PolicyStatement(
                actions=["textract:*"], 
                resources=["*"]
            )
        )


        # lambda API setup
        api = apigateway.LambdaRestApi(
            self,
            "TextractAPI",
            handler=textract_lambda,
            proxy=True,
            default_cors_preflight_options={
                "allow_origins": apigateway.Cors.ALL_ORIGINS, # anything can access
                "allow_methods": apigateway.Cors.ALL_METHODS, # allows all HTTP methods like GET, POST, PUT, DELETE,
            }
        )



        # dynamic frontend deployment via s3 bucket:
        s3_deployment.BucketDeployment(
            self,
            "DeployFrontendFiles",
            sources=[
                s3_deployment.Source.asset("./frontend", exclude=["config.json"]),
                s3_deployment.Source.data( # .data() should verify args are the same type, then send to s3 and deploy
                    "config.json",
                    json.dumps({
                        "UPLOAD_BUCKET": f"https://{self.uploads_bucket.bucket_name}.s3.amazonaws.com/",
                        "API_URL": api.url
                    })
                )
            ],
            # have to send to frontend_bucket
            destination_bucket=self.frontend_bucket,
        )

        # Outputs
        CfnOutput(
            self,
            "FrontendWebsiteURL",
            value=self.frontend_bucket.bucket_website_url,
            description="URL for the hosted front-end website"
        )
