"""
backend/security/secret_manager.py

Cloud-friendly secret manager.
On Railway (and other cloud platforms), secrets are set as environment
variables in the platform dashboard — no Vault server needed.

Vault is still supported for local development. The fallback chain is:
  1. HashiCorp Vault (if VAULT_ADDR + VAULT_TOKEN are set)
  2. GITHUB_TOKEN environment variable (cloud / CI)
"""

import os


class SecretManager:

    @classmethod
    def get_github_token(cls) -> str:
        """
        Retrieve the GitHub token.
        Tries Vault first (local dev), then falls back to env var (cloud).
        """
        # ── Try Vault first (local dev) ───────────────────────────────────
        vault_addr  = os.environ.get("VAULT_ADDR", "").strip()
        vault_token = os.environ.get("VAULT_TOKEN", "").strip()

        if vault_addr and vault_token:
            try:
                import hvac
                client = hvac.Client(url=vault_addr, token=vault_token)
                if not client.is_authenticated():
                    raise ValueError("Vault token is invalid or expired.")
                secret   = client.secrets.kv.v2.read_secret_version(path="github")
                token    = secret["data"]["data"].get("token", "").strip()
                if token:
                    return token
            except Exception:
                pass  # Fall through to env var

        # ── Fall back to plain environment variable (cloud) ───────────────
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            return token

        raise RuntimeError(
            "GitHub token not found. Set GITHUB_TOKEN as an environment variable "
            "in your Railway dashboard (or VAULT_ADDR + VAULT_TOKEN for local dev)."
        )