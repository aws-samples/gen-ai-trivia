# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import json
from constructs import Construct
from aws_cdk import (
    Stack,
    Aws,
    Aspects,
    Environment,
    Tags,
    RemovalPolicy,
    pipelines,
    aws_iam as iam,
    aws_s3 as s3,
    aws_codepipeline_actions as codepipeline_actions
)
from cdk_nag import NagSuppressions, AwsSolutionsChecks
from pipeline.pipeline_app_stage import PipelineAppStage


class PipelineStack(Stack):
    """
    CDK Stack for the deployment pipeline.

    This stack sets up the CodePipeline for building and deploying the application.
    It includes the source, build, and deployment stages, along with necessary resources
    such as S3 buckets and IAM roles.
    """

    def create_pipeline_source_bucket(self, config: dict):
        """
        Creates an S3 bucket for uploading the source code archive.

        Args:
            config (dict): The application configuration.
            
        Returns:
            s3.Bucket: The created S3 bucket.
        """
        # Get current stack name
        stack = Stack.of(self)
        region = stack.region
        account = stack.account

        # Create CodePipeline Source Bucket
        src_bucket_name = f"{config['deployInfrastructure']['codepipeline']['sourceBucketPrefix']}-{region}-{account}"
        self.source_bucket = s3.Bucket(
            self,
            "rGenAiTriviaSourceS3Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            bucket_name=src_bucket_name,
            enforce_ssl=True,
            versioned=True
        )

        NagSuppressions.add_resource_suppressions(
            self.source_bucket,
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "The S3 Bucket has server access logs disabled."
                }
            ]
        )

        return self.source_bucket

    def create_pipeline(self, config: dict):
        """
        Creates the CodePipeline for building and deploying the application.

        Args:
            config (dict): The application configuration.
            
        The pipeline includes the source, build, and deployment stages, along with 
        necessary resources such as S3 buckets and IAM roles.
        """
        # Get current stack name
        stack_name = Aws.STACK_NAME
        stack = Stack.of(self)
        region = stack.region
        account = stack.account

        # Create an S3 bucket CodePipeline Artifacts
        self.pipeline_bucket = s3.Bucket(
            self,
            "rGenAiTriviaPipelineS3Bucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            bucket_name=f"gen-ai-trivia-pipeline-{region}-{account}",
            enforce_ssl=True
        )

        NagSuppressions.add_resource_suppressions(
            self.pipeline_bucket,
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "The S3 Bucket has server access logs disabled."
                }
            ]
        )

        # Create a Pipeline
        source = pipelines.CodePipelineSource.s3(
            bucket=self.source_bucket,
            object_key="source.zip",
            action_name="Source",
            trigger=codepipeline_actions.S3Trigger.EVENTS
        )
        pipeline_name = config["deployInfrastructure"]["codepipeline"]["pipelineName"]
        deployment_pipeline = pipelines.CodePipeline(
            self,
            "rCodePipeline",
            pipeline_name=pipeline_name,
            artifact_bucket=self.pipeline_bucket,
            docker_enabled_for_self_mutation=True,
            docker_enabled_for_synth=True,
            enable_key_rotation=True,
            cross_account_keys=True,
            code_build_defaults=pipelines.CodeBuildOptions(
                role_policy=[
                    iam.PolicyStatement(
                        actions=[
                            "cloudformation:ListStacks", 
                            "ssm:GetParameter"
                        ],
                        resources=["*"],
                        effect=iam.Effect.ALLOW
                    )
                ],
                build_environment={"privileged": True}
            ),
            synth=pipelines.ShellStep(
                "Synth",
                input=source,
                commands=[
                    "cd www && npm ci && npm run build && cd ..",
                    "npm install -g aws-cdk",
                    "python -m pip install -r requirements.txt",
                    f'cdk synth {stack_name}'
                ]
            )
        )

        # Deployment Stage
        deployment_pipeline.add_stage(
            PipelineAppStage(
                self,
                "Deployment-Infrastructure",
                env=Environment(
                    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
                    region=os.getenv("CDK_DEFAULT_REGION")
                ),
                config=config
            ),
            # Have to do this as a post step because cognito ids are synthed tokens in the asset otherwise
            post=[
                pipelines.CodeBuildStep(
                    "Deploy-WebApp",
                    input=source,
                    commands=[
                        "python scripts/update_amplify_config.py",
                        "cat www/src/amplifyconfiguration.json",
                        "cd www && npm ci && npm run build && cd ..",
                        "npm install -g aws-cdk",
                        "python -m pip install -r requirements.txt",
                        f'cdk synth {config["appInfrastructure"]["productName"]}-s3-artifact-deployment',
                        f'cdk deploy {config["appInfrastructure"]["productName"]}-s3-artifact-deployment --require-approval never'
                    ],
                    role_policy_statements=[
                        iam.PolicyStatement(
                            actions=["sts:AssumeRole"],
                            resources=[f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/cdk-*"],
                            effect=iam.Effect.ALLOW
                        )
                    ]
                )
            ]
        )

        # Builds CodePipeline to allow for Suppression
        deployment_pipeline.build_pipeline()

        # Cleanup CodePipeline Artifact Bucket during Cfn Stack Deletion
        pipeline_bucket = deployment_pipeline.pipeline.artifact_bucket
        pipeline_bucket.apply_removal_policy(RemovalPolicy.DESTROY)

        NagSuppressions.add_resource_suppressions(
            deployment_pipeline,
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "The S3 Bucket has server access logs disabled."
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "The IAM entity contains wildcard permissions and does not " \
                        "have a cdk-nag rule suppression with evidence for those permission."
                },
                {
                    "id": "AwsSolutions-CB3",
                    "reason": "The CodeBuild project has privileged mode enabled."
                },
                {
                    "id": "AwsSolutions-CB4",
                    "reason": "The CodeBuild project does not use an AWS KMS key for encryption."
                }
            ],
            apply_to_children=True
        )

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        """
        Initialize the PipelineStack.

        Args:
            scope (Construct): The parent of this stack, usually an App or a Stage, but could be any construct.
            construct_id (str): The identifier of this stack. Must be unique within this scope.
            config (dict): Application configuration.
            **kwargs: Other parameters passed to the base class.
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create Source S3 Bucket
        self.create_pipeline_source_bucket(config=config)

        # CodePipeline Setup
        self.create_pipeline(config=config)

        # Add tags to all resources created
        tags = json.loads(json.dumps(config["tags"]))
        for key, value in tags.items():
            Tags.of(self).add(key, value)

        Aspects.of(self).add(AwsSolutionsChecks())
