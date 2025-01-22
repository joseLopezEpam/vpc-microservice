import logging
import os
import json
import time
import boto3

from custom_pulumi_automation import provision_vpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SQS_URL = os.getenv("SQS_URL")

if not SQS_URL:
    raise ValueError("Environment variable 'SQS_URL' is not set.")

logger.info("Initializing VPC Microservice...")
logger.info(f"AWS_REGION: {AWS_REGION}")
logger.info(f"SQS_URL: {SQS_URL}")

# Initialize SQS client
sqs_client = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

# Test SQS connection
try:
    logger.info("Testing SQS connection...")
    sqs_client.receive_message(QueueUrl=SQS_URL, MaxNumberOfMessages=1, WaitTimeSeconds=5)
    logger.info("SQS connection successful.")
except Exception as e:
    logger.error("Failed to connect to SQS.", exc_info=True)
    raise

def process_message(message_body: dict):
    """
    Processes an SQS message that requests a VPC creation.
    Expects fields: 
      - ProjectName (str)
      - Services (list que incluya "vpc")
      - VpcName (str)
      - CidrBlock (str)
      - NumPublicSubnets (int)
      - NumPrivateSubnets (int)
      - Tags (dict)

    Cualquier campo anterior que falte se asigna a un valor válido por defecto.
    """
    logger.info(f"Processing message body: {message_body}")

    project_name = message_body.get("ProjectName", "default-project")
    services = message_body.get("Services", [])

    if "vpc" in services:
        # Asignar valores por defecto válidos en caso de que falten
        vpc_name = message_body.get("VpcName", "default-vpc")
        cidr_block = message_body.get("CidrBlock", "10.0.0.0/16")
        num_public_subnets = message_body.get("NumPublicSubnets", 1)
        num_private_subnets = message_body.get("NumPrivateSubnets", 1)
        tags = message_body.get("Tags", {})

        vpc_config = {
            "vpc_cidr": cidr_block,
            "num_public_subnets": num_public_subnets,
            "num_private_subnets": num_private_subnets,
            "vpc_name": vpc_name,
            "tags": tags
        }

        logger.info(f"Provisionando VPC para el proyecto: {project_name}")
        logger.info(f"Configuración final de la VPC: {vpc_config}")

        try:
            outputs = provision_vpc("my-pulumi-project", "dev", vpc_config)
            logger.info("VPC deployment outputs:")
            for key, output_value in outputs.items():
                logger.info(f"  {key}: {output_value.value}")
        except Exception as e:
            logger.error(f"Error during VPC deployment: {e}", exc_info=True)
    else:
        logger.warning(f"No se encuentra 'vpc' en la lista de servicios: {services}")

def main_loop():
    logger.info("Starting SQS polling loop...")
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=30,
            )

            logger.info(f"SQS receive_message response: {response}")

            messages = response.get("Messages", [])
            if not messages:
                logger.info("No messages found in the queue.")
            else:
                for msg in messages:
                    logger.info(f"Processing SQS message: {msg}")

                    # Simplemente parseamos el body:
                    # (Ya no buscamos "Records", porque tu mensaje NO lo tiene)
                    raw_body = msg["Body"]
                    logger.info(f"raw_body: {raw_body}")

                    message_body = json.loads(raw_body)
                    logger.info(f"message_body parsed: {message_body}")

                    # Procesar
                    process_message(message_body)

                    # Eliminar mensaje de la cola
                    sqs_client.delete_message(QueueUrl=SQS_URL, ReceiptHandle=msg["ReceiptHandle"])
                    logger.info("Message processed and deleted from the queue.")

        except Exception as e:
            logger.error("Error in main loop.", exc_info=True)

        time.sleep(5)

if __name__ == "__main__":
    main_loop()
