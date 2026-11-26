
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction as db_transaction
from decimal import Decimal
from django.utils import timezone

from .models import (
    Customer,
    Account,
    Transaction,
    Loan,
    Beneficiary
)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(request, 'bank/login.html')


@login_required
def dashboard(request):
    customer = Customer.objects.get(
        email=request.user.email
    )

    accounts = Account.objects.filter(
        customer=customer
    )

    transactions = Transaction.objects.filter(
        account__in=accounts
    ).order_by('-transaction_date')[:10]

    total_balance = sum(
        account.balance or 0
        for account in accounts
    )

    all_transactions = Transaction.objects.filter(
        account__in=accounts
    )

    deposit_total = sum(
        transaction.amount
        for transaction in all_transactions
        if transaction.transaction_type == 'Deposit'
    )

    withdrawal_total = sum(
        transaction.amount
        for transaction in all_transactions
        if transaction.transaction_type == 'Withdrawal'
    )

    transfer_total = sum(
        transaction.amount
        for transaction in all_transactions
        if transaction.transaction_type == 'Transfer'
    )

    context = {
        'customer': customer,
        'accounts': accounts,
        'transactions': transactions,
        'total_balance': total_balance,
        'deposit_total': deposit_total,
        'withdrawal_total': withdrawal_total,
        'transfer_total': transfer_total,
    }

    return render(
        request,
        'bank/dashboard.html',
        context
    )


@login_required
def withdraw(request):
    customer = Customer.objects.get(
        email=request.user.email
    )

    accounts = Account.objects.filter(
        customer=customer
    )

    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        amount = request.POST.get('amount')

        try:
            amount = Decimal(amount)

            if amount <= 0:
                messages.error(
                    request,
                    'Amount must be greater than zero.'
                )

                return render(
                    request,
                    'bank/withdraw.html',
                    {'accounts': accounts}
                )

            # Start database transaction
            with db_transaction.atomic():

                # Lock account before checking/updating balance
                account = Account.objects.select_for_update().get(
                    account_id=account_id,
                    customer=customer
                )

                # Check sufficient balance
                if account.balance < amount:
                    messages.error(
                        request,
                        'Insufficient balance.'
                    )

                    return render(
                        request,
                        'bank/withdraw.html',
                        {'accounts': accounts}
                    )

                # Deduct money
                account.balance -= amount

                account.save(
                    update_fields=['balance']
                )

                # Record transaction
                Transaction.objects.create(
                    account=account,
                    transaction_type='Withdrawal',
                    amount=amount,
                    description='Cash withdrawal',
                    status='Success',
                    transaction_date=timezone.now()
                )

            messages.success(
                request,
                f'₹{amount} withdrawn successfully.'
            )

            return redirect('dashboard')

        except (
            ValueError,
            TypeError,
            Account.DoesNotExist
        ):
            messages.error(
                request,
                'Invalid withdrawal request.'
            )

    return render(
        request,
        'bank/withdraw.html',
        {'accounts': accounts}
    )


@login_required
def deposit(request):
    customer = Customer.objects.get(
        email=request.user.email
    )

    accounts = Account.objects.filter(
        customer=customer
    )

    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        amount = request.POST.get('amount')

        try:
            amount = Decimal(amount)

            if amount <= 0:
                messages.error(
                    request,
                    'Amount must be greater than zero.'
                )

                return render(
                    request,
                    'bank/deposit.html',
                    {'accounts': accounts}
                )

            account = Account.objects.get(
                account_id=account_id,
                customer=customer
            )

            with db_transaction.atomic():

                account.balance += amount

                account.save(
                    update_fields=['balance']
                )

                Transaction.objects.create(
                    account=account,
                    transaction_type='Deposit',
                    amount=amount,
                    description='Cash deposit',
                    status='Success',
                    transaction_date=timezone.now()
                )

            messages.success(
                request,
                f'₹{amount} deposited successfully.'
            )

            return redirect('dashboard')

        except (
            ValueError,
            TypeError,
            Account.DoesNotExist
        ):
            messages.error(
                request,
                'Invalid deposit request.'
            )

    return render(
        request,
        'bank/deposit.html',
        {'accounts': accounts}
    )


