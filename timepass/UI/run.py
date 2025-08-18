#!/usr/bin/env python3
"""
Run script for AgriAI Assistant UI
Provides easy startup with configuration options
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import requests
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False

def setup_environment(args):
    """Setup environment variables"""
    env_vars = {}
    
    if args.api_url:
        env_vars["API_BASE_URL"] = args.api_url
    if args.debug:
        env_vars["DEBUG"] = "True"
    if args.mock_api:
        env_vars["ENABLE_MOCK_API"] = "True"
    if args.timeout:
        env_vars["API_TIMEOUT"] = str(args.timeout)
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"🔧 Set {key}={value}")

def run_streamlit(args):
    """Run the Streamlit application"""
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", str(args.port),
        "--server.address", args.host
    ]
    
    if args.headless:
        cmd.extend(["--server.headless", "true"])
    
    print(f"🚀 Starting AgriAI Assistant on http://{args.host}:{args.port}")
    print("🌾 Welcome to AgriAI Assistant!")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 AgriAI Assistant stopped. Thank you for using our service!")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="AgriAI Assistant UI - Run Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                          # Run with defaults
  python run.py --mock-api               # Run with mock API
  python run.py --debug --port 8502      # Debug mode on custom port
  python run.py --api-url http://api.com # Custom backend URL
        """
    )
    
    # Server configuration
    parser.add_argument("--host", default="localhost", 
                       help="Host address (default: localhost)")
    parser.add_argument("--port", type=int, default=8501,
                       help="Port number (default: 8501)")
    parser.add_argument("--headless", action="store_true",
                       help="Run in headless mode (no browser auto-open)")
    
    # API configuration
    parser.add_argument("--api-url", 
                       help="Backend API URL (default: http://localhost:8000)")
    parser.add_argument("--timeout", type=int,
                       help="API timeout in seconds (default: 30)")
    parser.add_argument("--mock-api", action="store_true",
                       help="Use mock API for development/testing")
    
    # Development options
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode")
    parser.add_argument("--skip-deps", action="store_true",
                       help="Skip dependency check")
    
    args = parser.parse_args()
    
    # Welcome message
    print("🌾 AgriAI Assistant UI - Startup Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ Error: app.py not found in current directory")
        print("📁 Please run this script from the project root directory")
        sys.exit(1)
    
    # Check dependencies
    if not args.skip_deps and not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment(args)
    
    # Display configuration
    print("\n📋 Configuration:")
    print(f"   🌐 Host: {args.host}")
    print(f"   🔌 Port: {args.port}")
    print(f"   🤖 Mock API: {'Yes' if args.mock_api else 'No'}")
    print(f"   🐛 Debug: {'Yes' if args.debug else 'No'}")
    if args.api_url:
        print(f"   🔗 API URL: {args.api_url}")
    print()
    
    # Run the application
    run_streamlit(args)

if __name__ == "__main__":
    main()