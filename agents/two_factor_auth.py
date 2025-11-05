"""
Two-Factor Authentication (2FA) Module
Supports TOTP (Time-based One-Time Password) and backup codes
"""

import pyotp
import qrcode
import io
import base64
import secrets
import string
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json

class TwoFactorAuth:
    """Manage 2FA for users"""

    def __init__(self, db):
        self.db = db
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure 2FA tables exist"""
        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS two_factor_auth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                secret TEXT NOT NULL,
                enabled BOOLEAN DEFAULT FALSE,
                backup_codes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS two_factor_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ip_address TEXT,
                success BOOLEAN,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

    def generate_secret(self, user_id: int, email: str) -> Dict:
        """
        Generate a new 2FA secret for a user

        Args:
            user_id: User ID
            email: User email for QR code

        Returns:
            Dict with secret, QR code, and backup codes
        """
        # Generate secret
        secret = pyotp.random_base32()

        # Generate backup codes
        backup_codes = self._generate_backup_codes()

        # Check if user already has 2FA setup
        existing = self.db.fetch_one(
            "SELECT id FROM two_factor_auth WHERE user_id = ?",
            (user_id,)
        )

        if existing:
            # Update existing record
            self.db.execute_query(
                """
                UPDATE two_factor_auth
                SET secret = ?, backup_codes = ?, enabled = FALSE
                WHERE user_id = ?
                """,
                (secret, json.dumps(backup_codes), user_id)
            )
        else:
            # Create new record
            self.db.execute_query(
                """
                INSERT INTO two_factor_auth (user_id, secret, backup_codes, enabled)
                VALUES (?, ?, ?, FALSE)
                """,
                (user_id, secret, json.dumps(backup_codes))
            )

        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name='AI Assistant Platform'
        )

        qr_code = self._generate_qr_code(totp_uri)

        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes,
            "manual_entry_key": secret
        }

    def _generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(8)
            )
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes

    def _generate_qr_code(self, data: str) -> str:
        """Generate QR code as base64 string"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    def enable_2fa(self, user_id: int, token: str) -> bool:
        """
        Enable 2FA after verifying the initial token

        Args:
            user_id: User ID
            token: TOTP token to verify

        Returns:
            True if enabled successfully
        """
        # Get user's secret
        record = self.db.fetch_one(
            "SELECT secret FROM two_factor_auth WHERE user_id = ? AND enabled = FALSE",
            (user_id,)
        )

        if not record:
            return False

        # Verify token
        if self._verify_totp(record['secret'], token):
            # Enable 2FA
            self.db.execute_query(
                """
                UPDATE two_factor_auth
                SET enabled = TRUE, last_used = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,)
            )
            return True

        return False

    def disable_2fa(self, user_id: int, password: str = None) -> bool:
        """
        Disable 2FA for a user

        Args:
            user_id: User ID
            password: User password for verification (optional)

        Returns:
            True if disabled successfully
        """
        # TODO: Verify password if provided

        # Disable 2FA
        self.db.execute_query(
            """
            UPDATE two_factor_auth
            SET enabled = FALSE
            WHERE user_id = ?
            """,
            (user_id,)
        )

        return True

    def verify_token(self, user_id: int, token: str, ip_address: str = None) -> bool:
        """
        Verify a 2FA token

        Args:
            user_id: User ID
            token: TOTP token or backup code
            ip_address: IP address of the attempt

        Returns:
            True if token is valid
        """
        # Get user's 2FA record
        record = self.db.fetch_one(
            """
            SELECT secret, backup_codes, enabled
            FROM two_factor_auth
            WHERE user_id = ? AND enabled = TRUE
            """,
            (user_id,)
        )

        if not record:
            return False

        success = False

        # Check if it's a TOTP token
        if len(token) == 6 and token.isdigit():
            success = self._verify_totp(record['secret'], token)
            if success:
                # Update last used
                self.db.execute_query(
                    "UPDATE two_factor_auth SET last_used = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,)
                )
        else:
            # Check if it's a backup code
            success = self._verify_backup_code(user_id, token, record['backup_codes'])

        # Log attempt
        self._log_attempt(user_id, ip_address, success)

        return success

    def _verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        # Allow for time drift (±1 time window)
        return totp.verify(token, valid_window=1)

    def _verify_backup_code(self, user_id: int, code: str, backup_codes_json: str) -> bool:
        """Verify and consume backup code"""
        if not backup_codes_json:
            return False

        backup_codes = json.loads(backup_codes_json)

        # Normalize code format
        code = code.upper().replace('-', '')
        normalized_code = f"{code[:4]}-{code[4:]}" if len(code) == 8 else code

        if normalized_code in backup_codes:
            # Remove used code
            backup_codes.remove(normalized_code)

            # Update backup codes
            self.db.execute_query(
                """
                UPDATE two_factor_auth
                SET backup_codes = ?
                WHERE user_id = ?
                """,
                (json.dumps(backup_codes), user_id)
            )

            return True

        return False

    def _log_attempt(self, user_id: int, ip_address: str, success: bool):
        """Log 2FA attempt"""
        self.db.execute_query(
            """
            INSERT INTO two_factor_attempts (user_id, ip_address, success)
            VALUES (?, ?, ?)
            """,
            (user_id, ip_address, success)
        )

    def is_2fa_enabled(self, user_id: int) -> bool:
        """Check if 2FA is enabled for a user"""
        record = self.db.fetch_one(
            "SELECT enabled FROM two_factor_auth WHERE user_id = ?",
            (user_id,)
        )
        return record and record['enabled']

    def get_backup_codes(self, user_id: int) -> List[str]:
        """Get remaining backup codes for a user"""
        record = self.db.fetch_one(
            "SELECT backup_codes FROM two_factor_auth WHERE user_id = ?",
            (user_id,)
        )

        if record and record['backup_codes']:
            return json.loads(record['backup_codes'])

        return []

    def regenerate_backup_codes(self, user_id: int) -> List[str]:
        """Regenerate backup codes for a user"""
        new_codes = self._generate_backup_codes()

        self.db.execute_query(
            """
            UPDATE two_factor_auth
            SET backup_codes = ?
            WHERE user_id = ?
            """,
            (json.dumps(new_codes), user_id)
        )

        return new_codes

    def get_recent_attempts(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent 2FA attempts for a user"""
        attempts = self.db.fetch_all(
            """
            SELECT ip_address, success, attempted_at
            FROM two_factor_attempts
            WHERE user_id = ?
            ORDER BY attempted_at DESC
            LIMIT ?
            """,
            (user_id, limit)
        )

        return [dict(attempt) for attempt in attempts]

    def check_rate_limit(self, user_id: int, ip_address: str, window_minutes: int = 5, max_attempts: int = 5) -> bool:
        """
        Check if user has exceeded rate limit for 2FA attempts

        Args:
            user_id: User ID
            ip_address: IP address
            window_minutes: Time window in minutes
            max_attempts: Maximum attempts allowed

        Returns:
            True if within rate limit, False if exceeded
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        count = self.db.fetch_one(
            """
            SELECT COUNT(*) as count
            FROM two_factor_attempts
            WHERE user_id = ? AND ip_address = ?
            AND attempted_at > ? AND success = FALSE
            """,
            (user_id, ip_address, cutoff_time.isoformat())
        )

        return count['count'] < max_attempts if count else True