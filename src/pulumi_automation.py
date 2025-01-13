import logging
import pulumi_automation as auto

from vpc_stack import create_vpc_resources

logger = logging.getLogger(__name__)

def provision_vpc(project_name: str, stack_name: str, config: dict):
    """
    Crea o selecciona un stack de Pulumi, le pasa la configuración y hace un pulumi up.
    :param project_name: Nombre del proyecto Pulumi
    :param stack_name: Nombre del stack (p.e. "dev")
    :param config: Diccionario de configuración para crear la VPC
    :return: Resultado del up() con los outputs
    """
    try:
        # Validar configuración inicial
        if not config.get("vpc_cidr"):
            raise ValueError("El parámetro 'vpc_cidr' es obligatorio en la configuración.")

        if config.get("num_public_subnets", 0) <= 0:
            raise ValueError("Debe haber al menos una subnet pública.")

        if config.get("num_private_subnets", 0) <= 0:
            raise ValueError("Debe haber al menos una subnet privada.")

        logger.info(f"Configuración recibida en provision_vpc: {config}")

        # Definimos la función 'program' que Pulumi ejecutará
        def pulumi_program():
            create_vpc_resources(config)

        # Creamos o seleccionamos el stack
        logger.info(f"Creando o seleccionando el stack '{stack_name}' en el proyecto '{project_name}'...")
        stack = auto.create_or_select_stack(
            project_name=project_name,
            stack_name=stack_name,
            program=pulumi_program
        )

        # Instalamos el plugin de AWS para Pulumi (versión 5.20.0)
        logger.info("Instalando plugin de AWS para Pulumi...")
        stack.workspace.install_plugin("aws", "v5.20.0")

        logger.info("Ejecutando 'pulumi up'...")
        up_res = stack.up(on_output=print)

        # Validamos y mostramos los outputs
        if not up_res.outputs:
            logger.warning("'pulumi up' se completó pero no generó outputs.")
        else:
            logger.info("Outputs generados por 'pulumi up':")
            for key, value in up_res.outputs.items():
                logger.info(f"  {key}: {value['value']}")

        return up_res.outputs

    except auto.exceptions.ConcurrentUpdateError as e:
        logger.error(f"Otro proceso de Pulumi está actualizando el stack: {e}", exc_info=True)
        raise
    except auto.exceptions.StackAlreadyExistsError as e:
        logger.error(f"El stack ya existe pero ocurrió un problema: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Ocurrió un error inesperado en Pulumi: {e}", exc_info=True)
        raise
