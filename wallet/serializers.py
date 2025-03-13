from rest_framework import serializers
from .models import Account, Transaction
import secrets
import string


class AccountSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(read_only=True, max_digits=24, decimal_places=8)

    class Meta:
        model = Account
        fields = ["id", "public_address", "balance", "created_at"]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        # Generate a random private key (in a real app, use proper key generation)
        alphabet = string.ascii_letters + string.digits
        private_key = "".join(secrets.choice(alphabet) for _ in range(64))

        account = Account(**validated_data)
        account.encrypt_private_key(private_key)
        account.save()

        # Return the private key to the caller, it won't be saved in plain text
        self.context["private_key"] = private_key

        return account


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "from_account",
            "to_account",
            "amount",
            "transaction_type",
            "status",
            "hash",
            "created_at",
        ]
        read_only_fields = ["id", "status", "hash", "created_at"]


class DepositSerializer(serializers.Serializer):
    to_account = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=24, decimal_places=8)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value

    def validate_to_account(self, value):
        try:
            return Account.objects.get(id=value)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist")


class WithdrawSerializer(serializers.Serializer):
    from_account = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=24, decimal_places=8)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value

    def validate(self, data):
        try:
            account = Account.objects.get(id=data["from_account"])
            data["from_account"] = account
        except Account.DoesNotExist:
            raise serializers.ValidationError(
                {"from_account": "Account does not exist"}
            )

        if account.balance < data["amount"]:
            raise serializers.ValidationError({"amount": "Insufficient funds"})

        return data
