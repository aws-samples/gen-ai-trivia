# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import os
import tempfile
import shutil
import fileinput
from pathlib import Path
from aws_cdk import SecretValue, aws_ssm as ssm


def get_secret_value(secrets_name: str):
    """Retrieves the value of a secret from AWS Secrets Manager.

    Args:
        secrets_name (str): The name of the secret. Can be the secret ID
            or a JSON field in the format "secret_id.json_field".

    Returns:
        str: The value of the secret.

    This function retrieves secrets stored in AWS Secrets Manager. It handles
    both cases where secrets_name is just the secret ID, and where it contains
    the secret ID and JSON field separated by a period. The secret value is
    returned after retrieving it from Secrets Manager.
    """
    if len(secrets_name.split(".")) == 1:
        _value = SecretValue.secrets_manager(secret_id=secrets_name).to_string()

    if len(secrets_name.split(".")) > 1:
        _secrets_id = secrets_name.split(".")[0]
        _secret_json = secrets_name.split(".")[1]
        _value = SecretValue.secrets_manager(
            secret_id=_secrets_id, json_field=_secret_json
        ).to_string()

    return _value


def get_ssm_value(scope, parameter_name: str):
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
    _value = ssm.StringParameter.value_from_lookup(scope, parameter_name)
    if "dummy-value" in _value and "arn" in _value.lower():
        return "arn:aws:service:us-east-1:123456789012:entity/dummy-value"
    if "dummy-value" in _value:
        return "dummy-value"

    return _value


def replace_ssm_in_config(scope, temp_config: dict) -> dict:
    """Replaces SSM and secret values in a configuration dictionary.

    Args:
        scope (cdk.Construct): The construct scope.
        temp_config (dict): The configuration dictionary.

    Returns:
        dict: The updated configuration dictionary with SSM and secret values replaced.

    This function recursively searches the configuration dictionary for strings
    containing "SSM:" or "SECRET:". These values are replaced by calling
    get_ssm_value() or get_secret_value() respectively. The configuration is
    searched at all dictionary levels to support nested structures. The updated
    configuration is returned.
    """
    for key1, val1 in temp_config.items():
        if isinstance(val1, str) and "SSM:" in val1:
            temp_config[key1] = get_ssm_value(
                scope, parameter_name=val1.replace("SSM:", "")
            )

        if isinstance(val1, str) and "SECRET:" in val1:
            temp_config[key1] = get_secret_value(
                secrets_name=val1.replace("SECRET:", "")
            )

        if isinstance(val1, dict):
            for key2, val2 in val1.items():
                if isinstance(val2, str) and "SSM:" in val2:
                    temp_config[key1][key2] = get_ssm_value(
                        scope, parameter_name=val2.replace("SSM:", "")
                    )

                if isinstance(val2, str) and "SECRET:" in val2:
                    temp_config[key1][key2] = get_secret_value(
                        secrets_name=val2.replace("SECRET:", "")
                    )

                if isinstance(val2, dict):
                    for key3, val3 in val2.items():
                        if isinstance(val3, str) and "SSM:" in val3:
                            temp_config[key1][key2][key3] = get_ssm_value(
                                scope, parameter_name=val3.replace("SSM:", "")
                            )

                        if isinstance(val3, str) and "SECRET:" in val3:
                            temp_config[key1][key2][key3] = get_secret_value(
                                secrets_name=val3.replace("SECRET:", "")
                            )

        if isinstance(val1, list):
            count = 0
            for _val1 in val1:
                for key2, val2 in _val1.items():
                    if isinstance(val2, str) and "SSM:" in val2:
                        temp_config[key1][count][key2] = get_ssm_value(
                            scope, parameter_name=val2.replace("SSM:", "")
                        )

                    if isinstance(val2, str) and "SECRET:" in val2:
                        temp_config[key1][count][key2] = get_secret_value(
                            secrets_name=val1.replace("SECRET:", "")
                        )

                count = count + 1

    return temp_config


def update_config(existing_config: dict, account_info) -> dict:
    """Updates an existing configuration dictionary with account info.

    Args:
        existing_config (dict): The existing configuration dictionary.
        account_info (str): A JSON string containing account info.

    Returns:
        dict: The updated configuration dictionary.

    This function takes an existing configuration dictionary and account
    information as a JSON string. It loads the account info JSON and iterates
    through the key-value pairs. If the key is "deploy", it updates the
    "deploymentAccount" in the config. Otherwise it finds the matching SDLC
    account by name and updates its "awsAccount". The updated configuration
    is returned.
    """
    acc_info = json.loads(account_info)
    for key, value in acc_info.items():
        if key.lower() == "deploy":
            existing_config["deploymentAccount"].update({"awsAccount": value})
        else:
            for sdlc_acc in existing_config["sdlcAccounts"]:
                if sdlc_acc["name"] == key:
                    sdlc_acc.update({"awsAccount": value})

    return existing_config


def create_archive(config: dict = {}, zip_name="zip_file") -> str:
    """Creates a zip archive of files from a configuration.

    Args:
        config (dict, optional): Configuration dictionary. Defaults to empty dict.
        zip_name (str, optional): Name of the zip file. Defaults to 'zip_file'.

    Returns:
        str: Path to the created zip file.

    This function creates a temporary directory and copies files from the
    project root directory into it, ignoring any files/directories specified
    in the 'codecommit' configuration. It then searches for and replaces any
    strings specified in the 'fileReplacement' config. Finally, it zips the
    contents of the temporary directory and returns the path to the created
    zip archive.
    """
    # Setting up array with a None value
    ignored_files_directories = config["deployInfrastructure"]["codecommit"].get(
        "ignoreFilesDirectoriesCodeCommit", []
    )

    # Adding standard ignored files/directories to variable
    ignored_files_directories.extend(
        (
            "__pycache__",
            "cdk.out",
            ".git",
            ".DS_Store",
            ".venv",
            ".python-version",
            "dist",
            "node_modules",
        )
    )

    root_dir = Path(__file__).parents[1]
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a copy of the directory
        shutil.copytree(
            root_dir,
            os.path.join(tmpdir, zip_name),
            # UPDATE this section if there are additional pattern that need to be ignored
            ignore=shutil.ignore_patterns(*ignored_files_directories),
        )

        for item in config["deployInfrastructure"]["codecommit"].get(
            "fileReplacement", []
        ):
            file_string_replacement(
                filename=f"{os.path.join(tmpdir, zip_name)}/{item['filename']}",
                search_str=item["search_str"],
                replace_str=item["replace_str"],
            )

        # Create Zip File
        shutil.make_archive(
            os.path.join("cdk.out/", zip_name), "zip", os.path.join(tmpdir, zip_name)
        )

    return os.path.join("cdk.out/", zip_name + ".zip")


def file_string_replacement(filename: str, search_str: str, replace_str: str) -> None:
    """
    Replace a string in a file.

    Args:
        filename (str): The path to the file to modify.
        search_str (str): The string to search for.
        replace_str (str): The string to replace matches with.

    Returns:
        None
    
    This function replaces all occurrences of search_str with replace_str
    in the given filename. It uses fileinput.FileInput to open the file
    in-place, iterates through each line, and prints it after replacing
    the search string. This has the effect of modifying the file contents
    directly.
    """
    with fileinput.FileInput(filename, inplace=True, backup="") as file:
        for line in file:
            print(line.replace(search_str, replace_str), end="")
