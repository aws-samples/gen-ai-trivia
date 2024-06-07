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
    aws_codecommit as codecommit,
    aws_iam as iam,
    aws_s3 as s3
)
from cdk_nag import NagSuppressions, AwsSolutionsChecks
from pipeline.pipeline_helper import create_archive, replace_ssm_in_config
from pipeline.pipeline_app_stage import PipelineAppStage


class PipelineStack(Stack):
    """
    A CDK Stack that creates a CodeCommit repository and a CodePipeline pipeline.
    """

    def create_repository(self, config: dict):
        """
        Create a CodeCommit repository from a configuration.

        Args:
            config (dict): The configuration dictionary containing the repository details.

        Returns:
            codecommit.Repository: The created CodeCommit repository object.

        This method creates a CodeCommit repository based on the provided configuration dictionary.
        If the configuration specifies a CodeCommit repository, it creates a ZIP archive containing
        the code and initializes the repository with the contents of the archive.
        """
        if config["deployInfrastructure"].get("codecommit"):
            # Create a zip file to all CodeCommit to import
            archive_file = create_archive(config=config)

            repository_name = config["deployInfrastructure"]["codecommit"][
                "repositoryName"
            ]
            repository = codecommit.Repository(
                self,
                "rCodeCommitRepository",
                repository_name=repository_name,
                description=f"This is the {repository_name} repository",
                code=codecommit.Code.from_zip_file(
                    file_path=archive_file,
                    branch=config["deployInfrastructure"]["codecommit"][
                        "repositoryBranch"
                    ]
                )
            )

            return repository

    def create_pipeline(self, repository, config: dict):
        """
        Create a CodePipeline pipeline.

        Args:
            repository (codecommit.Repository): The CodeCommit repository to use as the source.
            config (dict): The configuration dictionary containing the pipeline details.

        Returns:
            pipelines.CodePipeline: The created CodePipeline object.

        This method creates a CodePipeline pipeline with the provided CodeCommit repository as the source.
        The pipeline includes a synth step to build the application and a deployment stage to deploy the
        infrastructure and the web application.
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
                    "reason": "The S3 Bucket has server access logs disabled.",
                }
            ]
        )

        # Create a Pipeline
        source = pipelines.CodePipelineSource.code_commit(repository, "main")
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

        # Replace SSM Parameters within config file
        config = replace_ssm_in_config(scope=self, temp_config=config)

        # CodeCommit Setup
        i_repository = self.create_repository(config=config)

        # CodePipeline Setup
        self.create_pipeline(repository=i_repository, config=config)

        # Add tags to all resources created
        tags = json.loads(json.dumps(config["tags"]))
        for key, value in tags.items():
            Tags.of(self).add(key, value)

        Aspects.of(self).add(AwsSolutionsChecks())
