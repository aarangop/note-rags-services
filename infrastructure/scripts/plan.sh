#!/bin/bash
MY_IP=$(curl -s ifconfig.me)
echo "🌐 Current IP: $MY_IP"
echo "🏗️  Planning infrastructure..."

terraform plan \
    -var="allowed_ssh_cidrs=[\"$MY_IP/32\"]" \
    -var="create_bastion=true" \
    -var="bastion_key_name=fa-macbook"