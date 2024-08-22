# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import tempfile
import logging
import shutil
from pathlib import Path
import yaml
import boto3

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)
logger.info("Starting...")


def create_archive(config: dict, zip_name="source") -> str:
    """
    Create an archive of the source code, excluding specified files and directories.

    Args:
        config (dict): Application configuration.
        zip_name (str): The name of the zip archive (default: "source").

    Returns:
        str: The full path of the created archive file.

    The function creates a temporary directory, copies the source code into it
    (excluding specified files and directories), creates a zip archive of the
    temporary directory, and returns the full path of the created archive file.
    """
    logger.info("Creating archive")
    # Setting up array with a None value
    ignored_files_directories = config["deployInfrastructure"]['sourceCode'].get(
        "ignoreFilesDirectories", []
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
    logger.info("Ignoring the following in archive file %s", ignored_files_directories)

    root_dir = Path(__file__).parents[1]
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a copy of the directory
        shutil.copytree(
            root_dir,
            os.path.join(tmpdir, zip_name),
            ignore=shutil.ignore_patterns(*ignored_files_directories),
        )
        # Create Zip File
        shutil.make_archive(
            os.path.join(zip_name), "zip", os.path.join(tmpdir, zip_name)
        )

    arch_file_path = os.path.join(tmpdir, zip_name + ".zip")
    logger.info("Archive Path: %s", arch_file_path)
    return arch_file_path


if __name__ == "__main__":
    # Main function to upload the source code archive to the pipeline source S3 bucket.

    # The function reads the application configuration, creates a source code archive using
    # create_archive(), and uploads the archive to the specified S3 bucket.

    # It handles any exceptions and logs appropriate messages.

    # The function reads the application configuration, creates a source code archive using
    # create_archive(), and uploads the archive to the specified S3 bucket.

    # It handles any exceptions and logs appropriate messages.
    s3_client = boto3.client("s3")

    try:
        CONFIG_FILE_PATH = "./configs/deploy-config.yaml"
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            deploy_config = yaml.load(f, Loader=yaml.SafeLoader)

        archive_file_path = create_archive(config=deploy_config)
        archive_file_name = archive_file_path.split("/")[-1]

        src_bucket_prefix = deploy_config['deployInfrastructure']['codepipeline']['sourceBucketPrefix']

        buckets = s3_client.list_buckets()
        for bucket in buckets['Buckets']:
            if src_bucket_prefix in bucket['Name']:
                src_bucket_name = bucket['Name']
                logger.info("Uploading %s to %s", archive_file_name, src_bucket_name)
                response = s3_client.upload_file(
                    Filename=archive_file_name,
                    Bucket=src_bucket_name,
                    Key=archive_file_name
                )

    except Exception as e:
        logger.error("Error: %s", e)
        raise e
