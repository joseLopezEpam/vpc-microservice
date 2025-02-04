import logging
import os
import pulumi
from pulumi.automation import (
    create_or_select_stack,
    ConfigValue,
    ConcurrentUpdateError,
    StackAlreadyExistsError,
)
from vpc_stack import create_vpc_resources

logger = logging.getLogger(__name__)

# Retrieve AWS credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# Define the stack name that will manage multiple VPCs
STACK_NAME = "my-vpc-stack"
PROJECT_NAME = "multi-vpc-project"

def pulumi_program(vpcs_to_create):
    """
    Pulumi program that provisions multiple VPCs within a single stack.
    """
    logger.info(f"Provisioning {len(vpcs_to_create)} VPC(s) in the same stack.")
    for vpc_config in vpcs_to_create:
        create_vpc_resources(vpc_config)  # Add each VPC to the stack

def provision_vpcs(vpcs_to_create):
    """
    Provisions multiple VPCs in a single Pulumi stack.
    """
    try:
        # Create or select the single stack
        stack = create_or_select_stack(
            project_name=PROJECT_NAME,
            stack_name=STACK_NAME,
            program=lambda: pulumi_program(vpcs_to_create),
        )

        stack.workspace.install_plugin("aws", "v6.66.0")

        # Configure Pulumi with AWS credentials
        stack.set_config("aws:region", ConfigValue(value=AWS_REGION))
        stack.set_config("aws:accessKey", ConfigValue(value=AWS_ACCESS_KEY_ID))
        stack.set_config("aws:secretKey", ConfigValue(value=AWS_SECRET_ACCESS_KEY))

        # Synchronize the stack state
        stack.refresh(on_output=print)

        # Execute Pulumi to apply the changes
        up_res = stack.up(on_output=print)

        return up_res.outputs

    except ConcurrentUpdateError:
        logger.error("Concurrent update detected.", exc_info=True)
        raise
    except StackAlreadyExistsError:
        logger.error("Stack already exists but encountered an error.", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Pulumi provisioning: {e}", exc_info=True)
        raise
