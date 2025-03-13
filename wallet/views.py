from django.db.models import Q
from django.db import transaction

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Account, Transaction
from .serializers import (
    AccountSerializer,
    TransactionSerializer,
    DepositSerializer,
    WithdrawSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing blockchain accounts
    """

    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Include private key in response (only during creation)
        response_data = serializer.data
        if "private_key" in serializer.context:
            response_data["private_key"] = serializer.context["private_key"]

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        """
        Get the current balance of an account
        """
        account = self.get_object()
        return Response({"balance": account.balance})

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """
        Get transaction history for an account
        """
        account = self.get_object()

        # Get all transactions related to this account
        transactions = Transaction.objects.filter(
            Q(from_account=account) | Q(to_account=account)
        ).order_by("-created_at")

        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing transactions
    """

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    @transaction.atomic
    @action(detail=False, methods=["post"])
    def deposit(self, request):
        """
        Deposit funds into an account
        """
        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            # Create a new deposit transaction
            deposit = Transaction.objects.create(
                to_account=serializer.validated_data["to_account"],
                amount=serializer.validated_data["amount"],
                transaction_type=Transaction.Type.DEPOSIT,
                status=Transaction.Status.PENDING,
            )

            try:
                # Simulate blockchain deposit processing
                # In a real implementation, this would integrate with blockchain APIs

                # Mark the transaction as completed
                deposit.complete(hash=f"simulated_hash_{deposit.id}")

                return Response(
                    TransactionSerializer(deposit).data, status=status.HTTP_201_CREATED
                )
            except Exception as e:
                # Something went wrong, rollback the transaction
                deposit.rollback()
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    @action(detail=False, methods=["post"])
    def withdraw(self, request):
        """
        Withdraw funds from an account
        """
        serializer = WithdrawSerializer(data=request.data)
        if serializer.is_valid():
            # Create a new withdrawal transaction
            withdrawal = Transaction.objects.create(
                from_account=serializer.validated_data["from_account"],
                amount=serializer.validated_data["amount"],
                transaction_type=Transaction.Type.WITHDRAWAL,
                status=Transaction.Status.PENDING,
            )

            try:
                # Simulate blockchain withdrawal processing
                # In a real implementation, this would integrate with blockchain APIs

                # Mark the transaction as completed
                withdrawal.complete(hash=f"simulated_hash_{withdrawal.id}")

                return Response(
                    TransactionSerializer(withdrawal).data,
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                # Something went wrong, rollback the transaction
                withdrawal.rollback()
                return Response(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
