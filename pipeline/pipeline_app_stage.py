# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from constructs import Construct
from aws_cdk import Stage
from app.app_stack import ApplicationStack


class PipelineAppStage(Stage):
    """
    Application stage for the CDK pipeline.

    This class represents a stage in the CDK pipeline that deploys the
    application stack.

    Attributes:
        app_stack (ApplicationStack): The application stack instance.
    """

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        """
        Initialize the PipelineAppStage.
        
        Args:
            scope (Construct): The parent of this stage, usually an App or a Stage, but could be any construct.
            construct_id (str): The identifier of this stage. Must be unique within this scope.
            config (dict): Application configuration.  
            **kwargs: Other parameters passed to the base class.
        """
        super().__init__(scope, construct_id, **kwargs)

        ApplicationStack(
            self, config['appInfrastructure']['productName'],
            stack_name=config['appInfrastructure']['cloudformation']['stackName'],
            config=config
        )
