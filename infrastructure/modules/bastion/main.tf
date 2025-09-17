# Data source for Amazon Linux AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security Group for Bastion Host
resource "aws_security_group" "bastion" {
  count       = var.create_bastion ? 1 : 0
  name        = "${var.prefix}-${var.environment}-bastion-sg"
  description = "Security group for bastion host"
  vpc_id      = var.vpc_id

  # SSH access from specified CIDRs
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
    description = "SSH access"
  }

  # All outbound traffic (for package updates, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name = "${var.prefix}-${var.environment}-bastion-sg"
  }
}

# Bastion Host Instance
resource "aws_instance" "bastion" {
  count                  = var.create_bastion ? 1 : 0
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  subnet_id              = var.public_subnet_id
  vpc_security_group_ids = [aws_security_group.bastion[0].id]
  key_name               = var.bastion_key_name
  region                 = var.region

  # User data script for initial setup
  user_data_base64 = base64encode(templatefile("${path.module}/bastion_userdata.sh", {
    db_endpoint = var.db_endpoint
  }))

  # Enable detailed monitoring
  monitoring = true

  # Instance metadata service v2 (security best practice)
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "${var.prefix}-${var.environment}-bastion"
    Type = "bastion"
  }
}

# Elastic IP for Bastion (optional but recommended)
resource "aws_eip" "bastion" {
  count    = var.create_bastion ? 1 : 0
  instance = aws_instance.bastion[0].id
  domain   = "vpc"

  tags = {
    Name = "${var.prefix}-${var.environment}-bastion-eip"
  }
}
