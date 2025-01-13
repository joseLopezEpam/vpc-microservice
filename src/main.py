import logging
import os
import json
import time
import boto3

from pulumi_automation import provision_vpc

# Configurar el nivel de logging general de la aplicación
logging.basicConfig(level=logging.INFO)  # Puedes cambiar a DEBUG si requieres más detalle
logger = logging.getLogger(__name__)

logger.info("Iniciando el servicio VPC Microservice...")

logger.info(f"AWS_ACCESS_KEY_ID: {os.environ.get('AWS_ACCESS_KEY_ID')}")
logger.info(f"AWS_REGION: {os.environ.get('AWS_REGION')}")
logger.info(f"SQS_URL: {os.environ.get('SQS_URL')}")

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SQS_URL = os.environ.get("SQS_URL")
if not SQS_URL:
    raise ValueError("La variable de entorno 'SQS_URL' no está configurada.")

# Inicializar cliente SQS con credenciales explícitas
sqs_client = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
)

# Probar conexión a SQS antes de iniciar el loop
try:
    logger.info("Probando conexión a SQS con un receive_message inicial...")
    test_response = sqs_client.receive_message(
        QueueUrl=SQS_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )
    logger.info(f"Respuesta de prueba SQS: {test_response}")
except Exception as e:
    logger.error(f"Error durante la prueba de conexión a SQS: {e}", exc_info=True)
    raise

def process_message(message_body: dict):
    """
    Procesa el mensaje. Por ejemplo, si `Service` incluye "vpc",
    llama a Pulumi para crear la VPC.
    """
    service = message_body.get("Service")
    project_name = message_body.get("ProjectName", "default-project")

    logger.info(f"process_message() -> Service={service}, ProjectName={project_name}")

    if service == "vpc":
        logger.info(f"Creando VPC para el proyecto {project_name}...")
        vpc_config = {
            "vpc_cidr": "10.1.0.0/16",
            "num_public_subnets": 2,
            "num_private_subnets": 2,
        }
        try:
            outputs = provision_vpc(
                project_name="my-pulumi-project",
                stack_name="dev",
                config=vpc_config,
            )
            logger.info("Despliegue completado. Outputs:")
            for k, v in outputs.items():
                logger.info(f"  {k}: {v['value']}")
        except Exception as e:
            logger.error(f"Error al crear la VPC con Pulumi: {e}", exc_info=True)
    else:
        logger.info(f"Service '{service}' no se reconoce o no es 'vpc'. No se crea VPC.")

def main_loop():
    """
    Bucle principal que hace long polling a la cola SQS y procesa mensajes.
    """
    logger.info("Iniciando loop de polling SQS...")

    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=30
            )
            messages = response.get("Messages", [])
            if not messages:
                logger.debug("No hay mensajes en la cola.")
            else:
                for msg in messages:
                    logger.info(f"Mensaje recibido: {msg}")
                    body = json.loads(msg["Body"])
                    process_message(body)

                    # Borrar el mensaje de la cola para que no reaparezca
                    sqs_client.delete_message(
                        QueueUrl=SQS_URL,
                        ReceiptHandle=msg["ReceiptHandle"]
                    )
                    logger.info("Mensaje procesado y borrado de la cola.")
        except Exception as e:
            logger.error(f"Ocurrió un error en main_loop: {e}", exc_info=True)

        time.sleep(5)

if __name__ == "__main__":
    main_loop()
