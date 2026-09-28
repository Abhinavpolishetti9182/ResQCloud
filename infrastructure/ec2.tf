# Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# ResQCloud EC2 Server
resource "aws_instance" "resqcloud_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.ec2_instance_type
  key_name      = "resqcloud-key"

  subnet_id              = aws_subnet.resqcloud_public_subnet.id
  vpc_security_group_ids = [aws_security_group.resqcloud_ec2_sg.id]

  associate_public_ip_address = true

  iam_instance_profile = aws_iam_instance_profile.resqcloud_ec2_profile.name

  user_data = file("${path.module}/user_data.sh")

  user_data_replace_on_change = true

  # IMDSv2 Security Configuration
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  # Root Volume Configuration
  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = "${var.project_name}-server"
  }
}