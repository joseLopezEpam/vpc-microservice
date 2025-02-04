import logging
import json
import boto3
import os
from botocore.exceptions import ClientError
from custom_pulumi_automation import provision_vpcs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
SQS_URL = os.getenv("SQS_URL")

logger.info(f"AWS_REGION: {AWS_REGION}")
logger.info(f"SQS_URL: {SQS_URL}")

sqs_client = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def test_sqs_connection():
    """Tests the connection to SQS."""
    try:
        sqs_client.get_queue_attributes(QueueUrl=SQS_URL, AttributeNames=["All"])
        logger.info("SQS connection successful.")
    except ClientError as e:
        logger.error(f"Error testing SQS connection: {e}")
        raise

def process_messages(messages):
    """
    Processes multiple messages from the SQS queue.
    Creates a list of VPCs and sends them together to Pulumi.
    """
    vpcs_to_create = []

    for message in messages:
        try:
            raw_body = message["Body"]
            logger.info(f"raw_body: {raw_body}")
            body = json.loads(raw_body)

            vpc_name = body.get("VpcName", "default-vpc")
            vpc_config = {
                "vpc_cidr": body.get("CidrBlock", "10.0.0.0/16"),
                "num_public_subnets": body.get("NumPublicSubnets", 2),
                "num_private_subnets": body.get("NumPrivateSubnets", 2),
                "vpc_name": vpc_name,
                "tags": body.get("Tags", {}),
            }

            logger.info(f"Adding VPC to list: {vpc_name}")
            vpcs_to_create.append(vpc_config)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            continue  # If there is an error with a message, continue with the rest

    if vpcs_to_create:
        logger.info(f"Sending {len(vpcs_to_create)} VPCs to Pulumi...")
        outputs = provision_vpcs(vpcs_to_create)
        logger.info(f"Provisioned VPC outputs: {outputs}")

def poll_sqs():
    """Continuously polls the SQS queue and processes multiple messages."""
    while True:
        response = sqs_client.receive_message(
            QueueUrl=SQS_URL,
            MaxNumberOfMessages=10,  
            WaitTimeSeconds=10,
        )

        if "Messages" in response:
            logger.info(f"Received {len(response['Messages'])} messages from SQS.")
            process_messages(response["Messages"])

            for message in response["Messages"]:
                sqs_client.delete_message(QueueUrl=SQS_URL, ReceiptHandle=message["ReceiptHandle"])
                logger.info(f"Deleted message {message['MessageId']} from SQS.")

if __name__ == "__main__":
    logger.info("Initializing VPC Microservice...")
    test_sqs_connection()
    logger.info("Starting SQS polling loop...")
    poll_sqs()
