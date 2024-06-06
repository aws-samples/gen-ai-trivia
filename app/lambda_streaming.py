# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam
)
from cdk_nag import NagSuppressions


class BedrockStreamingFunction(Construct):
    """
    Lambda function for streaming question generation using Bedrock.

    This class creates a Lambda function with the necessary permissions and
    configuration to generate questions using the Bedrock AI model.

    Attributes:
        function (lambda.Function): The Lambda function.
    """

    def __init__(self, scope: Construct, id: str, **kwargs):
        """
        Initialize the BedrockStreamingFunction construct.

        Args:
            scope (Construct): The scope of the construct.  
            id (str): The ID of the construct.
            **kwargs: Additional arguments.
        """
        super().__init__(scope, id, **kwargs)

        self.lambda_function = _lambda.Function(
            self,
            "rGenAiTriviaBedrockStreamingFunction",
            function_name="bedrock-generate-questions-streaming",
            runtime=_lambda.Runtime.NODEJS_20_X,
            handler="index.handler",
            code=_lambda.Code.from_asset("app/lambda_src/generate_questions_streaming"),
            timeout=cdk.Duration.seconds(900)
        )

        self.lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModelWithResponseStream"],
                resources=["*"]
            )
        )

        NagSuppressions.add_resource_suppressions(
            self.lambda_function,
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Managed policy for Lambda Execution",
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Using wildcard to allow multiple models if needed.",
                }
            ],
            apply_to_children=True
        )
