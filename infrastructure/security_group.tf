# ---------------------------------------------------------
# ResQCloud EC2 Security Group
# ---------------------------------------------------------

resource "aws_security_group" "resqcloud_ec2_sg" {
  name        = "${var.project_name}-ec2-security-group"
  description = "Security group for the ResQCloud EC2 application server"
  vpc_id      = aws_vpc.resqcloud_vpc.id

  tags = {
    Name = "${var.project_name}-ec2-security-group"
  }
}

# ---------------------------------------------------------
# SSH Inbound Rule
# ---------------------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.resqcloud_ec2_sg.id

  cidr_ipv4   = var.admin_ip_cidr
  from_port   = 22
  to_port     = 22
  ip_protocol = "tcp"

  description = "Allow SSH access from the administrator public IP"
}

# ---------------------------------------------------------
# HTTP Inbound Rule
# ---------------------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.resqcloud_ec2_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"

  description = "Allow public HTTP traffic"
}

# ---------------------------------------------------------
# HTTPS Inbound Rule
# ---------------------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.resqcloud_ec2_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"

  description = "Allow public HTTPS traffic"
}

# ---------------------------------------------------------
# Outbound Rule
# ---------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "all_outbound" {
  security_group_id = aws_security_group.resqcloud_ec2_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"

  description = "Allow outbound traffic"
}