terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.30" }
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" { source = "./modules/vpc" }
module "ecs" { source = "./modules/ecs", vpc_id = module.vpc.vpc_id }
module "rds" { source = "./modules/rds", vpc_id = module.vpc.vpc_id }
module "redis" { source = "./modules/redis", vpc_id = module.vpc.vpc_id }
