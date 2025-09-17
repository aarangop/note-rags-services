output "bastion_public_ip" {
  description = "Public IP of bastion host"
  value       = var.create_bastion ? aws_eip.bastion[0].public_ip : null
}

output "bastion_private_ip" {
  description = "Private IP of bastion host"
  value       = var.create_bastion ? aws_instance.bastion[0].private_ip : null
}