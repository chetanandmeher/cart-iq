provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "cartiq_server" {
  ami           = "ami-0c7217cdde317cfec" # Amazon Linux 2 AMI
  instance_type = "t3.medium"

  tags = {
    Name = "CartIQ-Server"
  }
}
