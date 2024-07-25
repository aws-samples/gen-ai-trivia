# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import aws_dynamodb as dynamodb, RemovalPolicy


def create_dynamodb(
    scope, table_name: str, pit_recovery: bool = True
) -> dynamodb.ITable:
    """
    Create a DynamoDB table.

    Args:
        scope (Construct): The scope in which to define this construct.
        table_name (str): Desired DynamoDB Table name.
        pit_recovery (bool, optional): Enable Point in Time Recovery. Defaults to True.

    Returns:
        dynamodb.ITable: CDK Interface for created DynamoDB Table
    """

    table = dynamodb.Table(
        scope,
        f"rGenAiTriviaDynamoDBTable{table_name.title().replace('/','')}",
        table_name=table_name,
        partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
        sort_key=dynamodb.Attribute(name="score", type=dynamodb.AttributeType.NUMBER),
        point_in_time_recovery=pit_recovery,
        removal_policy=RemovalPolicy.DESTROY,
    )

    table.add_global_secondary_index(
        index_name="sortedScores",
        partition_key=dynamodb.Attribute(
            name="sortID", type=dynamodb.AttributeType.NUMBER
        ),
        sort_key=dynamodb.Attribute(name="score", type=dynamodb.AttributeType.NUMBER),
    )

    return table
