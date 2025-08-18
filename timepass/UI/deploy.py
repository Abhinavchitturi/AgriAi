#!/usr/bin/env python3
"""
Deployment script for AgriAI Assistant UI
Handles various deployment scenarios
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from typing import Dict, List

class AgriUIDeployer:
    """Handles deployment of AgriAI Assistant UI"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.required_files = [
            "app.py", "config.py", "api_client.py", 
            "utils.py", "requirements.txt"
        ]
    
    def check_prerequisites(self) -> bool:
        """Check if all required files exist"""
        print("🔍 Checking prerequisites...")
        
        missing_files = []
        for file in self.required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        print("✅ All required files found")
        return True
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        print("📦 Installing dependencies...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def create_systemd_service(self, user: str = "agriuser", 
                              port: int = 8501) -> bool:
        """Create systemd service file for Linux deployment"""
        print("🔧 Creating systemd service...")
        
        service_content = f"""[Unit]
Description=AgriAI Assistant UI
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={self.project_root}
Environment=PATH={sys.executable}
ExecStart={sys.executable} -m streamlit run app.py --server.port {port} --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_file = Path("/etc/systemd/system/agri-ai-ui.service")
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            print(f"✅ Service file created at {service_file}")
            print("🔧 Run the following commands to enable the service:")
            print("   sudo systemctl daemon-reload")
            print("   sudo systemctl enable agri-ai-ui")
            print("   sudo systemctl start agri-ai-ui")
            return True
            
        except PermissionError:
            print("❌ Permission denied. Run with sudo or create service file manually")
            print(f"📄 Service file content:\n{service_content}")
            return False
    
    def create_nginx_config(self, domain: str = "localhost", 
                           port: int = 8501) -> str:
        """Create Nginx reverse proxy configuration"""
        nginx_config = f"""server {{
    listen 80;
    server_name {domain};
    
    location / {{
        proxy_pass http://localhost:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }}
    
    # Streamlit specific configurations
    location /_stcore/stream {{
        proxy_pass http://localhost:{port}/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }}
    
    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
}}
"""
        return nginx_config
    
    def deploy_docker(self, image_name: str = "agri-ai-ui", 
                     port: int = 8501, api_url: str = "") -> bool:
        """Deploy using Docker"""
        print("🐳 Deploying with Docker...")
        
        # Build Docker image
        try:
            build_cmd = ["docker", "build", "-t", image_name, "."]
            subprocess.check_call(build_cmd)
            print(f"✅ Docker image '{image_name}' built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build Docker image: {e}")
            return False
        
        # Run Docker container
        try:
            run_cmd = [
                "docker", "run", "-d",
                "--name", "agri-ai-ui-container",
                "-p", f"{port}:8501"
            ]
            
            if api_url:
                run_cmd.extend(["-e", f"API_BASE_URL={api_url}"])
            
            run_cmd.append(image_name)
            
            subprocess.check_call(run_cmd)
            print(f"✅ Container started on port {port}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to run Docker container: {e}")
            return False
    
    def deploy_heroku(self, app_name: str) -> bool:
        """Deploy to Heroku"""
        print("🚀 Deploying to Heroku...")
        
        # Create Procfile
        procfile_content = "web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0"
        
        with open("Procfile", "w") as f:
            f.write(procfile_content)
        
        print("✅ Procfile created")
        
        # Create setup.sh for Streamlit configuration
        setup_sh_content = """mkdir -p ~/.streamlit/

echo "\\
[general]\\n\\
email = \\"your-email@example.com\\"\\n\\
" > ~/.streamlit/credentials.toml

echo "\\
[server]\\n\\
headless = true\\n\\
enableCORS=false\\n\\
port = $PORT\\n\\
" > ~/.streamlit/config.toml
"""
        
        with open("setup.sh", "w") as f:
            f.write(setup_sh_content)
        
        os.chmod("setup.sh", 0o755)
        print("✅ setup.sh created")
        
        print("🔧 Next steps for Heroku deployment:")
        print("1. heroku create your-app-name")
        print("2. git add .")
        print("3. git commit -m 'Initial deployment'")
        print("4. git push heroku main")
        print("5. heroku config:set API_BASE_URL=your-backend-url")
        
        return True
    
    def deploy_streamlit_cloud(self) -> bool:
        """Prepare for Streamlit Cloud deployment"""
        print("☁️ Preparing for Streamlit Cloud deployment...")
        
        # Create .streamlit/config.toml
        streamlit_dir = Path(".streamlit")
        streamlit_dir.mkdir(exist_ok=True)
        
        config_content = """[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
headless = true
"""
        
        with open(streamlit_dir / "config.toml", "w") as f:
            f.write(config_content)
        
        print("✅ Streamlit config created")
        print("🔧 Next steps for Streamlit Cloud:")
        print("1. Push code to GitHub repository")
        print("2. Go to https://share.streamlit.io/")
        print("3. Connect your GitHub repository")
        print("4. Deploy app.py")
        print("5. Set API_BASE_URL in the secrets management")
        
        return True
    
    def create_docker_compose(self, api_url: str = "http://backend:8000") -> bool:
        """Create docker-compose.yml for multi-service deployment"""
        compose_content = f"""version: '3.8'

services:
  agri-ui:
    build:
      context: .
      target: production
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL={api_url}
      - DEBUG=false
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - agri-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - agri-ui
    restart: unless-stopped
    networks:
      - agri-network

networks:
  agri-network:
    driver: bridge
"""
        
        with open("docker-compose.yml", "w") as f:
            f.write(compose_content)
        
        # Create nginx.conf
        nginx_conf = self.create_nginx_config("localhost", 8501)
        with open("nginx.conf", "w") as f:
            f.write(nginx_conf)
        
        print("✅ docker-compose.yml and nginx.conf created")
        print("🔧 Run: docker-compose up -d")
        
        return True

def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="AgriAI Assistant UI Deployment Script")
    parser.add_argument("deployment_type", 
                       choices=["local", "docker", "heroku", "streamlit-cloud", "systemd", "compose"],
                       help="Type of deployment")
    parser.add_argument("--port", type=int, default=8501, help="Port number")
    parser.add_argument("--api-url", help="Backend API URL")
    parser.add_argument("--domain", default="localhost", help="Domain name")
    parser.add_argument("--app-name", help="App name (for Heroku)")
    parser.add_argument("--user", default="agriuser", help="System user (for systemd)")
    
    args = parser.parse_args()
    
    deployer = AgriUIDeployer()
    
    print("🌾 AgriAI Assistant UI - Deployment Script")
    print("=" * 50)
    
    # Check prerequisites
    if not deployer.check_prerequisites():
        sys.exit(1)
    
    success = False
    
    if args.deployment_type == "local":
        success = deployer.install_dependencies()
        if success:
            print("🚀 Starting local development server...")
            os.system(f"streamlit run app.py --server.port {args.port}")
    
    elif args.deployment_type == "docker":
        success = deployer.deploy_docker(port=args.port, api_url=args.api_url or "")
    
    elif args.deployment_type == "heroku":
        if not args.app_name:
            print("❌ App name required for Heroku deployment")
            sys.exit(1)
        success = deployer.deploy_heroku(args.app_name)
    
    elif args.deployment_type == "streamlit-cloud":
        success = deployer.deploy_streamlit_cloud()
    
    elif args.deployment_type == "systemd":
        success = deployer.create_systemd_service(args.user, args.port)
    
    elif args.deployment_type == "compose":
        success = deployer.create_docker_compose(args.api_url or "http://backend:8000")
    
    if success:
        print("🎉 Deployment completed successfully!")
    else:
        print("❌ Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()