#!/usr/bin/env python3
"""
AWS Cognito Token Generator Script

This script authenticates with AWS Cognito and returns a JWT access token
that can be used for API testing with Postman or other tools.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import string
import subprocess
import sys
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("❌ Error: boto3 is not installed")
    print("Install it with: pip install boto3")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: python-dotenv is not installed")
    print("Install it with: pip install python-dotenv")
    sys.exit(1)

try:
    import click
except ImportError:
    print("❌ Error: click is not installed")
    print("Install it with: pip install click")
    sys.exit(1)


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_colored(message: str, color: str = Colors.NC):
    """Print colored message to console."""
    print(f"{color}{message}{Colors.NC}")


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard. Returns True if successful."""
    try:
        # macOS
        if os.system("which pbcopy > /dev/null 2>&1") == 0:
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            return True
        # Linux
        elif os.system("which xclip > /dev/null 2>&1") == 0:
            subprocess.run(
                ["xclip", "-selection", "clipboard"], input=text.encode(), check=True
            )
            return True
    except subprocess.CalledProcessError:
        pass
    return False


def load_config():
    """Load configuration from .env.auth file."""
    env_file = Path(".env.auth")

    if not env_file.exists():
        print_colored(f"❌ Error: {env_file} file not found!", Colors.RED)
        print_colored(
            f"Please create {env_file} based on .env.auth.example", Colors.YELLOW
        )
        sys.exit(1)

    print_colored(f"Loading configuration from {env_file}...", Colors.YELLOW)
    load_dotenv(env_file)

    # Required environment variables
    required_vars = [
        "COGNITO_USER_POOL_ID",
        "COGNITO_CLIENT_ID",
        "COGNITO_USERNAME",
        "COGNITO_PASSWORD",
    ]

    config = {}
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            config[var] = value

    if missing_vars:
        print_colored("❌ Error: Missing required environment variables:", Colors.RED)
        for var in missing_vars:
            print_colored(f"  - {var}", Colors.RED)
        sys.exit(1)

    # Optional variables with defaults
    config["AWS_REGION"] = os.getenv("AWS_REGION", "us-east-1")
    config["AWS_PROFILE"] = os.getenv("AWS_PROFILE")
    config["COGNITO_CLIENT_SECRET"] = os.getenv("COGNITO_CLIENT_SECRET")  # Optional

    return config


