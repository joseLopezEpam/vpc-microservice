import logging
import pulumi
import pulumi_aws as aws

logger = logging.getLogger(__name__)

def create_vpc_resources(config: dict):
    """
    Crea un VPC con subnets públicas y privadas, NAT gateway, etc.
    :param config: Diccionario con opciones de configuración (CIDR, num_subnets, etc.)
    """
    logger.info(f"create_vpc_resources() -> config: {config}")

    vpc_cidr = config.get("vpc_cidr", "10.0.0.0/16")
    num_public_subnets = config.get("num_public_subnets", 2)
    num_private_subnets = config.get("num_private_subnets", 2)

    # 1) Crear el VPC
    vpc = aws.ec2.Vpc(
        "my-vpc",
        cidr_block=vpc_cidr,
        tags={"Name": "my-vpc"}
    )

    # 2) Crear una Internet Gateway para subnets públicas
    igw = aws.ec2.InternetGateway(
        "my-igw",
        vpc_id=vpc.id,
        tags={"Name": "my-igw"}
    )

    # 3) Crear subnets públicas
    public_subnets = []
    for i in range(num_public_subnets):
        subnet = aws.ec2.Subnet(
            f"public-subnet-{i}",
            vpc_id=vpc.id,
            cidr_block=f"10.0.{i}.0/24",
            map_public_ip_on_launch=True,
            availability_zone=f"us-east-1{chr(97 + i)}",  # us-east-1a, us-east-1b, etc.
            tags={"Name": f"public-subnet-{i}"}
        )
        public_subnets.append(subnet)

    # 4) Crear subnets privadas
    private_subnets = []
    offset = num_public_subnets
    for i in range(num_private_subnets):
        subnet = aws.ec2.Subnet(
            f"private-subnet-{i}",
            vpc_id=vpc.id,
            cidr_block=f"10.0.{i+offset}.0/24",
            availability_zone=f"us-east-1{chr(97 + i + offset)}",
            tags={"Name": f"private-subnet-{i}"}
        )
        private_subnets.append(subnet)

    # 5) Route table para subnets públicas
    public_route_table = aws.ec2.RouteTable(
        "public-rt",
        vpc_id=vpc.id,
        routes=[{
            "cidr_block": "0.0.0.0/0",
            "gateway_id": igw.id,
        }],
        tags={"Name": "public-rt"}
    )

    # Asociar subnets públicas con la public route table
    for i, subnet in enumerate(public_subnets):
        aws.ec2.RouteTableAssociation(
            f"public-rt-assoc-{i}",
            route_table_id=public_route_table.id,
            subnet_id=subnet.id
        )

    # 6) NAT Gateway (si deseas Internet en privadas)
    eip_for_nat = aws.ec2.Eip("nat-eip", vpc=True)
    nat_gw = aws.ec2.NatGateway(
        "my-nat-gw",
        allocation_id=eip_for_nat.id,
        subnet_id=public_subnets[0].id,
        tags={"Name": "my-nat-gw"}
    )

    # 7) Route table para subnets privadas
    private_route_table = aws.ec2.RouteTable(
        "private-rt",
        vpc_id=vpc.id,
        routes=[{
            "cidr_block": "0.0.0.0/0",
            "nat_gateway_id": nat_gw.id,
        }],
        tags={"Name": "private-rt"}
    )

    # Asociar subnets privadas con la private route table
    for i, subnet in enumerate(private_subnets):
        aws.ec2.RouteTableAssociation(
            f"private-rt-assoc-{i}",
            route_table_id=private_route_table.id,
            subnet_id=subnet.id
        )

    # Exportar valores
    pulumi.export("vpc_id", vpc.id)
    pulumi.export("vpc_cidr", vpc.cidr_block)
    pulumi.export("public_subnet_ids", [s.id for s in public_subnets])
    pulumi.export("private_subnet_ids", [s.id for s in private_subnets])

    # Retornar outputs (opcional, se devuelven en up_res.outputs también)
    return {
        "vpc_id": vpc.id,
        "public_subnet_ids": [s.id for s in public_subnets],
        "private_subnet_ids": [s.id for s in private_subnets],
    }
