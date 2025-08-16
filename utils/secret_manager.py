# In file: utils/secrets_manager.py

import boto3
import json
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# This is more efficient than creating a new client on every function call
_secrets_client = None

def get_secret(secret_name: str) -> dict | str:
    """
    Retrieves a secret from AWS Secrets Manager.

    This function is optimized to reuse the boto3 client and can handle
    both plain string secrets and JSON secrets automatically.

    Args:
        secret_name (str): The name or ARN of the secret to retrieve.

    Returns:
        dict | str: The secret value. If the secret is a JSON string,
                    it returns a dictionary. Otherwise, it returns a raw string.
    """
    global _secrets_client
    if _secrets_client is None:
        region_name = os.getenv("AWS_REGION")
        if not region_name:
            # Fallback for local development or misconfiguration
            # Lambda provides AWS_REGION automatically
            logger.warning("AWS_REGION environment variable not set. Falling back to 'ap-southeast-2'.")
            region_name = "ap-southeast-2"
        _secrets_client = boto3.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = _secrets_client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.error(f"Couldn't retrieve secret '{secret_name}'. Error: {e}")
        raise e

    # Extract the secret string
    secret_string = get_secret_value_response.get('SecretString')

    if not secret_string:
        logger.error(f"Secret string for '{secret_name}' is empty.")
        # Depending on your use case, you might return None or raise an error
        raise ValueError(f"Secret '{secret_name}' has no SecretString.")

    # Try to parse it as JSON, if it fails, return the raw string
    try:
        return json.loads(secret_string)
    except json.JSONDecodeError:
        return secret_string