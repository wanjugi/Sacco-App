from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    # NEW: The Dashboard has its own home
    path("dashboard/", views.dashboard, name="dashboard"),
    
    # API Routes
    path("api/dashboard-data/", views.dashboard_api, name="dashboard_api"),
    path("api/apply-loan/", views.apply_loan_api, name="apply_loan_api"),
    path("loans/apply/", views.apply_loan, name="loan_apply"),
    path("api/transact/", views.transact_api, name="transact_api"),

    # Staff Routes
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/approve/<int:loan_id>/", views.approve_loan, name="approve_loan"),
    path("staff/reject/<int:loan_id>/", views.reject_loan, name="reject_loan"),

    # NEW ADMIN ROUTES
    path("admin-portal/", views.admin_dashboard, name="admin_dashboard"), # Admin Home
    path("api/admin-data/", views.admin_dashboard_api, name="admin_dashboard_api"), # Admin Data
    path("api/admin-invest/", views.admin_invest_api, name="admin_invest_api"), # Buy Bonds
    path("staff/delete-user/<int:user_id>/", views.delete_user, name="delete_user"), # Delete User
]