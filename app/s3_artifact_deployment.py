# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from constructs import Construct
from aws_cdk import (
    Stack,
    Aspects,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_ssm as ssm,
    aws_s3_deployment as s3deploy
)
from cdk_nag import NagSuppressions, AwsSolutionsChecks


class S3ArtifactDeployment(Stack):
    """
    A CDK Stack that deploys an artifact to an S3 bucket and associates it with a CloudFront distribution.

    Deploys the frontend artifact to the S3 bucket created in the main application stack.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initializes the S3ArtifactDeployment stack.

        Args:
            scope (Construct): The scope in which this construct is created.
            construct_id (str): The unique identifier for this construct.
            **kwargs: Additional keyword arguments to pass to the Stack constructor.
        """
        super().__init__(scope, construct_id, **kwargs)

        ssm_bucket_arn = self.get_ssm_value(parameter_name="/genAiTrivia/s3/bucketArn")
        ssm_distribution_id = self.get_ssm_value(parameter_name="/genAiTrivia/cloudfront/distributionId")
        ssm_distribution_name = self.get_ssm_value(parameter_name="/genAiTrivia/cloudfront/distributionDomainName")

        i_bucket = s3.Bucket.from_bucket_attributes(
            self,
            "rGetIBucket",
            bucket_arn=ssm_bucket_arn
        )

        i_distribution = cloudfront.Distribution.from_distribution_attributes(
            self,
            "rGetIDistribution",
            distribution_id=ssm_distribution_id,
            domain_name=ssm_distribution_name
        )

        s3deploy.BucketDeployment(
            self,
            "rGenAiTriviaDeploySourceToBucket",
            sources=[s3deploy.Source.asset("./www/dist")],
            destination_bucket=i_bucket,
            distribution=i_distribution,
            distribution_paths=["/"]
        )

        NagSuppressions.add_resource_suppressions(
            self,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "The IAM user, role, or group uses AWS managed policies."
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "The IAM entity contains wildcard permissions and does not have " \
                        "a cdk-nag rule suppression with evidence for those permission."
                },
                {
                    "id": "AwsSolutions-L1",
                    "reason": "The non-container Lambda function is not configured to use the latest runtime version."
                }
            ],
            apply_to_children=True
        )

        Aspects.of(self).add(AwsSolutionsChecks())

    def get_ssm_value(self, parameter_name: str):
        """Retrieves the value of a Systems Manager parameter.

        Args:
            scope (cdk.Construct): The construct scope.
            parameter_name (str): The name of the SSM parameter.

        Returns:
            str: The value of the SSM parameter.

        This function retrieves the value of an SSM parameter by name. It first uses
        the CDK's value_from_lookup method to get the parameter value. If the value
        contains the string 'dummy-value', it will return either a hardcoded ARN
        or the string 'dummy-value' itself. Otherwise it simply returns the
        original value retrieved from SSM.
        """
        _value = ssm.StringParameter.value_from_lookup(self, parameter_name)
        if 'dummy-value' in _value and "arn" in _value.lower():
            return "arn:aws:service:us-east-1:123456789012:entity/dummy-value"
        if 'dummy-value' in _value:
            return "dummy-value"

        return _value
