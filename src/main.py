import logging
import json
import boto3
import os
from botocore.exceptions import ClientError
from custom_pulumi_automation import provision_vpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration (from environment variables)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SQS_URL = os.getenv("SQS_URL")

if not SQS_URL:
    logger.error("SQS_URL environment variable is not set. Exiting...")
    raise EnvironmentError("SQS_URL environment variable is required.")

# SQS client
sqs_client = boto3.client("sqs", region_name=AWS_REGION)

def test_sqs_connection():
    try:
        sqs_client.get_queue_attributes(QueueUrl=SQS_URL, AttributeNames=["All"])
        logger.info("SQS connection successful.")
    except ClientError as e:
        logger.error(f"Error testing SQS connection: {e}")
        raise

def process_message(message):
    try:
        raw_body = message["Body"]
        logger.info(f"raw_body: {raw_body}")
        body = json.loads(raw_body)

        vpc_config = {
            "vpc_cidr": body.get("CidrBlock", "10.0.0.0/16"),
            "num_public_subnets": body.get("NumPublicSubnets", 2),
            "num_private_subnets": body.get("NumPrivateSubnets", 2),
            "vpc_name": body.get("VpcName", "default-vpc"),
            "tags": body.get("Tags", {}),
        }

        logger.info(f"Provisioning VPC for project: {body.get('ProjectName')}")
        logger.info(f"Final VPC configuration: {vpc_config}")

        outputs = provision_vpc("my-pulumi-project", "dev", vpc_config)
        logger.info(f"Provisioned VPC outputs: {outputs}")
    except Exception as e:
        logger.error(f"Error during message processing: {e}")
        raise

def poll_sqs():
    while True:
        response = sqs_client.receive_message(
            QueueUrl=SQS_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10,
        )
        if "Messages" in response:
            for message in response["Messages"]:
                logger.info(f"SQS receive_message response: {response}")
                process_message(message)
                sqs_client.delete_message(QueueUrl=SQS_URL, ReceiptHandle=message["ReceiptHandle"])
                logger.info("Message processed and deleted from the queue.")

if __name__ == "__main__":
    logger.info("Initializing VPC Microservice...")
    logger.info(f"AWS_REGION: {AWS_REGION}")
    logger.info(f"SQS_URL: {SQS_URL}")

    test_sqs_connection()
    logger.info("Starting SQS polling loop...")
    poll_sqs()
