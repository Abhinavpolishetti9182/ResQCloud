output "ec2_instance_id" {
  description = "ID of the ResQCloud EC2 instance"
  value       = aws_instance.resqcloud_server.id
}

output "ec2_public_ip" {
  description = "Public IPv4 address of the ResQCloud EC2 instance"
  value       = aws_instance.resqcloud_server.public_ip
}

output "ec2_private_ip" {
  description = "Private IPv4 address of the ResQCloud EC2 instance"
  value       = aws_instance.resqcloud_server.private_ip
}

output "ec2_ami_id" {
  description = "AMI ID used by the ResQCloud EC2 instance"
  value       = data.aws_ami.ubuntu.id
}