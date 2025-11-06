"""
Secrets Management System
Enterprise-grade secrets and credentials management
Supports: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, Environment Variables
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend


logger = logging.getLogger(__name__)


class SecretType(Enum):
    """Types of secrets"""
    API_KEY = "api_key"
    DATABASE_URL = "database_url"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    OAUTH_CLIENT_SECRET = "oauth_client_secret"
    WEBHOOK_SECRET = "webhook_secret"
    SERVICE_ACCOUNT_KEY = "service_account_key"
    TLS_CERTIFICATE = "tls_certificate"
    TLS_PRIVATE_KEY = "tls_private_key"


class SecretProvider(Enum):
    """Secret storage providers"""
    ENVIRONMENT = "environment"
    VAULT = "vault"  # HashiCorp Vault
    AWS_SECRETS = "aws_secrets_manager"
    AZURE_KEYVAULT = "azure_keyvault"
    GCP_SECRET_MANAGER = "gcp_secret_manager"
    FILE = "file"  # Encrypted file


@dataclass
class Secret:
    """Secret data structure"""
    name: str
    value: str
    secret_type: SecretType
    provider: SecretProvider
    version: str
    created_at: str
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SecretsManager:
    """
    Unified secrets management interface

    Features:
    - Multiple provider support (Vault, AWS, Azure, GCP)
    - Automatic rotation
    - Version control
    - Encryption at rest
    - Audit logging
    - Caching with TTL
    """

    def __init__(self, provider: SecretProvider = SecretProvider.ENVIRONMENT):
        self.provider = provider
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self._encryption_key = self._get_encryption_key()
        self._cipher = Fernet(self._encryption_key) if self._encryption_key else None

    def _get_encryption_key(self) -> Optional[bytes]:
        """Get or generate encryption key for local secrets"""
        key_env = os.getenv("SECRETS_ENCRYPTION_KEY")
        if key_env:
            return base64.urlsafe_b64decode(key_env)

        # Generate key from password if available
        password = os.getenv("SECRETS_PASSWORD")
        if password:
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'aiassistant-salt',  # In production, use random salt
                iterations=100000,
                backend=default_backend()
            )
            return base64.urlsafe_b64encode(kdf.derive(password.encode()))

        return None

    async def get_secret(
        self,
        secret_name: str,
        secret_type: Optional[SecretType] = None,
        version: str = "latest"
    ) -> Optional[str]:
        """
        Get secret value

        Args:
            secret_name: Name of the secret
            secret_type: Type of secret
            version: Secret version (default: latest)

        Returns:
            Secret value or None if not found
        """
        cache_key = f"{secret_name}:{version}"

        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached["expires_at"] > time.time():
                logger.debug(f"Secret '{secret_name}' retrieved from cache")
                return cached["value"]

        # Retrieve from provider
        secret_value = None

        if self.provider == SecretProvider.ENVIRONMENT:
            secret_value = self._get_from_environment(secret_name)

        elif self.provider == SecretProvider.VAULT:
            secret_value = await self._get_from_vault(secret_name, version)

        elif self.provider == SecretProvider.AWS_SECRETS:
            secret_value = await self._get_from_aws_secrets(secret_name, version)

        elif self.provider == SecretProvider.AZURE_KEYVAULT:
            secret_value = await self._get_from_azure_keyvault(secret_name, version)

        elif self.provider == SecretProvider.GCP_SECRET_MANAGER:
            secret_value = await self._get_from_gcp_secrets(secret_name, version)

        elif self.provider == SecretProvider.FILE:
            secret_value = self._get_from_file(secret_name)

        if secret_value:
            # Cache the secret
            import time
            self.cache[cache_key] = {
                "value": secret_value,
                "expires_at": time.time() + self.cache_ttl
            }
            logger.info(f"Secret '{secret_name}' retrieved successfully")

        return secret_value

    async def set_secret(
        self,
        secret_name: str,
        secret_value: str,
        secret_type: SecretType,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store or update a secret

        Args:
            secret_name: Name of the secret
            secret_value: Secret value
            secret_type: Type of secret
            expires_at: Expiration date (ISO format)
            metadata: Additional metadata

        Returns:
            True if successful
        """
        try:
            if self.provider == SecretProvider.ENVIRONMENT:
                raise ValueError("Cannot set secrets in environment provider")

            elif self.provider == SecretProvider.VAULT:
                success = await self._set_in_vault(secret_name, secret_value, metadata)

            elif self.provider == SecretProvider.AWS_SECRETS:
                success = await self._set_in_aws_secrets(secret_name, secret_value, metadata)

            elif self.provider == SecretProvider.AZURE_KEYVAULT:
                success = await self._set_in_azure_keyvault(secret_name, secret_value, metadata)

            elif self.provider == SecretProvider.FILE:
                success = self._set_in_file(secret_name, secret_value, metadata)

            else:
                success = False

            if success:
                logger.info(f"Secret '{secret_name}' stored successfully")
                # Invalidate cache
                self._invalidate_cache(secret_name)

            return success

        except Exception as e:
            logger.error(f"Failed to set secret '{secret_name}': {e}")
            return False

    async def delete_secret(self, secret_name: str) -> bool:
        """
        Delete a secret

        Args:
            secret_name: Name of the secret to delete

        Returns:
            True if successful
        """
        try:
            if self.provider == SecretProvider.VAULT:
                success = await self._delete_from_vault(secret_name)
            elif self.provider == SecretProvider.AWS_SECRETS:
                success = await self._delete_from_aws_secrets(secret_name)
            elif self.provider == SecretProvider.AZURE_KEYVAULT:
                success = await self._delete_from_azure_keyvault(secret_name)
            else:
                success = False

            if success:
                logger.info(f"Secret '{secret_name}' deleted successfully")
                self._invalidate_cache(secret_name)

            return success

        except Exception as e:
            logger.error(f"Failed to delete secret '{secret_name}': {e}")
            return False

    async def rotate_secret(
        self,
        secret_name: str,
        new_value: str
    ) -> bool:
        """
        Rotate a secret (create new version, keep old version for grace period)

        Args:
            secret_name: Name of the secret
            new_value: New secret value

        Returns:
            True if successful
        """
        logger.info(f"Rotating secret '{secret_name}'")

        try:
            # Get current secret
            old_value = await self.get_secret(secret_name)

            # Store new version
            success = await self.set_secret(
                secret_name,
                new_value,
                SecretType.API_KEY,  # Default type
                metadata={"rotated": True, "rotation_date": datetime.utcnow().isoformat()}
            )

            if success:
                logger.info(f"Secret '{secret_name}' rotated successfully")
                # Audit the rotation
                await self._audit_secret_rotation(secret_name)

            return success

        except Exception as e:
            logger.error(f"Failed to rotate secret '{secret_name}': {e}")
            return False

    def _invalidate_cache(self, secret_name: str):
        """Invalidate cached secret"""
        keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{secret_name}:")]
        for key in keys_to_remove:
            del self.cache[key]

    # Provider implementations

    def _get_from_environment(self, secret_name: str) -> Optional[str]:
        """Get secret from environment variables"""
        return os.getenv(secret_name)

    async def _get_from_vault(self, secret_name: str, version: str) -> Optional[str]:
        """Get secret from HashiCorp Vault"""
        try:
            import hvac

            vault_url = os.getenv("VAULT_ADDR", "http://localhost:8200")
            vault_token = os.getenv("VAULT_TOKEN")

            if not vault_token:
                logger.error("VAULT_TOKEN not configured")
                return None

            client = hvac.Client(url=vault_url, token=vault_token)

            if not client.is_authenticated():
                logger.error("Vault authentication failed")
                return None

            # Read secret
            secret_path = f"secret/data/{secret_name}"
            response = client.secrets.kv.v2.read_secret_version(
                path=secret_name,
                version=None if version == "latest" else int(version)
            )

            return response["data"]["data"]["value"]

        except Exception as e:
            logger.error(f"Failed to get secret from Vault: {e}")
            return None

    async def _set_in_vault(
        self,
        secret_name: str,
        secret_value: str,
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Set secret in HashiCorp Vault"""
        try:
            import hvac

            vault_url = os.getenv("VAULT_ADDR", "http://localhost:8200")
            vault_token = os.getenv("VAULT_TOKEN")

            client = hvac.Client(url=vault_url, token=vault_token)

            # Write secret
            client.secrets.kv.v2.create_or_update_secret(
                path=secret_name,
                secret={"value": secret_value, **(metadata or {})}
            )

            return True

        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            return False

    async def _delete_from_vault(self, secret_name: str) -> bool:
        """Delete secret from Vault"""
        try:
            import hvac

            vault_url = os.getenv("VAULT_ADDR")
            vault_token = os.getenv("VAULT_TOKEN")

            client = hvac.Client(url=vault_url, token=vault_token)
            client.secrets.kv.v2.delete_metadata_and_all_versions(path=secret_name)

            return True

        except Exception as e:
            logger.error(f"Failed to delete secret from Vault: {e}")
            return False

    async def _get_from_aws_secrets(self, secret_name: str, version: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            import boto3

            session = boto3.session.Session()
            client = session.client(service_name='secretsmanager')

            response = client.get_secret_value(
                SecretId=secret_name,
                VersionId=version if version != "latest" else None
            )

            return response.get('SecretString')

        except Exception as e:
            logger.error(f"Failed to get secret from AWS: {e}")
            return None

    async def _set_in_aws_secrets(
        self,
        secret_name: str,
        secret_value: str,
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Set secret in AWS Secrets Manager"""
        try:
            import boto3

            client = boto3.client('secretsmanager')

            try:
                # Try to update existing secret
                client.put_secret_value(
                    SecretId=secret_name,
                    SecretString=secret_value
                )
            except client.exceptions.ResourceNotFoundException:
                # Create new secret
                client.create_secret(
                    Name=secret_name,
                    SecretString=secret_value
                )

            return True

        except Exception as e:
            logger.error(f"Failed to set secret in AWS: {e}")
            return False

    async def _delete_from_aws_secrets(self, secret_name: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        try:
            import boto3

            client = boto3.client('secretsmanager')
            client.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=True
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete secret from AWS: {e}")
            return False

    async def _get_from_azure_keyvault(self, secret_name: str, version: str) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            vault_url = os.getenv("AZURE_KEYVAULT_URL")
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)

            secret = client.get_secret(
                secret_name,
                version=version if version != "latest" else None
            )

            return secret.value

        except Exception as e:
            logger.error(f"Failed to get secret from Azure: {e}")
            return None

    async def _set_in_azure_keyvault(
        self,
        secret_name: str,
        secret_value: str,
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Set secret in Azure Key Vault"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            vault_url = os.getenv("AZURE_KEYVAULT_URL")
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)

            client.set_secret(secret_name, secret_value)

            return True

        except Exception as e:
            logger.error(f"Failed to set secret in Azure: {e}")
            return False

    async def _delete_from_azure_keyvault(self, secret_name: str) -> bool:
        """Delete secret from Azure Key Vault"""
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            vault_url = os.getenv("AZURE_KEYVAULT_URL")
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)

            client.begin_delete_secret(secret_name)

            return True

        except Exception as e:
            logger.error(f"Failed to delete secret from Azure: {e}")
            return False

    async def _get_from_gcp_secrets(self, secret_name: str, version: str) -> Optional[str]:
        """Get secret from GCP Secret Manager"""
        try:
            from google.cloud import secretmanager

            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("GCP_PROJECT_ID")

            name = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
            response = client.access_secret_version(request={"name": name})

            return response.payload.data.decode('UTF-8')

        except Exception as e:
            logger.error(f"Failed to get secret from GCP: {e}")
            return None

    def _get_from_file(self, secret_name: str) -> Optional[str]:
        """Get secret from encrypted file"""
        try:
            secrets_file = os.getenv("SECRETS_FILE", ".secrets.enc")

            if not os.path.exists(secrets_file):
                return None

            with open(secrets_file, 'rb') as f:
                encrypted_data = f.read()

            if self._cipher:
                decrypted_data = self._cipher.decrypt(encrypted_data)
                secrets = json.loads(decrypted_data.decode())
                return secrets.get(secret_name)

            return None

        except Exception as e:
            logger.error(f"Failed to get secret from file: {e}")
            return None

    def _set_in_file(
        self,
        secret_name: str,
        secret_value: str,
        metadata: Optional[Dict[str, Any]]
    ) -> bool:
        """Set secret in encrypted file"""
        try:
            secrets_file = os.getenv("SECRETS_FILE", ".secrets.enc")
            secrets = {}

            # Load existing secrets
            if os.path.exists(secrets_file):
                with open(secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                if self._cipher:
                    decrypted_data = self._cipher.decrypt(encrypted_data)
                    secrets = json.loads(decrypted_data.decode())

            # Add/update secret
            secrets[secret_name] = secret_value

            # Encrypt and save
            if self._cipher:
                encrypted_data = self._cipher.encrypt(json.dumps(secrets).encode())
                with open(secrets_file, 'wb') as f:
                    f.write(encrypted_data)

            return True

        except Exception as e:
            logger.error(f"Failed to set secret in file: {e}")
            return False

    async def _audit_secret_rotation(self, secret_name: str):
        """Audit secret rotation"""
        from api.audit.audit_logger import audit_logger, AuditEventType

        await audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            action=f"Secret rotated: {secret_name}",
            details={"secret_name": secret_name, "action": "rotation"}
        )


# Global secrets manager instance
secrets_manager = SecretsManager(
    provider=SecretProvider(os.getenv("SECRETS_PROVIDER", "environment"))
)


# Convenience functions
async def get_database_url() -> str:
    """Get database URL from secrets"""
    return await secrets_manager.get_secret("DATABASE_URL", SecretType.DATABASE_URL) or ""


async def get_jwt_secret() -> str:
    """Get JWT secret from secrets"""
    return await secrets_manager.get_secret("JWT_SECRET_KEY", SecretType.JWT_SECRET) or ""


async def get_api_key(service: str) -> Optional[str]:
    """Get API key for external service"""
    return await secrets_manager.get_secret(f"{service.upper()}_API_KEY", SecretType.API_KEY)
