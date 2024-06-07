# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
from constructs import Construct
from aws_cdk import (
    Stack,
    Tags,
    Aspects,
    CfnOutput
)
from cdk_nag import AwsSolutionsChecks
from app.dynamodb_helper import create_dynamodb
from app.cognito_helper import CognitoUserPool
from app.cloudfront_helper import CreateCloudFrontFrontEnd
from app.lambda_streaming import BedrockStreamingFunction


class ApplicationStack(Stack):
    """
    Application stack for Gen AI Trivia.

    This stack creates the core application infrastructure, including:
    - DynamoDB table
    - Cognito user pool and identity pool
    - CloudFront distribution for frontend hosting 
    - Lambda function for streaming question generation

    Attributes:
        table (dynamodb.ITable): The DynamoDB table.
        user_pool (CognitoUserPool): The Cognito user pool.
        frontend (CreateCloudFrontFrontEnd): The CloudFront distribution for frontend hosting.
        streaming_lambda (BedrockStreamingFunction): The Lambda function for streaming question generation.
    """

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        """
        Initialize the ApplicationStack.

        Args:
            scope (Construct): The parent of this stack, usually an App or a Stage, but could be any construct.
            construct_id (str): The identifier of this stack. Must be unique within this scope.  
            config (dict): Application configuration.
            **kwargs: Other parameters passed to the base class.

        Attributes:
            Tags: Tags applied to all resources in the stack.
        """
        super().__init__(scope, construct_id, **kwargs)
        # DynamoDB Tables
        create_dynamodb(
            scope=self,
            table_name=config["appInfrastructure"]["dynamoDb"]["tableName"]
        )

        # Cognito
        cognito = CognitoUserPool(
            self,
            "rCreateCognitoUserPool",
            table_name=config["appInfrastructure"]['dynamoDb']['tableName']
        )

        cog_identity_pool_id = cognito.get_identity_pool_id()

        CfnOutput(
            self,
            "oGenAiTriviaCognitoPoolIdOutput", 
            value=cog_identity_pool_id,
            description="Cognito Identity Pool ID"
        )

        # CloudFront
        cloudfront = CreateCloudFrontFrontEnd(
            self,
            "rCreateCloudFrontFrontEnd"
        )

        cf_distribution_domain_name = cloudfront.get_distribution_domain_name()

        CfnOutput(
            self,
            "oGenAiTriviaCloudFrontDistributionDomainName",
            value=cf_distribution_domain_name,
            description="CloudFront Distribution Domain Name"
        )

        # BedRock
        BedrockStreamingFunction(
            self,
            "rBedrockStreamingFunction"
        )

        # Add tags to all resources created
        tags = json.loads(json.dumps(config["tags"]))
        for key, value in tags.items():
            Tags.of(self).add(key, value)

        Aspects.of(self).add(AwsSolutionsChecks())
