# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from constructs import Construct
from aws_cdk import (
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_ssm as ssm
)
from cdk_nag import NagSuppressions


class CreateCloudFrontFrontEnd(Construct):
    """
    CloudFront distribution for frontend hosting.

    This class creates an S3 bucket for hosting the frontend, and a CloudFront
    distribution to serve the frontend content.

    Attributes:
        s3_bucket (s3.Bucket): The S3 bucket for hosting the frontend.
        s3_deployment (s3_deployment.BucketDeployment): Deploys the frontend files to the S3 bucket.
        origin_access_identity (cloudfront.OriginAccessIdentity): CloudFront origin access identity to access the S3 bucket.
        user_pool (cognito.UserPool): The Cognito user pool for user authentication.
        user_pool_client (cognito.UserPoolClient): The Cognito user pool client.
    """

    def __init__(self, scope: Construct, id: str, **kwargs):
        """
        Initialize the CreateCloudFrontFrontEnd construct.

        Args:
            scope (Construct): The scope of the construct.
            id (str): The ID of the construct.  
            **kwargs: Additional arguments.

        Attributes:
            bucket (s3.Bucket): The S3 bucket for hosting the frontend.
            distribution (cloudfront.Distribution): The CloudFront distribution for serving the frontend.
        """
        super().__init__(scope, id, **kwargs)

        # Get the stack name and region
        stack = Stack.of(scope)
        region = stack.region
        account = stack.account

        # Create an S3 bucket for hosting the frontend and CloudFront Logs
        self.app_bucket = s3.Bucket(
            self,
            "rGenAiTriviaFrontendS3Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            bucket_name=f"gen-ai-trivia-frontend-{region}-{account}",
            enforce_ssl=True
        )

        NagSuppressions.add_resource_suppressions(
            self.app_bucket,
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "The S3 Bucket has server access logs disabled.",
                }
            ]
        )

        self.log_bucket = s3.Bucket(
            self,
            "rGenAiTriviaFrontendLogS3Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            bucket_name=f"gen-ai-trivia-frontend-logs-{region}-{account}",
            access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE,
            enforce_ssl=True
        )

        NagSuppressions.add_resource_suppressions(
            self.log_bucket,
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "The S3 Bucket has server access logs disabled.",
                }
            ]
        )

        # Create an Origin Access Identity (OAI) for CloudFront
        self.oai = cloudfront.OriginAccessIdentity(self, "rGenAiTriviaOai")

        # Grant the OAI access to the S3 bucket
        self.app_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[self.oai.grant_principal],
                actions=["s3:GetObject"],
                resources=[f"arn:aws:s3:::{self.app_bucket.bucket_name}/*"]
            )
        )

        # Create a CloudFront Web Distribution
        self.distribution = cloudfront.Distribution(
            self,
            "rGenAiTriviaCloudFrontDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.app_bucket, origin_access_identity=self.oai),
            ),
            enabled=True,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=404,
                    response_page_path="/error.html",
                )
            ],
            enable_logging=True,
            log_bucket=self.log_bucket,
            log_file_prefix="gen-ai-trivia-frontend-cloudfront-logs"
        )

        NagSuppressions.add_resource_suppressions(
            self.distribution,
            [
                {
                    "id": "AwsSolutions-CFR1",
                    "reason": "The CloudFront distribution may require Geo restrictions.",
                },
                {
                    "id": "AwsSolutions-CFR2",
                    "reason": "The CloudFront distribution may require integration with AWS WAF.",
                },
                {
                    "id": "AwsSolutions-CFR4",
                    "reason": "The CloudFront distribution allows for SSLv3 or TLSv1 for HTTPS viewer connections.",
                },
                {
                    "id": "AwsSolutions-S1",
                    "reason": "The S3 Bucket has server access logs disabled.",
                },
                {
                    "id": "AwsSolutions-S10",
                    "reason": "The S3 Bucket or bucket policy does not require requests to use SSL.",
                }
            ],
            apply_to_children=True
        )

        ssm.StringParameter(
            self,
            "rGenAiTriviaS3BucketName",
            parameter_name="/genAiTrivia/s3/bucketArn",
            string_value=self.app_bucket.bucket_arn
        )
        ssm.StringParameter(
            self,
            "rGenAiTriviaCloudfrontDistributionId",
            parameter_name="/genAiTrivia/cloudfront/distributionId",
            string_value=self.distribution.distribution_id
        )
        ssm.StringParameter(
            self,
            "rGenAiTriviaCloudfrontDistributionDomainName",
            parameter_name="/genAiTrivia/cloudfront/distributionDomainName",
            string_value=self.distribution.domain_name
        )

    def get_distribution_domain_name(self):
        """
        Get the CloudFront distribution domain name.

        Returns:
            str: The CloudFront distribution domain name.
        """
        return self.distribution.distribution_domain_name
