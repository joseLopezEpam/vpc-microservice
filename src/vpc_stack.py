import logging
import pulumi
import pulumi_aws as aws

logger = logging.getLogger(__name__)

def create_vpc_resources(config: dict):
    """
    Creates a VPC with subnets, NAT gateway, and route tables.
    
    Expects in config:
      - config["vpc_cidr"] (str)
      - config["num_public_subnets"] (int)
      - config["num_private_subnets"] (int)
      - config["vpc_name"] (str)
      - config["tags"] (dict)
    """
    logger.info(f"Creating VPC resources with config: {config}")

    vpc_cidr = config["vpc_cidr"]
    vpc_name = config["vpc_name"]
    num_public_subnets = config["num_public_subnets"]
    num_private_subnets = config["num_private_subnets"]
    tags = config["tags"]

    # 1. Crear VPC
    vpc = aws.ec2.Vpc(
    resource_name=f"vpc-{vpc_name}",  # <-- Dinámico
    cidr_block=vpc_cidr,
    tags={
        "Name": vpc_name,  # El tag "Name" es distinto al resource_name
        **tags
    }
)

    # 2. Internet Gateway
    igw = aws.ec2.InternetGateway(
        resource_name="my-igw",
        vpc_id=vpc.id,
        tags={
            "Name": f"{vpc_name}-igw",
            **tags
        }
    )

    # 3. Crear Subnets
    public_subnets = []
    for i in range(num_public_subnets):
        subnet = aws.ec2.Subnet(
            f"public-subnet-{i}",
            vpc_id=vpc.id,
            cidr_block=f"10.1.{i}.0/24",
            tags={
                "Name": f"{vpc_name}-public-subnet-{i}",
                "Type": "public",
                **tags
            }
        )
        public_subnets.append(subnet)

    private_subnets = []
    for i in range(num_private_subnets):
        subnet = aws.ec2.Subnet(
            f"private-subnet-{i}",
            vpc_id=vpc.id,
            cidr_block=f"10.1.{i+10}.0/24",
            tags={
                "Name": f"{vpc_name}-private-subnet-{i}",
                "Type": "private",
                **tags
            }
        )
        private_subnets.append(subnet)

    # 4. NAT Gateway
    eip = aws.ec2.Eip(
        "nat-eip",
        vpc=True,
        tags={
            "Name": f"{vpc_name}-nat-eip",
            **tags
        }
    )

    nat_gw = aws.ec2.NatGateway(
        "my-nat-gw",
        allocation_id=eip.id,
        subnet_id=public_subnets[0].id if public_subnets else None,
        tags={
            "Name": f"{vpc_name}-nat-gw",
            **tags
        }
    )

    # 5. Route Tables
    public_rt = aws.ec2.RouteTable(
        "public-rt",
        vpc_id=vpc.id,
        tags={
            "Name": f"{vpc_name}-public-rt",
            **tags
        }
    )

    aws.ec2.Route(
        "public-default-route",
        route_table_id=public_rt.id,
        gateway_id=igw.id,
        cidr_block="0.0.0.0/0"
    )

    private_rt = aws.ec2.RouteTable(
        "private-rt",
        vpc_id=vpc.id,
        tags={
            "Name": f"{vpc_name}-private-rt",
            **tags
        }
    )

    aws.ec2.Route(
        "private-default-route",
        route_table_id=private_rt.id,
        nat_gateway_id=nat_gw.id,
        cidr_block="0.0.0.0/0"
    )

    for i, subnet in enumerate(public_subnets):
        aws.ec2.RouteTableAssociation(
            f"public-rt-assoc-{i}",
            route_table_id=public_rt.id,
            subnet_id=subnet.id
        )

    for i, subnet in enumerate(private_subnets):
        aws.ec2.RouteTableAssociation(
            f"private-rt-assoc-{i}",
            route_table_id=private_rt.id,
            subnet_id=subnet.id
        )

    # 6. Exports de Pulumi
    pulumi.export("vpc_id", vpc.id)
    pulumi.export("vpc_cidr", vpc.cidr_block)
    pulumi.export("igw_id", igw.id)
    pulumi.export("nat_gw_id", nat_gw.id)

    for i, subnet in enumerate(public_subnets):
        pulumi.export(f"public_subnet_{i}_id", subnet.id)
    for i, subnet in enumerate(private_subnets):
        pulumi.export(f"private_subnet_{i}_id", subnet.id)

    logger.info("VPC, subnets, NAT gateway, and route tables have been successfully created.")
