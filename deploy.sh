#!/bin/bash

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and required packages
sudo apt-get install -y python3-pip python3-venv nginx

# Create application directory
mkdir -p /home/ubuntu/NGO
cd /home/ubuntu/NGO

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install application dependencies
pip install -r requirements.txt
pip install gunicorn

# Create uploads directory
mkdir -p uploads

# Create systemd service file
sudo tee /etc/systemd/system/student-results.service << EOF
[Unit]
Description=Student Results Portal
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/NGO
Environment="PATH=/home/ubuntu/NGO/venv/bin"
ExecStart=/home/ubuntu/NGO/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 app:app

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable student-results
sudo systemctl start student-results

# Configure Nginx
sudo tee /etc/nginx/sites-available/student-results << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /uploads {
        alias /home/ubuntu/NGO/uploads;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/student-results /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Set up firewall
sudo ufw allow 80
sudo ufw allow 22
sudo ufw enable 