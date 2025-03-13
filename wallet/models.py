import os
import base64
from cryptography.fernet import Fernet

from django.db import models
from django.conf import settings
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError

from common.models import BaseModel

# Generate a key for encryption if it doesn't exist
if not hasattr(settings, "ENCRYPTION_KEY"):
    settings.ENCRYPTION_KEY = base64.urlsafe_b64encode(os.urandom(32))


class Account(BaseModel):
    """
    Represents a blockchain wallet account
    """

    public_address = models.CharField(max_length=255, unique=True)
    private_key_encrypted = models.TextField()

    @property
    def balance(self):
        """
        Calculate balance from transactions, not storing it directly
        """
        # aggregate queries for withdraw and deposits for performance
        total = Transaction.objects.filter(
            account=self,
            status=Transaction.Status.COMPLETED,
        ).aggregate(
            total_deposits=Sum(
                "amount", filter=Q(transaction_type=Transaction.Type.DEPOSIT)
            ),
            total_withdrawals=Sum(
                "amount", filter=Q(transaction_type=Transaction.Type.WITHDRAWAL)
            ),
        )
        return (total["total_deposits"] or 0) - (total["total_withdrawals"] or 0)

    def encrypt_private_key(self, private_key):
        """
        Encrypt the private key before storing
        """
        f = Fernet(settings.ENCRYPTION_KEY)
        encrypted_key = f.encrypt(private_key.encode())
        self.private_key_encrypted = encrypted_key.decode()

    def decrypt_private_key(self):
        """
        Decrypt the private key for use
        """
        f = Fernet(settings.ENCRYPTION_KEY)
        return f.decrypt(self.private_key_encrypted.encode()).decode()

    def __str__(self):
        return f"Account {self.public_address}"


class Transaction(BaseModel):
    """
    Represents a transaction in the blockchain
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL = "withdrawal", "Withdrawal"

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="account_transactions",
        null=True,
        blank=True,
        db_index=True,
    )
    amount = models.DecimalField(max_digits=24, decimal_places=8)
    transaction_type = models.CharField(max_length=20, choices=Type.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    hash = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        # Validate transaction
        if self.amount <= 0:
            raise ValidationError("Amount must be positive")

        if self.transaction_type == self.Type.DEPOSIT and not self.account:
            raise ValidationError(
                "Deposit transactions must have a destination account"
            )

        if self.transaction_type == self.Type.WITHDRAWAL and not self.account:
            raise ValidationError("Withdrawal transactions must have a source account")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def rollback(self):
        """
        Rollback a transaction by marking it as failed
        """
        if self.status == self.Status.PENDING:
            self.status = self.Status.FAILED
            self.save()

    def complete(self, hash=None):
        """
        Mark a transaction as completed with optional hash
        """
        if self.status == self.Status.PENDING:
            self.status = self.Status.COMPLETED
            if hash:
                self.hash = hash
            self.save()

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.status}"
