# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from constructs import Construct
from aws_cdk import (
    RemovalPolicy,
    Stack,
    Duration,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_cognito_identitypool_alpha as cognitoip,
    aws_ssm as ssm
)
from cdk_nag import NagSuppressions


class CognitoUserPool(Construct):
    """
    Cognito user pool and identity pool for user authentication and authorization.

    This class creates a Cognito user pool, user pool client, and identity pool,
    along with the necessary IAM roles and policies. It also stores the relevant
    IDs in Systems Manager Parameter Store.

    Attributes:
        user_pool (cognito.UserPool): The Cognito user pool.
        user_pool_client (cognito.UserPoolClient): The Cognito user pool client.
        identity_pool (cognitoip.IdentityPool): The Cognito identity pool.
    """

    def __init__(self, scope: Construct, id: str, table_name: str, **kwargs):
        """
        Initialize the CognitoUserPool construct.

        Args:  
            scope (Construct): The scope of the construct.
            id (str): The ID of the construct.
            table_name (str): The name of the DynamoDB table.
            **kwargs: Additional arguments.
        """
        super().__init__(scope, id, **kwargs)

        # Get the stack name and region
        stack = Stack.of(self)
        region = stack.region
        account = stack.account
        partition = stack.partition

        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            "rGenAiTriviaCognitoUserPool",
            removal_policy=RemovalPolicy.DESTROY,
            self_sign_up_enabled=False,
            user_pool_name="GenAI-Trivia-UserPool",
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(3)
            ),
            advanced_security_mode=cognito.AdvancedSecurityMode.ENFORCED
        )

        NagSuppressions.add_resource_suppressions(
            self.user_pool,
            [
                {
                    "id": "AwsSolutions-COG2",
                    "reason": "The Cognito user pool does not require MFA."
                }
            ]
        )

        user_pool_client = self.user_pool.add_client(
            "rGenAiTriviaCognitoUserPoolClient",
            user_pool_client_name="GenAI-Trivia-UserPoolClient",
            # id_token_validity=Duration.days(1),
            # access_token_validity=Duration.days(1),
            generate_secret=False
        )

        # Cognito Identity Pool
        self.identity_pool = cognitoip.IdentityPool(
            self,
            "rGenAiTriviaCognitoIdentityPool",
            identity_pool_name="GenAI-Trivia",
            allow_unauthenticated_identities=False,
            authentication_providers=cognitoip.IdentityPoolAuthenticationProviders(
                user_pools=[
                    cognitoip.UserPoolAuthenticationProvider(
                        user_pool=self.user_pool,
                        user_pool_client=user_pool_client
                    )
                ]
            )
        )

        self.identity_pool.authenticated_role.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:Scan",
                    "dynamodb:Query",
                    "dynamodb:UpdateItem",
                    "dynamodb:UpdateTable",
                    "dynamodb:GetRecords"
                ],
                resources=[
                    f"arn:{partition}:dynamodb:{region}:{account}:table/{table_name}/index/*",
                    f"arn:{partition}:dynamodb:{region}:{account}:table/{table_name}/stream/*",
                    f"arn:{partition}:dynamodb:{region}:{account}:table/{table_name}"
                ]
            )
        )

        self.identity_pool.authenticated_role.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction",
                    "lambda:InvokeAsync"
                ],
                resources=[
                    f"arn:{partition}:lambda:{region}:{account}:function:bedrock-generate-questions-streaming"
                ]
            )
        )

        self.identity_pool.authenticated_role.add_to_principal_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["cognito-identity:GetCredentialsForIdentity"],
                resources=["*"]
            )
        )

        NagSuppressions.add_resource_suppressions(
            self.identity_pool,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "The IAM entity contains wildcard permissions and does not have " \
                        "a cdk-nag rule suppression with evidence for those permission.",
                }
            ],
            apply_to_children=True
        )

        ssm.StringParameter(
            self,
            "rGenAiTriviaCognitoUserPoolId",
            parameter_name="/genAiTrivia/cognito/userPoolId",
            string_value=self.user_pool.user_pool_id,
        )
        ssm.StringParameter(
            self,
            "rGenAiTriviaCognitoUserPoolClientId",
            parameter_name="/genAiTrivia/cognito/userPoolClientId",
            string_value=user_pool_client.user_pool_client_id,
        )
        ssm.StringParameter(
            self,
            "rGenAiTriviaCognitoIdentityPoolId",
            parameter_name="/genAiTrivia/cognito/identityPoolId",
            string_value=self.identity_pool.identity_pool_id,
        )

    def get_identity_pool_id(self):
        """
        Get the Cognito identity pool ID.

        Returns:
            str: The Cognito identity pool ID.
        """
        return self.identity_pool.identity_pool_id
