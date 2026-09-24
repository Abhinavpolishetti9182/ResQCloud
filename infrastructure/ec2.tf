# ---------------------------------------------------------
# Find the latest Ubuntu 24.04 LTS AMI
# ---------------------------------------------------------

data "aws_ami" "ubuntu" {
  most_recent = true

  owners = [
    "099720109477"
  ]

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

# ---------------------------------------------------------
# EC2 Instance
# ---------------------------------------------------------

resource "aws_instance" "resqcloud_server" {
  ami = data.aws_ami.ubuntu.id

  instance_type = var.ec2_instance_type

  subnet_id = aws_subnet.resqcloud_public_subnet.id

  vpc_security_group_ids = [
    aws_security_group.resqcloud_ec2_sg.id
  ]

  iam_instance_profile = aws_iam_instance_profile.resqcloud_ec2_profile.name

  associate_public_ip_address = true

  user_data = file("${path.module}/user_data.sh")

  user_data_replace_on_change = true

  root_block_device {
    volume_size = 20
    volume_type = "gp3"

    encrypted = true

    delete_on_termination = true
  }

  tags = {
    Name = "${var.project_name}-server"
  }
}