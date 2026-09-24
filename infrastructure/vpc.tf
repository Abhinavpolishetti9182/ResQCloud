# ---------------------------------------------------------
# ResQCloud VPC
# ---------------------------------------------------------

resource "aws_vpc" "resqcloud_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# ---------------------------------------------------------
# Internet Gateway
# ---------------------------------------------------------

resource "aws_internet_gateway" "resqcloud_igw" {
  vpc_id = aws_vpc.resqcloud_vpc.id

  tags = {
    Name = "${var.project_name}-internet-gateway"
  }
}

# ---------------------------------------------------------
# Public Subnet
# ---------------------------------------------------------

resource "aws_subnet" "resqcloud_public_subnet" {
  vpc_id                  = aws_vpc.resqcloud_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
    Tier = "public"
  }
}

# ---------------------------------------------------------
# Public Route Table
# ---------------------------------------------------------

resource "aws_route_table" "resqcloud_public_route_table" {
  vpc_id = aws_vpc.resqcloud_vpc.id

  tags = {
    Name = "${var.project_name}-public-route-table"
  }
}

# ---------------------------------------------------------
# Internet Route
# ---------------------------------------------------------

resource "aws_route" "resqcloud_internet_route" {
  route_table_id         = aws_route_table.resqcloud_public_route_table.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.resqcloud_igw.id
}

# ---------------------------------------------------------
# Associate Public Subnet with Route Table
# ---------------------------------------------------------

resource "aws_route_table_association" "resqcloud_public_association" {
  subnet_id      = aws_subnet.resqcloud_public_subnet.id
  route_table_id = aws_route_table.resqcloud_public_route_table.id
}