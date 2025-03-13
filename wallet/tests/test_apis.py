import uuid
import pytest
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAccountAPI:
    """
    Test suite for Account API endpoints.

    These tests verify:
    - Account creation
    - Account retrieval
    - Balance retrieval
    - Transaction history retrieval
    """

    @pytest.fixture
    def client(self):
        """Create and return an API client."""
        return APIClient()

    def test_account_creation(self, client):
        """Test creating a new account via the API."""
        response = client.post("/accounts/", {"public_address": "0xabcdef1234567890"})

        # Check response status and data
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert "private_key" in response.data
        assert response.data["public_address"] == "0xabcdef1234567890"
        assert response.data["balance"] == "0.00000000"

    def test_account_retrieval(self, client):
        """Test retrieving an account via the API."""
        # First create an account
        create_response = client.post(
            "/accounts/", {"public_address": "0xretrieval_test_account"}
        )
        account_id = create_response.data["id"]

        # Then retrieve it
        response = client.get(f"/accounts/{account_id}/")

        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == account_id
        assert response.data["public_address"] == "0xretrieval_test_account"

    def test_account_balance(self, client):
        """Test retrieving an account's balance via the API."""
        # Create an account
        create_response = client.post(
            "/accounts/", {"public_address": "0xbalance_test_account"}
        )
        account_id = create_response.data["id"]

        # Get balance
        response = client.get(f"/accounts/{account_id}/balance/")

        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert "balance" in response.data
        assert response.data["balance"] == 0

    def test_account_transactions(self, client):
        """Test retrieving an account's transaction history via the API."""
        # Create an account
        create_response = client.post(
            "/accounts/", {"public_address": "0xtx_history_test_account"}
        )
        account_id = create_response.data["id"]

        # First make a deposit
        client.post(
            "/transactions/deposit/", {"to_account": account_id, "amount": "100.5"}
        )

        # Then get transaction history
        response = client.get(f"/accounts/{account_id}/transactions/")

        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["transaction_type"] == "deposit"
        assert response.data[0]["amount"] == "100.50000000"


@pytest.mark.django_db
class TestTransactionAPI:
    """
    Test suite for Transaction API endpoints.

    These tests verify:
    - Deposit functionality
    - Withdrawal functionality
    - Withdrawal validation (insufficient funds)
    - Transaction listing
    """

    @pytest.fixture
    def client(self):
        """Create and return an API client."""
        return APIClient()

    @pytest.fixture
    def account(self, client):
        """Create and return a test account."""
        response = client.post(
            "/accounts/", {"public_address": "0xtransaction_test_account"}
        )
        return response.data["id"]

    def test_deposit(self, client, account):
        """Test making a deposit via the API."""
        response = client.post(
            "/transactions/deposit/", {"to_account": account, "amount": "100.5"}
        )

        # Check response
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["transaction_type"] == "deposit"
        assert response.data["amount"] == "100.50000000"
        assert response.data["status"] == "completed"

        # Check balance was updated
        balance_response = client.get(f"/accounts/{account}/balance/")
        assert balance_response.data["balance"] == Decimal("100.5")

    def test_withdrawal(self, client, account):
        """Test making a withdrawal via the API."""
        # First deposit some funds
        client.post(
            "/transactions/deposit/", {"to_account": account, "amount": "100.0"}
        )

        # Then make a withdrawal
        response = client.post(
            "/transactions/withdraw/", {"from_account": account, "amount": "50.0"}
        )

        # Check response
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["transaction_type"] == "withdrawal"
        assert response.data["amount"] == "50.00000000"
        assert response.data["status"] == "completed"

        # Check balance was updated
        balance_response = client.get(f"/accounts/{account}/balance/")
        assert balance_response.data["balance"] == Decimal("50")

    def test_insufficient_funds(self, client, account):
        """Test that withdrawals fail properly when there are insufficient funds."""
        # Try to withdraw without funds
        response = client.post(
            "/transactions/withdraw/", {"from_account": account, "amount": "50.0"}
        )

        # Check that the request was rejected
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "amount" in response.data
        assert "Insufficient funds" in response.data["amount"][0]

    def test_transaction_listing(self, client, account):
        """Test retrieving the list of all transactions via the API."""
        # Create some transactions
        client.post(
            "/transactions/deposit/", {"to_account": account, "amount": "100.0"}
        )

        client.post(
            "/transactions/withdraw/", {"from_account": account, "amount": "30.0"}
        )

        # Get transaction list
        response = client.get("/transactions/")

        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        # Sort by type to check both transactions
        tx_by_type = {tx["transaction_type"]: tx for tx in response.data}
        assert "deposit" in tx_by_type
        assert "withdrawal" in tx_by_type
        assert tx_by_type["deposit"]["amount"] == "100.00000000"
        assert tx_by_type["withdrawal"]["amount"] == "30.00000000"


@pytest.mark.django_db
class TestEdgeCases:
    """
    Test suite for edge cases and error handling.

    These tests verify:
    - Negative amount validation
    - Invalid account handling
    - Transaction status transitions
    """

    @pytest.fixture
    def client(self):
        """Create and return an API client."""
        return APIClient()

    @pytest.fixture
    def account(self, client):
        """Create and return a test account."""
        response = client.post(
            "/accounts/", {"public_address": "0xedge_case_test_account"}
        )
        return response.data["id"]

    def test_negative_amount_deposit(self, client, account):
        """Test that deposits with negative amounts are rejected."""
        response = client.post(
            "/transactions/deposit/", {"to_account": account, "amount": "-50.0"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "amount" in response.data

    def test_nonexistent_account(self, client):
        """Test handling of transactions with non-existent accounts."""
        fake_uuid = str(uuid.uuid4())
        response = client.post(
            "/transactions/deposit/", {"to_account": fake_uuid, "amount": "50.0"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "to_account" in response.data

    def test_zero_amount_transaction(self, client, account):
        """Test that transactions with zero amounts are rejected."""
        response = client.post(
            "/transactions/deposit/", {"to_account": account, "amount": "0.0"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "amount" in response.data