def calculate_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calculate the SECRET_HASH required for Cognito authentication with client secret."""
    message = username + client_id
    dig = hmac.new(
        client_secret.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


def generate_secure_password(length: int = 16) -> str:
    """Generate a secure random password with mixed case, numbers, and symbols."""
    # Use a mix of uppercase, lowercase, digits, and safe symbols
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


def authenticate_with_cognito(config, new_password: str | None = None):
    """Authenticate with AWS Cognito and return JWT tokens."""
    try:
        # Configure AWS session
        session_kwargs = {"region_name": config["AWS_REGION"]}
        if config["AWS_PROFILE"]:
            session_kwargs["profile_name"] = config["AWS_PROFILE"]
            print_colored(f"Using AWS Profile: {config['AWS_PROFILE']}", Colors.YELLOW)

        session = boto3.Session(**session_kwargs)
        cognito_client = session.client("cognito-idp")

        print_colored("Authenticating with AWS Cognito...", Colors.YELLOW)
        print(f"User Pool ID: {config['COGNITO_USER_POOL_ID']}")
        print(f"Client ID: {config['COGNITO_CLIENT_ID']}")
        print(f"Username: {config['COGNITO_USERNAME']}")
        print(f"Region: {config['AWS_REGION']}")
        print()

        # Prepare authentication parameters
        auth_parameters = {
            "USERNAME": config["COGNITO_USERNAME"],
            "PASSWORD": config["COGNITO_PASSWORD"],
        }

        # Add SECRET_HASH if client secret is provided
        if config["COGNITO_CLIENT_SECRET"]:
            secret_hash = calculate_secret_hash(
                config["COGNITO_USERNAME"],
                config["COGNITO_CLIENT_ID"],
                config["COGNITO_CLIENT_SECRET"],
            )
            auth_parameters["SECRET_HASH"] = secret_hash
            print_colored("Using client secret authentication", Colors.YELLOW)

        # Perform AWS Cognito authentication
        response = cognito_client.admin_initiate_auth(
            UserPoolId=config["COGNITO_USER_POOL_ID"],
            ClientId=config["COGNITO_CLIENT_ID"],
            AuthFlow="ADMIN_NO_SRP_AUTH",
            AuthParameters=auth_parameters,
        )

        # Handle challenges (like NEW_PASSWORD_REQUIRED)
        if "ChallengeName" in response:
            if response["ChallengeName"] == "NEW_PASSWORD_REQUIRED":
                print_colored(
                    "🔒 User must set a new permanent password", Colors.YELLOW
                )

                # Use provided password or generate a secure one
                if new_password:
                    permanent_password = new_password
                    print("Using provided new password")
                else:
                    permanent_password = generate_secure_password()
                    print_colored(
                        f"Generated new secure password: {permanent_password}",
                        Colors.GREEN,
                    )

                # Prepare challenge response parameters
                challenge_params = {
                    "USERNAME": config["COGNITO_USERNAME"],
                    "NEW_PASSWORD": permanent_password,
                }

                if config["COGNITO_CLIENT_SECRET"]:
                    challenge_params["SECRET_HASH"] = auth_parameters["SECRET_HASH"]
                
                # Handle required attributes from the challenge
                required_attrs = response.get("ChallengeParameters", {}).get("requiredAttributes")
                if required_attrs:
                    import ast
                    required_attrs_list = ast.literal_eval(required_attrs)
                    print_colored(f"Required attributes: {required_attrs_list}", Colors.YELLOW)
                    
                    # Add required attributes with default values
                    for attr in required_attrs_list:
                        if attr == "userAttributes.name":
                            challenge_params["userAttributes.name"] = "Admin User"  # Default name
                            print("Setting default name: 'Admin User'")
                        # Add more attribute handling as needed

                # Respond to the challenge
                try:
                    challenge_response = cognito_client.admin_respond_to_auth_challenge(
                        UserPoolId=config["COGNITO_USER_POOL_ID"],
                        ClientId=config["COGNITO_CLIENT_ID"],
                        ChallengeName="NEW_PASSWORD_REQUIRED",
                        Session=response["Session"],
                        ChallengeResponses=challenge_params,
                    )
                except ClientError as challenge_error:
                    print_colored("❌ Challenge response failed:", Colors.RED)
                    print(f"Error: {challenge_error.response['Error']['Code']} - {challenge_error.response['Error']['Message']}")
                    print(f"Challenge parameters received: {response.get('ChallengeParameters', {})}")
                    print()
                    print("This might be because your User Pool requires additional attributes.")
                    print("Try setting a permanent password manually in the AWS Console:")
                    print("1. Go to AWS Cognito → Users → [your-user] → Actions → Set permanent password")
                    sys.exit(1)

                print_colored("✅ Password set as permanent", Colors.GREEN)

                # Return both the auth result and the new password for display
                return challenge_response["AuthenticationResult"], permanent_password
            else:
                print_colored(
                    f"❌ Unhandled challenge: {response['ChallengeName']}", Colors.RED
                )
                print(
                    f"Challenge parameters: {response.get('ChallengeParameters', {})}"
                )
                sys.exit(1)

        # No challenge, return auth result with no password change
        return response["AuthenticationResult"], None

    except NoCredentialsError:
        print_colored("❌ AWS credentials not found!", Colors.RED)
        print("Please configure your AWS credentials using one of these methods:")
        print("1. AWS CLI: aws configure")
        print("2. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("3. IAM roles (if running on EC2)")
        print("4. AWS profile in .env.auth: AWS_PROFILE=your-profile")
        sys.exit(1)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        print_colored("❌ Authentication failed!", Colors.RED)
        print(f"Error: {error_code} - {error_message}")
        print()
        print("Common solutions:")
        if error_code == "UserNotConfirmedException":
            print("• Confirm your user in the Cognito console")
        elif error_code == "NotAuthorizedException":
            print("• Check your username and password")
            print("• Ensure your user account is not locked")
        elif error_code == "InvalidParameterException":
            print("• Verify your User Pool ID and Client ID")
            print("• Check that ADMIN_NO_SRP_AUTH flow is enabled")
        else:
            print("• Check your Cognito configuration")
            print("• Verify AWS permissions for cognito-idp:AdminInitiateAuth")
        sys.exit(1)


@click.command()
@click.option(
    "--new-password", 
    help="New permanent password to set (if user needs password change). If not provided, a secure password will be generated."
)
@click.option(
    "--debug", 
    is_flag=True, 
    help="Show decoded token claims for debugging"
)
def main(new_password, debug):
    """AWS Cognito Token Generator - Get JWT tokens for API testing."""
    print_colored("🔐 AWS Cognito Token Generator", Colors.BLUE)
    print_colored("=" * 40, Colors.BLUE)
    print()

    # Load configuration
    config = load_config()

    # Authenticate with Cognito
    auth_result, changed_password = authenticate_with_cognito(config, new_password)

    # Extract tokens
    access_token = auth_result["AccessToken"]
    expires_in = auth_result["ExpiresIn"]

    print_colored("✅ Authentication successful!", Colors.GREEN)
    print()
    
    # Show new password if it was changed
    if changed_password:
        print_colored("🔑 New Password Information:", Colors.GREEN)
        print(f"Your permanent password is now: {changed_password}")
        print_colored("⚠️  Save this password! Update your .env.auth file with the new password.", Colors.YELLOW)
        print()
        
    print_colored("Access Token (use this for API authorization):", Colors.GREEN)
    print(f"Bearer {access_token}")
    print()
    print_colored("Token Details:", Colors.GREEN)
    print(f"• Expires in: {expires_in} seconds ({expires_in // 60} minutes)")
    print(f"• Token length: {len(access_token)} characters")
    print()

    # Copy to clipboard
    if copy_to_clipboard(access_token):
        print_colored("📋 Access token copied to clipboard!", Colors.YELLOW)

    print()
    print_colored("Usage Instructions:", Colors.YELLOW)
    print("1. Copy the access token above")
    print("2. In Postman, go to Authorization tab")
    print("3. Select 'Bearer Token' type")
    print("4. Paste the token (without 'Bearer' prefix)")
    print("5. Send your API requests")
    print()
    print_colored("OpenAPI UI (Swagger) Instructions:", Colors.YELLOW)
    print("1. Go to http://localhost:8000/docs")
    print("2. Click the 'Authorize' button (🔒)")
    print(f"3. Enter: Bearer {access_token}")
    print("4. Click 'Authorize' and 'Close'")
    print()
    print_colored(f"Token is valid for {expires_in // 60} minutes", Colors.GREEN)

    # Optionally decode and display token claims for debugging
    if debug:
        try:
            import jwt

            decoded = jwt.decode(access_token, options={"verify_signature": False})
            print()
            print_colored("🔍 Token Claims (Debug Info):", Colors.BLUE)
            print(json.dumps(decoded, indent=2, default=str))
        except ImportError:
            print_colored(
                "Install PyJWT to see token claims: pip install PyJWT", Colors.YELLOW
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n❌ Operation cancelled by user", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"❌ Unexpected error: {e}", Colors.RED)
        sys.exit(1)
