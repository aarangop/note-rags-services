
module "networking" {
  source = "./modules/networking"
  # Base args
  prefix      = var.prefix
  environment = var.environment
  region      = var.region
  # Networking args
  vpc_cidr    = var.vpc_cidr
  az_count    = var.az_count
}

module "security" {
  source = "./modules/security"
  # Base args
  prefix      = var.prefix
  environment = var.environment
  # Networking args
  github_branches = var.github_branches
  github_org      = var.github_org
  github_repo     = var.github_repo
}

module "ecr" {
  source = "./modules/ecr"
  # Base args
  prefix      = var.prefix
  environment = var.environment
  # ECR args
  repository_name       = var.repository_name
  image_retention_count = var.image_retention_count
}

module "database" {
  source = "./modules/database"
  # Base args
  prefix      = var.prefix
  environment = var.environment
  # Database args
  vpc_id               = module.networking.vpc_id
  database_subnet_ids  = module.networking.database_subnet_ids
  private_subnet_cidrs = module.networking.private_subnet_cidrs
  db_instance_class    = var.db_instance_class
}

module "bastion" {
  source = "./modules/bastion"
  # Base args
  prefix      = var.prefix
  environment = var.environment
  region      = var.region
  # Bastion args
  create_bastion    = var.create_bastion
  allowed_ssh_cidrs = var.allowed_ssh_cidrs
  bastion_key_name  = var.bastion_key_name
  vpc_id            = module.networking.vpc_id
  public_subnet_id  = module.networking.public_subnet_ids[0]
  db_endpoint       = module.database.db_instance_endpoint
}

module "eks" {
  source = "./modules/eks"
  count  = var.create_eks ? 1 : 0

  # Base args
  prefix      = var.prefix
  environment = var.environment
  region      = var.region

  # Networking args
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids

  # Database connectivity
  db_security_group_id = module.database.db_security_group_id

  # EKS configuration
  cluster_version                     = var.cluster_version
  node_group_instance_types           = var.node_group_instance_types
  node_group_desired_size             = var.node_group_desired_size
  node_group_max_size                 = var.node_group_max_size
  node_group_min_size                 = var.node_group_min_size
  enable_irsa                         = true
  enable_aws_load_balancer_controller = true
}