#!/usr/bin/env python3
"""
Kubernetes Secret Management Script

This script manages Kubernetes secrets by loading environment variables from .env files
and creating/updating secrets using kubectl commands. This approach keeps sensitive data
out of version control while making secret management simple and maintainable.

Usage:
    python scripts/manage_k8s_secrets.py                 # Create secrets
    python scripts/manage_k8s_secrets.py --update        # Update existing secrets
    python scripts/manage_k8s_secrets.py --dry-run       # Preview operations
    python scripts/manage_k8s_secrets.py --delete        # Delete secrets
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv is required. Install it with: pip install python-dotenv")
    sys.exit(1)


class KubernetesSecretManager:
    def __init__(self, namespace: str = "note-rags"):
        self.namespace = namespace
        self.secrets_config = {
            "postgres-secret": {
                "env_vars": ["DB_USER", "DB_PASSWORD"],
                "kubectl_mapping": {"DB_USER": "POSTGRES_USER", "DB_PASSWORD": "POSTGRES_PASSWORD"},
                "labels": {"app": "postgres"},
            },
            "notes-api-secret": {
                "env_vars": ["JWKS_URL", "JWT_ISSUER"],
                "kubectl_mapping": {},  # Direct mapping
                "labels": {"app": "notes-api"},
            },
        }

    def load_environment_variables(self) -> dict[str, str]:
        """Load environment variables from .env and .env.auth files."""
        env_vars = {}

        # Load from .env file
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✓ Loaded environment variables from {env_file}")
        else:
            print(f"⚠ Warning: {env_file} not found")

        # Load from .env.auth file
        env_auth_file = Path(".env.auth")
        if env_auth_file.exists():
            load_dotenv(env_auth_file)
            print(f"✓ Loaded environment variables from {env_auth_file}")
        else:
            print(f"⚠ Warning: {env_auth_file} not found")

        # Get all required environment variables
        for _secret_name, config in self.secrets_config.items():
            for env_var in config["env_vars"]:
                value = os.getenv(env_var)
                if value:
                    env_vars[env_var] = value
                else:
                    print(f"⚠ Warning: {env_var} not found in environment")

        return env_vars

    def run_kubectl_command(self, args: list[str], dry_run: bool = False) -> bool:
        """Run a kubectl command and return success status."""
        cmd = ["kubectl"] + args

        if dry_run:
            print(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running kubectl command: {' '.join(cmd)}")
            print(f"Error: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: kubectl command not found. Please install kubectl.")
            return False

    def secret_exists(self, secret_name: str) -> bool:
        """Check if a secret exists in the namespace."""
        cmd = ["get", "secret", secret_name, "-n", self.namespace, "--ignore-not-found"]
        result = subprocess.run(["kubectl"] + cmd, capture_output=True, text=True)
        return bool(result.stdout.strip())

    def delete_secret(self, secret_name: str, dry_run: bool = False) -> bool:
        """Delete a secret if it exists."""
        if not self.secret_exists(secret_name) and not dry_run:
            return True

        cmd = ["delete", "secret", secret_name, "-n", self.namespace]
        return self.run_kubectl_command(cmd, dry_run)

    def create_secret(
        self, secret_name: str, env_vars: dict[str, str], dry_run: bool = False
    ) -> bool:
        """Create a secret from environment variables."""
        config = self.secrets_config[secret_name]

        # Build kubectl create secret command
        cmd = ["create", "secret", "generic", secret_name, "-n", self.namespace]

        # Add literal values
        for env_var in config["env_vars"]:
            if env_var not in env_vars:
                print(f"Error: Required environment variable {env_var} not found")
                return False

            # Use kubectl mapping if specified, otherwise use env var name directly
            kubectl_key = config["kubectl_mapping"].get(env_var, env_var)
            cmd.extend([f"--from-literal={kubectl_key}={env_vars[env_var]}"])

        # Create the secret first
        if not self.run_kubectl_command(cmd, dry_run):
            return False

        # Add labels separately (only if not dry run, since secret doesn't exist yet in dry run)
        if not dry_run and config["labels"]:
            label_cmd = ["label", "secret", secret_name, "-n", self.namespace]
            for key, value in config["labels"].items():
                label_cmd.append(f"{key}={value}")
            return self.run_kubectl_command(label_cmd, dry_run)
        elif dry_run and config["labels"]:
            # For dry run, show what labels would be added
            label_cmd = ["label", "secret", secret_name, "-n", self.namespace]
            for key, value in config["labels"].items():
                label_cmd.append(f"{key}={value}")
            self.run_kubectl_command(label_cmd, dry_run)

        return True

    def create_or_update_secret(
        self,
        secret_name: str,
        env_vars: dict[str, str],
        update: bool = False,
        dry_run: bool = False,
    ) -> bool:
        """Create a new secret or update an existing one."""
        if update and self.secret_exists(secret_name):
            print(f"Updating secret: {secret_name}")
            if not self.delete_secret(secret_name, dry_run):
                return False
        elif self.secret_exists(secret_name) and not dry_run:
            print(f"Secret {secret_name} already exists. Use --update to update it.")
            return True
        else:
            print(f"Creating secret: {secret_name}")

        return self.create_secret(secret_name, env_vars, dry_run)

    def delete_all_secrets(self, dry_run: bool = False) -> bool:
        """Delete all managed secrets."""
        success = True
        for secret_name in self.secrets_config:
            if self.secret_exists(secret_name) or dry_run:
                print(f"Deleting secret: {secret_name}")
                success &= self.delete_secret(secret_name, dry_run)
            else:
                print(f"Secret {secret_name} does not exist")
        return success

    def validate_environment(self, env_vars: dict[str, str]) -> bool:
        """Validate that all required environment variables are present."""
        missing_vars = []
        for _secret_name, config in self.secrets_config.items():
            for env_var in config["env_vars"]:
                if env_var not in env_vars or not env_vars[env_var]:
                    missing_vars.append(env_var)

        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            return False

        return True

    def manage_secrets(
        self, update: bool = False, dry_run: bool = False, delete: bool = False
    ) -> bool:
        """Main method to manage all secrets."""
        if delete:
            return self.delete_all_secrets(dry_run)

        # Load environment variables
        env_vars = self.load_environment_variables()

        # Validate environment
        if not self.validate_environment(env_vars):
            return False

        if dry_run:
            print("\n=== DRY RUN MODE ===")
            print("Environment variables loaded:")
            for var in env_vars:
                print(f"  {var}: {'*' * len(env_vars[var])}")
            print()

        # Create/update all secrets
        success = True
        for secret_name in self.secrets_config:
            success &= self.create_or_update_secret(secret_name, env_vars, update, dry_run)

        if success and not dry_run:
            print("\n✓ All secrets managed successfully!")
        elif success and dry_run:
            print("\n✓ Dry run completed successfully!")

        return success


def main():
    parser = argparse.ArgumentParser(
        description="Manage Kubernetes secrets from environment variables"
    )
    parser.add_argument(
        "--update", action="store_true", help="Update existing secrets (delete and recreate)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview operations without making changes"
    )
    parser.add_argument("--delete", action="store_true", help="Delete all managed secrets")
    parser.add_argument(
        "--namespace", default="note-rags", help="Kubernetes namespace (default: note-rags)"
    )

    args = parser.parse_args()

    # Change to the script's directory to ensure relative paths work
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    manager = KubernetesSecretManager(namespace=args.namespace)
    success = manager.manage_secrets(update=args.update, dry_run=args.dry_run, delete=args.delete)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
