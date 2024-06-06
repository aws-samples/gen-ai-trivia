# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# !/usr/bin/env python3

import yaml
import os
import aws_cdk as cdk
from pipeline.pipeline_stack import PipelineStack
from app.s3_artifact_deployment import S3ArtifactDeployment

# Get data from config file and convert to dict
config_file_path = "./configs/deploy-config.yaml"
with open(config_file_path, "r", encoding="utf-8") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

app = cdk.App()

# Pipeline Stack
PipelineStack(
    app,
    config["deployInfrastructure"]["cloudformation"]["stackName"],
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
    config=config,
)

S3ArtifactDeployment(
    app,
    config["appInfrastructure"]["productName"] + "-s3-artifact-deployment",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    )
)

app.synth()
