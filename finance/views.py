from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .models import Transaction, Loan
import json
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Transaction, Loan, LoanRepayment
from django.contrib.admin.views.decorators import staff_member_required # <--- Add to imports
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone 
from django.core.paginator import Paginator
from django.db.models import Sum, Q


@login_required
def dashboard(request):
    if request.user.is_staff:
        return HttpResponseRedirect(reverse("admin_dashboard")) # Protect user dashboard
    return render(request, "finance/index.html")

# Create a new index function for the Landing Page
def index(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return HttpResponseRedirect(reverse("admin_dashboard")) # Admins go here
        return HttpResponseRedirect(reverse("dashboard"))       # Users go here
    return render(request, "finance/landing.html")

@login_required
def dashboard_api(request):
    user = request.user

    # --- 1. Calculate Balances ---
    # Sum up all transaction types
    deposits = Transaction.objects.filter(user=user, transaction_type='DEPOSIT').aggregate(Sum('amount'))['amount__sum'] or 0
    withdrawals = Transaction.objects.filter(user=user, transaction_type='WITHDRAWAL').aggregate(Sum('amount'))['amount__sum'] or 0
    share_transfers = Transaction.objects.filter(user=user, transaction_type='SHARE_TRANSFER').aggregate(Sum('amount'))['amount__sum'] or 0

    # Savings (Available) = Deposits - Withdrawals - Money moved to Shares
    current_savings = deposits - withdrawals - share_transfers
    
    # Shares (Non-withdrawable) = Money moved to Shares
    share_capital = share_transfers
    
    # Dividends (Visual only: 10% of Share Capital)
    projected_dividends = float(share_capital) * 0.10

    # --- 2. Loan Calculations (Existing) ---
    active_loans = Loan.objects.filter(user=user, status='APPROVED').aggregate(Sum('balance_due'))['balance_due__sum'] or 0
    total_loans_count = Loan.objects.filter(user=user).count()
    
    # --- 3. Loan Status (Existing) ---
    latest_loan = Loan.objects.filter(user=user).order_by('-date_applied').first()
    loan_status_data = None
    if latest_loan:
        loan_status_data = {
            'status': latest_loan.status,
            'amount': float(latest_loan.principal_amount),
            'reason': latest_loan.rejection_reason if latest_loan.status == 'REJECTED' else ''
        }

    
    page_number = request.GET.get('page', 1)
    transaction_query = Transaction.objects.filter(user=user).order_by('-date').values(
        'transaction_type', 'amount', 'date', 'reference_code'
    )
    
    paginator = Paginator(transaction_query, 5) # Show 5 per page
    page_obj = paginator.get_page(page_number)

    return JsonResponse({
        'savings': float(current_savings),
        'share_capital': float(share_capital), 
        'dividends': projected_dividends,      
        'loan_balance': float(active_loans),
        'loans_count': total_loans_count,
        'recent_loan': loan_status_data,
        
        # Pagination Data
        'transactions': list(page_obj.object_list),
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'current_page': page_obj.number,
        'num_pages': paginator.num_pages
    })

@csrf_exempt  # For simplicity in this specific fetch request
@login_required
def apply_loan_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = Decimal(data.get('amount'))
            duration = int(data.get('duration'))

            # Basic Validation
            if amount <= 0 or duration <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid values'})

            # Create the Loan (Default status is PENDING)
            loan = Loan.objects.create(
                user=request.user,
                principal_amount=amount,
                duration_months=duration,
                interest_rate=Decimal(12.0) # Fixed rate for now
            )
            
            return JsonResponse({'success': True, 'message': 'Loan Application Submitted!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'POST method required'})

@login_required
def apply_loan(request):
    return render(request, "finance/loan_apply.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("dashboard"))
        else:
            return render(request, "finance/login.html", {
                "message": "Invalid username or password."
            })
    return render(request, "finance/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]

        if password != confirmation:
            return render(request, "finance/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "finance/register.html", {
                "message": "Username already taken."
            })
        
        login(request, user)
        return HttpResponseRedirect(reverse("dashboard"))
        
    return render(request, "finance/register.html")

@csrf_exempt
@login_required
def transact_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get('action')
            amount = Decimal(data.get('amount'))

            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid amount'})

            # --- Logic for Savings (Cash In) ---
            if action == 'DEPOSIT':
                Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transaction_type='DEPOSIT',
                    reference_code='MPESA-TOPUP'
                )
                return JsonResponse({'success': True, 'message': 'Top-up Successful!'})

            # --- Logic for Share Capital (Transfer) ---
            elif action == 'SHARE_TRANSFER':
                # Check balance first
                current_bal = dashboard_api(request).content # This is a hacky way to check balance, better to recalc:
                # Recalculate quick balance
                deps = Transaction.objects.filter(user=request.user, transaction_type='DEPOSIT').aggregate(Sum('amount'))['amount__sum'] or 0
                wds = Transaction.objects.filter(user=request.user, transaction_type__in=['WITHDRAWAL', 'SHARE_TRANSFER']).aggregate(Sum('amount'))['amount__sum'] or 0
                available = deps - wds
                
                if available < amount:
                    return JsonResponse({'success': False, 'error': 'Insufficient funds in Current Account'})

                Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transaction_type='SHARE_TRANSFER',
                    reference_code='TO SHARES'
                )
                return JsonResponse({'success': True, 'message': 'Shares bought successfully!'})

            # --- Logic for Repayment ---
            elif action == 'REPAY':
                active_loan = Loan.objects.filter(user=request.user, status='APPROVED').first()
                if not active_loan:
                    return JsonResponse({'success': False, 'error': 'No active loan'})
                
                # Deduct from savings
                Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transaction_type='WITHDRAWAL',
                    reference_code=f'LOAN #{active_loan.id} REPAY'
                )
                LoanRepayment.objects.create(loan=active_loan, amount=amount)
                
                return JsonResponse({'success': True, 'message': 'Repayment Successful!'})
            
            # --- Logic for Withdrawal (Cash Out) ---
            elif action == 'WITHDRAW':
                # Recalculate available balance (Current Account)
                deps = Transaction.objects.filter(user=request.user, transaction_type='DEPOSIT').aggregate(Sum('amount'))['amount__sum'] or 0
                # Sum of all money leaving the Current Account (Withdrawals + Transfers + Repayments usually come from here too, but for now we separate Repayments or include them if your logic does. 
                # Based on your dashboard_api, Repayments are tracking strictly against loan, but physically money leaves the account. 
                # For safety, let's just check against the 'Savings' balance logic:
                
                # Retrieve "Current Savings" logic locally
                wds = Transaction.objects.filter(user=request.user, transaction_type__in=['WITHDRAWAL', 'SHARE_TRANSFER']).aggregate(Sum('amount'))['amount__sum'] or 0
                
                available = deps - wds

                if available < amount:
                    return JsonResponse({'success': False, 'error': 'Insufficient funds in Current Account'})

                Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transaction_type='WITHDRAWAL',
                    reference_code='MPESA-WITHDRAW'
                )
                return JsonResponse({'success': True, 'message': 'Withdrawal Successful!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'POST required'})

@staff_member_required
def staff_dashboard(request):
    # Fetch all pending loans
    pending_loans = Loan.objects.filter(status='PENDING').order_by('-date_applied')
    return render(request, "finance/staff_dashboard.html", {
        "loans": pending_loans
    })

@staff_member_required
def approve_loan(request, loan_id):
    if request.method == "POST":
        loan = get_object_or_404(Loan, id=loan_id)
        loan.status = 'APPROVED'
        loan.date_approved = timezone.now()
        # The save() method in models.py will auto-calculate the total_due
        loan.save()
    return redirect('staff_dashboard')

@staff_member_required
def reject_loan(request, loan_id):
    if request.method == "POST":
        loan = get_object_or_404(Loan, id=loan_id)
        reason = request.POST.get('reason')
        loan.status = 'REJECTED'
        loan.rejection_reason = reason
        loan.save()
    return redirect('staff_dashboard')


# --- ADMIN VIEWS ---

@staff_member_required
def admin_dashboard(request):
    return render(request, "finance/admin_dashboard.html")

@staff_member_required
def delete_user(request, user_id):
    if request.method == "POST":
        user_to_delete = get_object_or_404(User, id=user_id)
        if not user_to_delete.is_staff: # Prevent deleting yourself/other admins
            user_to_delete.delete()
    return redirect('admin_dashboard')

@login_required
def admin_dashboard_api(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # 1. Calculate System-Wide Stats
    # Total Share Capital (The Pool) = Sum of ALL users' share transfers
    total_share_pool = Transaction.objects.filter(transaction_type='SHARE_TRANSFER').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Total Invested in Bonds (By Admin)
    # We track this using transactions made by the ADMIN user with type 'BOND_INVESTMENT'
    total_bonds = Transaction.objects.filter(transaction_type='BOND_INVESTMENT').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Available to Invest
    available_capital = total_share_pool - total_bonds

    # Projected Returns (15%)
    projected_returns = float(total_bonds) * 0.15

    # 2. Get User List with Details
    # We exclude staff members from this list
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    user_data = []

    for u in users:
        # Calculate Savings
        deps = Transaction.objects.filter(user=u, transaction_type='DEPOSIT').aggregate(Sum('amount'))['amount__sum'] or 0
        wds = Transaction.objects.filter(user=u, transaction_type__in=['WITHDRAWAL', 'SHARE_TRANSFER']).aggregate(Sum('amount'))['amount__sum'] or 0
        savings = deps - wds

        # Calculate Loans
        loan_bal = Loan.objects.filter(user=u, status='APPROVED').aggregate(Sum('balance_due'))['balance_due__sum'] or 0
        
        user_data.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'savings': float(savings),
            'loan_balance': float(loan_bal),
            'joined': u.date_joined
        })

    return JsonResponse({
        'total_users': users.count(),
        'share_pool': float(total_share_pool),
        'bonds_balance': float(total_bonds),
        'available_capital': float(available_capital),
        'returns': projected_returns,
        'users': user_data
    })

@csrf_exempt
@staff_member_required
def admin_invest_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            amount = Decimal(data.get('amount'))

            # Check if we have enough "Share Capital" pool to invest
            # (We reuse the logic from the dashboard api)
            share_pool = Transaction.objects.filter(transaction_type='SHARE_TRANSFER').aggregate(Sum('amount'))['amount__sum'] or 0
            current_bonds = Transaction.objects.filter(transaction_type='BOND_INVESTMENT').aggregate(Sum('amount'))['amount__sum'] or 0
            available = share_pool - current_bonds

            if amount > available:
                 return JsonResponse({'success': False, 'error': 'Insufficient Share Capital Pool'})

            # Create Investment Record (Linked to Admin)
            Transaction.objects.create(
                user=request.user,
                amount=amount,
                transaction_type='BOND_INVESTMENT',
                reference_code='GOVT-BOND-PURCHASE'
            )
            return JsonResponse({'success': True, 'message': 'Investment Successful!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'POST required'})