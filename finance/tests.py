from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Transaction, Loan, LoanRepayment
from decimal import Decimal
import json

class ModelTests(TestCase):
    def setUp(self):
        """Create a test user for model operations."""
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_loan_interest_calculation(self):
        """Test that interest is automatically calculated when a loan is saved."""
        # Principal: 10,000, Rate: 12%, Duration: 12 months
        # Interest = 10,000 * 0.12 * 1 = 1,200
        # Total Due should be 11,200
        loan = Loan.objects.create(
            user=self.user,
            principal_amount=Decimal(10000),
            interest_rate=Decimal(12),
            duration_months=12
        )
        self.assertEqual(loan.total_due, Decimal(11200))
        self.assertEqual(loan.balance_due, Decimal(11200))
        self.assertEqual(loan.status, 'PENDING')

    def test_loan_repayment_logic(self):
        """Test that repaying a loan reduces balance and updates status to PAID."""
        loan = Loan.objects.create(
            user=self.user,
            principal_amount=Decimal(10000),
            status='APPROVED'
        )
        
        # Partial Repayment (5,000)
        LoanRepayment.objects.create(loan=loan, amount=Decimal(5000))
        loan.refresh_from_db()
        self.assertEqual(loan.balance_due, Decimal(6200)) # 11200 - 5000
        self.assertEqual(loan.status, 'APPROVED')

        # Full Repayment of remainder (6,200)
        LoanRepayment.objects.create(loan=loan, amount=Decimal(6200))
        loan.refresh_from_db()
        self.assertEqual(loan.balance_due, Decimal(0))
        self.assertEqual(loan.status, 'PAID')

class ViewTests(TestCase):
    def setUp(self):
        """Set up client and user for view tests."""
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

    def test_dashboard_api_initial_state(self):
        """Ensure dashboard returns correct initial zero values."""
        response = self.client.get(reverse('dashboard_api'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertEqual(data['savings'], 0.0)
        self.assertEqual(data['loan_balance'], 0.0)
        self.assertEqual(data['loans_count'], 0)

    def test_deposit_transaction(self):
        """Test the deposit API endpoint."""
        url = reverse('transact_api')
        data = {'action': 'DEPOSIT', 'amount': '1000'}
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check if Transaction was created in DB
        self.assertTrue(Transaction.objects.filter(user=self.user, amount=1000, transaction_type='DEPOSIT').exists())
        
        # Check if Dashboard reflects the change
        dash_response = self.client.get(reverse('dashboard_api'))
        dash_data = json.loads(dash_response.content)
        self.assertEqual(dash_data['savings'], 1000.0)

    def test_withdraw_insufficient_funds(self):
        """Test that user cannot withdraw more than they have."""
        url = reverse('transact_api')
        data = {'action': 'WITHDRAW', 'amount': '500'} # User has 0 balance
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        res_data = json.loads(response.content)
        
        self.assertFalse(res_data['success'])
        self.assertEqual(res_data['error'], 'Insufficient funds in Current Account')

    def test_apply_loan_success(self):
        """Test applying for a loan via API."""
        url = reverse('apply_loan_api')
        data = {'amount': '5000', 'duration': '6'}
        
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Check DB
        self.assertTrue(Loan.objects.filter(user=self.user, principal_amount=5000).exists())

    def test_prevent_duplicate_loans(self):
        """Test that a user cannot apply for a second loan while one is active."""
        # Create an existing active loan
        Loan.objects.create(user=self.user, principal_amount=5000, status='APPROVED')
        
        # Try to apply for another
        url = reverse('apply_loan_api')
        data = {'amount': '2000', 'duration': '6'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        
        res_data = json.loads(response.content)
        self.assertFalse(res_data['success'])
        self.assertIn('already have an active loan', res_data['error'])