"""
Credit Manager Module
Handles user credit operations including balance, purchases, spending, and transactions
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "history.db"


class CreditManager:
    """Manages user credit operations"""

    def __init__(self, db_path: str = str(DB_PATH)):
        """Initialize credit manager with database connection"""
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    # ============= BALANCE OPERATIONS =============

    def get_balance(self, user_id: int) -> int:
        """
        Get user's current credit balance

        Args:
            user_id: User ID

        Returns:
            Current credit balance (0 if user has no credits record)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT balance FROM user_credits WHERE user_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            return result['balance'] if result else 0

    def get_credit_stats(self, user_id: int) -> Dict:
        """
        Get comprehensive credit statistics for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with balance, total_purchased, total_spent, created_at, updated_at
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT user_id, balance, total_purchased, total_spent,
                          created_at, updated_at
                   FROM user_credits
                   WHERE user_id = ?""",
                (user_id,)
            )
            result = cursor.fetchone()

            if result:
                return dict(result)
            else:
                # Return default stats if user has no credit record
                return {
                    'user_id': user_id,
                    'balance': 0,
                    'total_purchased': 0,
                    'total_spent': 0,
                    'created_at': None,
                    'updated_at': None
                }

    def has_sufficient_credits(self, user_id: int, required_credits: int) -> bool:
        """
        Check if user has enough credits for an operation

        Args:
            user_id: User ID
            required_credits: Number of credits needed

        Returns:
            True if user has sufficient credits, False otherwise
        """
        balance = self.get_balance(user_id)
        return balance >= required_credits

    # ============= TRANSACTION OPERATIONS =============

    def add_credits(
        self,
        user_id: int,
        amount: int,
        description: str = None,
        payment_id: int = None,
        metadata: Dict = None
    ) -> bool:
        """
        Add credits to user account (purchase, bonus, refund)

        Args:
            user_id: User ID
            amount: Number of credits to add (must be positive)
            description: Transaction description
            payment_id: Associated payment ID (optional)
            metadata: Additional metadata as dictionary (optional)

        Returns:
            True if successful, False otherwise
        """
        if amount <= 0:
            logger.error(f"Cannot add non-positive credits: {amount}")
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get current balance
                balance_before = self.get_balance(user_id)
                balance_after = balance_before + amount

                # Check if user_credits record exists
                cursor.execute(
                    "SELECT id FROM user_credits WHERE user_id = ?",
                    (user_id,)
                )
                exists = cursor.fetchone()

                if exists:
                    # Update existing record
                    cursor.execute("""
                        UPDATE user_credits
                        SET balance = balance + ?,
                            total_purchased = total_purchased + ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (amount, amount, user_id))
                else:
                    # Create new record
                    cursor.execute("""
                        INSERT INTO user_credits
                        (user_id, balance, total_purchased, total_spent)
                        VALUES (?, ?, ?, 0)
                    """, (user_id, amount, amount))

                # Record transaction
                import json
                metadata_json = json.dumps(metadata) if metadata else None

                cursor.execute("""
                    INSERT INTO credit_transactions
                    (user_id, type, amount, balance_before, balance_after,
                     description, payment_id, metadata)
                    VALUES (?, 'purchase', ?, ?, ?, ?, ?, ?)
                """, (user_id, amount, balance_before, balance_after,
                      description, payment_id, metadata_json))

                conn.commit()

                logger.info(
                    f"Added {amount} credits to user {user_id}. "
                    f"Balance: {balance_before} → {balance_after}"
                )
                return True

        except Exception as e:
            logger.error(f"Error adding credits: {e}")
            return False

    def charge_credits(
        self,
        user_id: int,
        amount: int,
        description: str = None,
        request_id: int = None,
        metadata: Dict = None
    ) -> bool:
        """
        Deduct credits from user account (for AI requests)

        Args:
            user_id: User ID
            amount: Number of credits to charge (must be positive)
            description: Transaction description
            request_id: Associated AI request ID (optional)
            metadata: Additional metadata as dictionary (optional)

        Returns:
            True if successful, False if insufficient balance or error
        """
        if amount <= 0:
            logger.error(f"Cannot charge non-positive credits: {amount}")
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get current balance
                balance_before = self.get_balance(user_id)

                # Check sufficient balance
                if balance_before < amount:
                    logger.warning(
                        f"Insufficient credits for user {user_id}. "
                        f"Required: {amount}, Available: {balance_before}"
                    )
                    return False

                balance_after = balance_before - amount

                # Deduct credits
                cursor.execute("""
                    UPDATE user_credits
                    SET balance = balance - ?,
                        total_spent = total_spent + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, amount, user_id))

                # Record transaction
                import json
                metadata_json = json.dumps(metadata) if metadata else None

                cursor.execute("""
                    INSERT INTO credit_transactions
                    (user_id, type, amount, balance_before, balance_after,
                     description, request_id, metadata)
                    VALUES (?, 'spend', ?, ?, ?, ?, ?, ?)
                """, (user_id, -amount, balance_before, balance_after,
                      description, request_id, metadata_json))

                conn.commit()

                logger.info(
                    f"Charged {amount} credits from user {user_id}. "
                    f"Balance: {balance_before} → {balance_after}"
                )
                return True

        except Exception as e:
            logger.error(f"Error charging credits: {e}")
            return False

    def refund_credits(
        self,
        user_id: int,
        amount: int,
        description: str = None,
        original_request_id: int = None
    ) -> bool:
        """
        Refund credits to user account (e.g., for failed requests)

        Args:
            user_id: User ID
            amount: Number of credits to refund (must be positive)
            description: Refund reason
            original_request_id: ID of the request being refunded

        Returns:
            True if successful, False otherwise
        """
        if amount <= 0:
            logger.error(f"Cannot refund non-positive credits: {amount}")
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get current balance
                balance_before = self.get_balance(user_id)
                balance_after = balance_before + amount

                # Add credits back
                cursor.execute("""
                    UPDATE user_credits
                    SET balance = balance + ?,
                        total_spent = total_spent - ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, amount, user_id))

                # Record transaction
                cursor.execute("""
                    INSERT INTO credit_transactions
                    (user_id, type, amount, balance_before, balance_after,
                     description, request_id)
                    VALUES (?, 'refund', ?, ?, ?, ?, ?)
                """, (user_id, amount, balance_before, balance_after,
                      description, original_request_id))

                conn.commit()

                logger.info(
                    f"Refunded {amount} credits to user {user_id}. "
                    f"Balance: {balance_before} → {balance_after}"
                )
                return True

        except Exception as e:
            logger.error(f"Error refunding credits: {e}")
            return False

    # ============= TRANSACTION HISTORY =============

    def get_transaction_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get transaction history for a user

        Args:
            user_id: User ID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip (for pagination)
            transaction_type: Filter by type ('purchase', 'spend', 'refund', 'bonus')

        Returns:
            List of transaction dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, user_id, type, amount, balance_before, balance_after,
                       description, request_id, payment_id, metadata, created_at
                FROM credit_transactions
                WHERE user_id = ?
            """
            params = [user_id]

            if transaction_type:
                query += " AND type = ?"
                params.append(transaction_type)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [dict(row) for row in results]

    def get_total_transactions_count(
        self,
        user_id: int,
        transaction_type: Optional[str] = None
    ) -> int:
        """
        Get total count of transactions for pagination

        Args:
            user_id: User ID
            transaction_type: Filter by type (optional)

        Returns:
            Total number of transactions
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT COUNT(*) as count FROM credit_transactions WHERE user_id = ?"
            params = [user_id]

            if transaction_type:
                query += " AND type = ?"
                params.append(transaction_type)

            cursor.execute(query, params)
            result = cursor.fetchone()
            return result['count'] if result else 0

    # ============= PACKAGE OPERATIONS =============

    def get_credit_packages(self, active_only: bool = True) -> List[Dict]:
        """
        Get available credit packages

        Args:
            active_only: Only return active packages

        Returns:
            List of package dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, name, credits, price_usd, bonus_credits,
                       discount_percentage, description, display_order
                FROM credit_packages
            """

            if active_only:
                query += " WHERE is_active = 1"

            query += " ORDER BY display_order ASC"

            cursor.execute(query)
            results = cursor.fetchall()

            packages = []
            for row in results:
                package = dict(row)
                # Calculate total credits (base + bonus)
                package['total_credits'] = package['credits'] + package['bonus_credits']
                # Calculate price per credit
                package['price_per_credit'] = package['price_usd'] / package['total_credits']
                packages.append(package)

            return packages

    def get_package_by_id(self, package_id: int) -> Optional[Dict]:
        """
        Get a specific credit package by ID

        Args:
            package_id: Package ID

        Returns:
            Package dictionary or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, credits, price_usd, bonus_credits,
                       discount_percentage, description, is_active
                FROM credit_packages
                WHERE id = ?
            """, (package_id,))

            result = cursor.fetchone()
            if result:
                package = dict(result)
                package['total_credits'] = package['credits'] + package['bonus_credits']
                return package
            return None

    # ============= ADMIN OPERATIONS =============

    def grant_bonus_credits(
        self,
        user_id: int,
        amount: int,
        description: str = "Admin bonus"
    ) -> bool:
        """
        Grant bonus credits to a user (admin function)

        Args:
            user_id: User ID
            amount: Number of credits to grant
            description: Reason for bonus

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                balance_before = self.get_balance(user_id)
                balance_after = balance_before + amount

                # Update balance
                cursor.execute("""
                    UPDATE user_credits
                    SET balance = balance + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (amount, user_id))

                # If user doesn't have credits record yet, create it
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO user_credits
                        (user_id, balance, total_purchased, total_spent)
                        VALUES (?, ?, 0, 0)
                    """, (user_id, amount))

                # Record transaction
                cursor.execute("""
                    INSERT INTO credit_transactions
                    (user_id, type, amount, balance_before, balance_after, description)
                    VALUES (?, 'bonus', ?, ?, ?, ?)
                """, (user_id, amount, balance_before, balance_after, description))

                conn.commit()
                logger.info(f"Granted {amount} bonus credits to user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Error granting bonus credits: {e}")
            return False


# Convenience function for quick access
def get_credit_manager() -> CreditManager:
    """Get CreditManager instance"""
    return CreditManager()
