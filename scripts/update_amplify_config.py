# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3


def get_cognito_param_values() -> list[str]:
    """
    Retrieve the values of the Cognito user pool ID, user pool client ID,
    and identity pool ID from AWS Systems Manager Parameter Store.

    Returns:
        list[str]: A list containing the user pool ID, user pool client ID, and identity pool ID.
    """
    client = boto3.client("ssm")
    user_pool_id = client.get_parameter(Name="/genAiTrivia/cognito/userPoolId")["Parameter"]["Value"]
    user_pool_client_id = client.get_parameter(Name="/genAiTrivia/cognito/userPoolClientId")["Parameter"]["Value"]
    identity_pool_id = client.get_parameter(Name="/genAiTrivia/cognito/identityPoolId")["Parameter"]["Value"]
    return user_pool_id, user_pool_client_id, identity_pool_id



def main() -> None:
    """
    Write the Cognito user pool ID, user pool client ID, and
    identity pool ID to the Amplify configuration file.

    Returns:
        None
    """
    with open(
        "www/src/amplifyconfiguration.json", "w+", encoding="UTF-8"
    ) as amp_config:
        user_pool_id, user_pool_client_id, identity_pool_id = get_cognito_param_values()
        data = {
            "Auth": {
                "Cognito": {
                    "userPoolId": user_pool_id,
                    "userPoolClientId": user_pool_client_id,
                    "identityPoolId": identity_pool_id,
                }
            }
        }
        json.dump(data, amp_config)


if __name__ == "__main__":
    main()
