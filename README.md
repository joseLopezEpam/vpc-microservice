# VPC Microservice

## Overview
The VPC Microservice is a flexible and scalable solution designed to dynamically create Virtual Private Clouds (VPCs) in AWS using Pulumi. The service accepts payloads to configure the VPC and includes all necessary components to serve as a fully functional development environment.

## Key Features
- **Dynamic VPC Creation**: Create VPCs with configurable CIDR blocks, public and private subnets, NAT gateways, route tables, and firewalls.
- **Scalability**: Supports varying sizes and user-specified numbers of subnets.
- **Kubernetes Integration**: Deploys to a local Minikube cluster.
- **Pulumi Automation**: Uses Pulumi for infrastructure as code (IaC) to ensure reliability and repeatability.
- **Exportable Outputs**: Exports key VPC details, such as VPC ID, CIDR block, and subnet IDs.

## Project Structure
```
vpc-microservice
├── .git                  # Git repository metadata
├── .gitignore            # Specifies files to be ignored by Git
├── Dockerfile            # Dockerfile to containerize the service
├── k8s-manifests         # Kubernetes manifests for deployment
├── pulimu.yaml           # Pulumi project configuration
├── Pulumi.dev.yaml       # Pulumi environment-specific configuration
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
├── src                   # Source code for the service
├── test_credentials.py   # Script to test AWS credentials
├── venv                  # Python virtual environment
├── vpc-microservice.tar  # Compressed project for distribution
```

## Requirements
- Python 3.9 or higher
- Docker
- AWS CLI configured with appropriate permissions
- Pulumi installed
- Minikube installed and configured

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd vpc-microservice
   ```

2. **Set Up Python Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   Ensure the following variables are set:
   - `AWS_REGION`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `SQS_URL` (for message queue integration)

5. **Run the Script**
   Execute the provided script to create the VPC and its components:
   ```bash
   python src/main.py
   ```

6. **Build and Run the Docker Container**
   ```bash
   docker build -t vpc-microservice .
   docker run -p 8080:8080 vpc-microservice
   ```

7. **Deploy to Kubernetes**
   Deploy to a local Minikube cluster:
   ```bash
   minikube start
   kubectl apply -f k8s-manifests/
   ```

## Usage

### Example Payload
The service accepts a JSON payload to configure the VPC. Example:
```json
{
  "ProjectName": "dev-project",
  "Services": ["vpc"],
  "VpcName": "dev-vpc",
  "CidrBlock": "10.0.0.0/16",
  "NumPublicSubnets": 2,
  "NumPrivateSubnets": 2,
  "Tags": {
    "Environment": "development"
  }
}
```

### Sending a Payload
Use `curl` or any HTTP client:
```bash
curl -X POST http://localhost:8080/vpc -H "Content-Type: application/json" -d '{...}'
```

### Outputs
The service exports key information, such as:
- `vpc_id`
- `vpc_cidr`
- `public_subnet_<index>_id`
- `private_subnet_<index>_id`

## Contribution
Contributions are welcome! Please fork the repository and submit a pull request.


## Contact
For questions or support, contact jose_lopez2@epam.com

