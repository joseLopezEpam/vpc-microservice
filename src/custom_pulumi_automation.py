import logging
from pulumi.automation import (
    create_or_select_stack,
    ConcurrentUpdateError,
    StackAlreadyExistsError,
)

from vpc_stack import create_vpc_resources

logger = logging.getLogger(__name__)

def provision_vpc(project_name: str, stack_name: str, config: dict) -> dict:
    """
    Provisions a VPC using Pulumi Automation API.
    :param project_name: Pulumi project name
    :param stack_name: Stack name (e.g., "dev")
    :param config: Configuration dictionary for the VPC
    :return: Outputs from the Pulumi stack execution
    """
    try:
        # Validar que vengan los campos básicos
        required_keys = ["vpc_cidr", "num_public_subnets", "num_private_subnets"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required config parameter: '{key}'")

        logger.info(f"Configuration received for provision_vpc: {config}")

        def pulumi_program():
            create_vpc_resources(config)

        logger.info(f"Creating or selecting stack '{stack_name}' for project '{project_name}'...")
        stack = create_or_select_stack(
            project_name=project_name,
            stack_name=stack_name,
            program=pulumi_program,
        )

        logger.info("Installing AWS plugin for Pulumi...")
        stack.workspace.install_plugin("aws", "v6.66.0")

        logger.info("Executing 'pulumi up'...")
        up_res = stack.up(on_output=print)

        if not up_res.outputs:
            logger.warning("'pulumi up' completed but no outputs were generated.")
        else:
            logger.info("Outputs from 'pulumi up':")
            for key, output_value in up_res.outputs.items():
                logger.info(f"  {key}: {output_value.value}")

        return up_res.outputs

    except ConcurrentUpdateError as e:
        logger.error("Concurrent update detected: another Pulumi operation is in progress.", exc_info=True)
        raise
    except StackAlreadyExistsError as e:
        logger.error(f"Stack already exists but encountered an error: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Pulumi provisioning: {e}", exc_info=True)
        raise
