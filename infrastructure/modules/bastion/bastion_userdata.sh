#!/bin/bash
yum update -y
yum install -y postgresql amazon-ssm-agent htop tree wget curl

# Install and start SSM agent
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Configure SSH for port forwarding
echo "AllowTcpForwarding yes" >> /etc/ssh/sshd_config
echo "GatewayPorts yes" >> /etc/ssh/sshd_config
systemctl restart sshd

# Create database connection helper script
cat > /home/ec2-user/connect_db.sh << 'EOL'
#!/bin/bash
DB_ENDPOINT="${db_endpoint}"
echo "Database endpoint: $DB_ENDPOINT"
echo "To connect to database from your local machine:"
echo "1. Run this command on your local machine:"
echo "   ssh -i your-key.pem -L 5432:$DB_ENDPOINT:5432 ec2-user@$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "2. Then connect DBeaver to localhost:5432"
echo ""
echo "To get database credentials:"
echo "   aws secretsmanager get-secret-value --secret-id 
note-rags-dev-db-password"
EOL

chmod +x /home/ec2-user/connect_db.sh
chown ec2-user:ec2-user /home/ec2-user/connect_db.sh

# Create a simple script to test database connectivity from bastion
cat > /home/ec2-user/test_db.sh << 'EOL'
#!/bin/bash
DB_ENDPOINT="${db_endpoint}"
echo "Testing database connectivity..."
pg_isready -h $DB_ENDPOINT -p 5432
if [ $? -eq 0 ]; then
    echo "✅ Database is reachable from bastion"
else
    echo "❌ Cannot reach database"
fi
EOL

chmod +x /home/ec2-user/test_db.sh
chown ec2-user:ec2-user /home/ec2-user/test_db.sh

echo "Bastion setup complete with database integration" >
/var/log/bastion-setup.log
echo "Database endpoint: ${db_endpoint}" >> /var/log/bastion-setup.log