@login_required
def transfer(request):
    customer = Customer.objects.get(
        email=request.user.email
    )

    accounts = Account.objects.filter(
        customer=customer
    )

    if request.method == 'POST':
        sender_account_id = request.POST.get(
            'sender_account_id'
        )

        receiver_account_number = request.POST.get(
            'receiver_account_number'
        )

        amount = request.POST.get('amount')

        try:
            amount = Decimal(amount)

            if amount <= 0:
                messages.error(
                    request,
                    'Amount must be greater than zero.'
                )

                return render(
                    request,
                    'bank/transfer.html',
                    {'accounts': accounts}
                )

            # Start database transaction
            with db_transaction.atomic():

                # Lock sender account
                sender = Account.objects.select_for_update().get(
                    account_id=sender_account_id,
                    customer=customer
                )

                # Lock receiver account
                receiver = Account.objects.select_for_update().get(
                    account_number=receiver_account_number
                )

                # Check receiver status
                if receiver.status != 'Active':
                    messages.error(
                        request,
                        'Receiver account is not active.'
                    )

                    return render(
                        request,
                        'bank/transfer.html',
                        {'accounts': accounts}
                    )

                # Prevent same-account transfer
                if sender.account_id == receiver.account_id:
                    messages.error(
                        request,
                        'You cannot transfer money to the same account.'
                    )

                    return render(
                        request,
                        'bank/transfer.html',
                        {'accounts': accounts}
                    )

                # Check balance
                if sender.balance < amount:
                    messages.error(
                        request,
                        'Insufficient balance.'
                    )

                    return render(
                        request,
                        'bank/transfer.html',
                        {'accounts': accounts}
                    )

                # Deduct from sender
                sender.balance -= amount

                sender.save(
                    update_fields=['balance']
                )

                # Add to receiver
                receiver.balance += amount

                receiver.save(
                    update_fields=['balance']
                )

                # Create sender transaction
                Transaction.objects.create(
                    account=sender,
                    transaction_type='Transfer',
                    amount=amount,
                    related_account=receiver,
                    description=(
                        f'Transfer to account '
                        f'{receiver.account_number}'
                    ),
                    status='Success',
                    transaction_date=timezone.now()
                )

                # Create receiver transaction
                Transaction.objects.create(
                    account=receiver,
                    transaction_type='Transfer',
                    amount=amount,
                    related_account=sender,
                    description=(
                        f'Transfer from account '
                        f'{sender.account_number}'
                    ),
                    status='Success',
                    transaction_date=timezone.now()
                )

            messages.success(
                request,
                f'₹{amount} transferred successfully.'
            )

            return redirect('dashboard')

        except (
            ValueError,
            TypeError,
            Account.DoesNotExist
        ):
            messages.error(
                request,
                'Invalid transfer request.'
            )

    return render(
        request,
        'bank/transfer.html',
        {'accounts': accounts}
    )


@login_required
def transactions(request):
    customer = Customer.objects.get(
        email=request.user.email
    )

    accounts = Account.objects.filter(
        customer=customer
    )

    transaction_list = Transaction.objects.filter(
        account__in=accounts
    ).order_by('-transaction_date')

    context = {
        'customer': customer,
        'transactions': transaction_list,
    }

    return render(
        request,
        'bank/transactions.html',
        context
    )


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def loans(request):
    customer = Customer.objects.get(
        email=request.user.email
    )

    if request.method == 'POST':
        loan_type = request.POST.get('loan_type')
        amount = request.POST.get('amount')
        interest_rate = request.POST.get('interest_rate')
        duration_months = request.POST.get(
            'duration_months'
        )

        Loan.objects.create(
            customer=customer,
            loan_type=loan_type,
            amount=amount,
            interest_rate=interest_rate,
            duration_months=duration_months,
            status='Pending',
            created_at=timezone.now()
        )

        messages.success(
            request,
            'Loan application submitted successfully.'
        )

        return redirect('loans')

    customer_loans = Loan.objects.filter(
        customer=customer
    ).order_by('-loan_id')

    return render(
        request,
        'bank/loans.html',
        {
            'loans': customer_loans
        }
    )


@login_required
def beneficiaries(request):
    customer = Customer.objects.get(
        email=request.user.email
    )

    if request.method == 'POST':
        beneficiary_name = request.POST.get(
            'beneficiary_name'
        )

        account_number = request.POST.get(
            'account_number'
        )

        bank_name = request.POST.get(
            'bank_name'
        )

        ifsc_code = request.POST.get(
            'ifsc_code'
        )

        Beneficiary.objects.create(
            customer=customer,
            beneficiary_name=beneficiary_name,
            account_number=account_number,
            bank_name=bank_name,
            ifsc_code=ifsc_code
        )

        messages.success(
            request,
            'Beneficiary added successfully.'
        )

        return redirect('beneficiaries')

    customer_beneficiaries = Beneficiary.objects.filter(
        customer=customer
    ).order_by('-beneficiary_id')

    return render(
        request,
        'bank/beneficiaries.html',
        {
            'beneficiaries': customer_beneficiaries
        }
    )

