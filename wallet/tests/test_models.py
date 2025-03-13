import pytest

from decimal import Decimal
from ..models import Account, Transaction


@pytest.mark.django_db
class TestAccountModel:
    """
    Test suite for the Account model functionality.

    These tests verify:
    - Account balance calculation from transactions
    - Private key encryption and decryption
    - Balance update after various transaction types
    """

    @pytest.fixture
    def account(self):
        """Create and return a test account with an encrypted private key."""
        account = Account.objects.create(
            public_address="0x1234567890abcdef",
        )
        account.encrypt_private_key("test_private_key")
        account.save()
        return account

    def test_initial_balance_is_zero(self, account):
        """Test that a newly created account has a zero balance."""
        assert account.balance == 0

    def test_balance_after_deposit(self, account):
        """Test that a completed deposit transaction increases the account balance."""
        # Create a deposit transaction
        Transaction.objects.create(
            account=account,
            amount=Decimal("100.0"),
            transaction_type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.COMPLETED,
        )

        # Verify balance is updated
        assert account.balance == Decimal("100.0")

    def test_balance_after_withdrawal(self, account):
        """Test that a completed withdrawal transaction decreases the account balance."""
        # First deposit funds
        Transaction.objects.create(
            account=account,
            amount=Decimal("100.0"),
            transaction_type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.COMPLETED,
        )

        # Then withdraw
        Transaction.objects.create(
            account=account,
            amount=Decimal("30.0"),
            transaction_type=Transaction.Type.WITHDRAWAL,
            status=Transaction.Status.COMPLETED,
        )

        # Verify balance is updated correctly
        assert account.balance == Decimal("70.0")

    def test_pending_transactions_do_not_affect_balance(self, account):
        """Test that pending transactions do not affect the account balance."""
        # First deposit funds
        Transaction.objects.create(
            account=account,
            amount=Decimal("100.0"),
            transaction_type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.COMPLETED,
        )

        # Create a pending withdrawal
        Transaction.objects.create(
            account=account,
            amount=Decimal("20.0"),
            transaction_type=Transaction.Type.WITHDRAWAL,
            status=Transaction.Status.PENDING,
        )

        # Balance should still be 100 since the withdrawal is pending
        assert account.balance == Decimal("100.0")

    def test_private_key_encryption(self, account):
        """Test that private keys are properly encrypted and can be decrypted."""
        original_key = "test_private_key"
        account.encrypt_private_key(original_key)
        decrypted_key = account.decrypt_private_key()

        # The decrypted key should match the original
        assert original_key == decrypted_key
        # The stored encrypted key should not match the original
        assert original_key != account.private_key_encrypted


@pytest.mark.django_db
class TestTransactionModel:
    """
    Test suite for the Transaction model functionality.

    These tests verify:
    - Transaction status flow (pending → completed/failed)
    - Transaction rollback functionality
    - Transaction completion with hash
    """

    @pytest.fixture
    def account(self):
        """Create and return a test account."""
        account = Account.objects.create(
            public_address="0x1234567890abcdef",
        )
        account.encrypt_private_key("test_private_key")
        account.save()
        return account

    def test_transaction_complete_flow(self, account):
        """Test the transaction completion flow with a hash."""
        # Create a pending transaction
        tx = Transaction.objects.create(
            account=account,
            amount=Decimal("50.0"),
            transaction_type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.PENDING,
        )

        # Verify initial status
        assert tx.status == Transaction.Status.PENDING

        # Complete the transaction with a hash
        test_hash = "test_hash_123"
        tx.complete(hash=test_hash)

        # Refresh from database
        tx.refresh_from_db()

        # Verify completion
        assert tx.status == Transaction.Status.COMPLETED
        assert tx.hash == test_hash

    def test_completed_transaction_cannot_be_rolled_back(self, account):
        """Test that completed transactions cannot be rolled back."""
        # Create and complete a transaction
        tx = Transaction.objects.create(
            account=account,
            amount=Decimal("50.0"),
            transaction_type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.PENDING,
        )
        tx.complete(hash="test_hash")

        # Try to rollback the completed transaction
        tx.rollback()
        tx.refresh_from_db()

        # Status should still be COMPLETED
        assert tx.status == Transaction.Status.COMPLETED

    def test_pending_transaction_can_be_rolled_back(self, account):
        """Test that pending transactions can be rolled back to failed status."""
        # Create a pending transaction
        tx = Transaction.objects.create(
            account=account,
            amount=Decimal("20.0"),
            transaction_type=Transaction.Type.WITHDRAWAL,
            status=Transaction.Status.PENDING,
        )

        # Rollback the transaction
        tx.rollback()
        tx.refresh_from_db()

        # Status should be FAILED
        assert tx.status == Transaction.Status.FAILED
