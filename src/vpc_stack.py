import logging
import pulumi
import pulumi_aws as aws

logger = logging.getLogger(__name__)

def create_vpc_resources(config: dict):
    logger.info(f"Creating VPC resources with configuration: {config}")

    vpc_cidr = config["vpc_cidr"]
    vpc_name = config["vpc_name"]
    num_public_subnets = config["num_public_subnets"]
    num_private_subnets = config["num_private_subnets"]
    tags = config["tags"]

    vpc = aws.ec2.Vpc(
        resource_name=f"vpc-{vpc_name}",
        cidr_block=vpc_cidr,
        enable_dns_support=True,
        enable_dns_hostnames=True,
        tags={"Name": vpc_name, **tags}
    )

    igw = aws.ec2.InternetGateway(
        resource_name=f"igw-{vpc_name}",
        vpc_id=vpc.id,
        tags={"Name": f"{vpc_name}-igw", **tags}
    )

    eip = aws.ec2.Eip(
        resource_name=f"eip-{vpc_name}",
        vpc=True,
        tags={"Name": f"{vpc_name}-nat-eip", **tags}
    )

    public_subnets = []
    for i in range(num_public_subnets):
        public_subnet = aws.ec2.Subnet(
            resource_name=f"public-subnet-{i}-{vpc_name}",
            vpc_id=vpc.id,
            cidr_block=f"10.0.{i}.0/24",
            map_public_ip_on_launch=True,
            tags={"Name": f"{vpc_name}-public-{i}", **tags}
        )
        public_subnets.append(public_subnet)

    nat_gw = aws.ec2.NatGateway(
        resource_name=f"nat-gw-{vpc_name}",
        allocation_id=eip.id,
        subnet_id=public_subnets[0].id,
        tags={"Name": f"{vpc_name}-nat-gw", **tags}
    )

    private_subnets = []
    for i in range(num_private_subnets):
        private_subnet = aws.ec2.Subnet(
            resource_name=f"private-subnet-{i}-{vpc_name}",
            vpc_id=vpc.id,
            cidr_block=f"10.0.{i + 10}.0/24",
            tags={"Name": f"{vpc_name}-private-{i}", **tags}
        )
        private_subnets.append(private_subnet)

    public_rt = aws.ec2.RouteTable(
        resource_name=f"public-rt-{vpc_name}",
        vpc_id=vpc.id,
        tags={"Name": f"{vpc_name}-public-rt", **tags}
    )

    aws.ec2.Route(
        resource_name=f"public-route-{vpc_name}",
        route_table_id=public_rt.id,
        gateway_id=igw.id,
        destination_cidr_block="0.0.0.0/0"
    )

    private_rt = aws.ec2.RouteTable(
        resource_name=f"private-rt-{vpc_name}",
        vpc_id=vpc.id,
        tags={"Name": f"{vpc_name}-private-rt", **tags}
    )

    aws.ec2.Route(
        resource_name=f"private-route-{vpc_name}",
        route_table_id=private_rt.id,
        nat_gateway_id=nat_gw.id,
        destination_cidr_block="0.0.0.0/0"
    )

    for i, subnet in enumerate(public_subnets):
        aws.ec2.RouteTableAssociation(
            resource_name=f"public-rt-assoc-{i}-{vpc_name}",
            route_table_id=public_rt.id,
            subnet_id=subnet.id
        )

    for i, subnet in enumerate(private_subnets):
        aws.ec2.RouteTableAssociation(
            resource_name=f"private-rt-assoc-{i}-{vpc_name}",
            route_table_id=private_rt.id,
            subnet_id=subnet.id
        )

    pulumi.export("vpc_id", vpc.id)
    pulumi.export("igw_id", igw.id)
    pulumi.export("nat_gw_id", nat_gw.id)

    for i, subnet in enumerate(public_subnets):
        pulumi.export(f"public_subnet_{i}_id", subnet.id)

    for i, subnet in enumerate(private_subnets):
        pulumi.export(f"private_subnet_{i}_id", subnet.id)

    logger.info("VPC, subnets, NAT gateway, and route tables successfully created.")
