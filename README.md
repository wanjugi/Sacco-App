# ZEED Sacco - Sacco Management System

## Distinctiveness and Complexity

ZEED Sacco is a financial technology web application designed to simulate the operations of a Kenyan Savings and Credit Cooperative Organization (SACCO). This project satisfies the distinctiveness and complexity requirements in the following ways:

### Distinctiveness
This project is distinct from the standard social network or e-commerce course projects because it models **institutional financial logic** rather than social interactions or product inventories.

* **VS Social Network:** There are no "follows," "likes," or user-to-user messaging. The primary relationship is User-to-Ledger. The system focuses on asset liability management (ALM) where user deposits become the organization's capital for loans and investments.
* **VS E-Commerce:** There is no shopping cart or product catalog. Instead, the application implements a **Dual-Account System** unique to Saccos:
    * **FOSA (Front Office Service Activity):** A liquid "Current Account" for daily withdrawals and deposits.
    * **BOSA (Back Office Service Activity):** Non-withdrawable "Share Capital" that earns dividends but cannot be accessed as cash.

### Complexity
The application moves beyond standard CRUD operations by implementing complex financial algorithms and a reactive frontend.

1.  **Advanced Financial Logic (Backend):**
    * **Waterfall Repayment Algorithm:** When a user makes a loan repayment, the system uses a custom algorithm to distribute funds across multiple active loans, prioritizing the oldest debts first until the payment amount is exhausted.
    * **Automated Interest Calculation:** The `Loan` model overrides the `save()` method to automatically calculate simple interest based on principal, rate, and duration, converting inputs to `Decimal` types to prevent floating-point precision errors.
    * **Polymorphic Transaction Handling:** A single `Transaction` model handles four distinct financial events (Deposits, Withdrawals, Share Transfers, Bond Investments), using aggregation queries to calculate live balances on the fly.

2.  **Reactive Frontend (Vue.js Integration):**
    * The application uses **Vue.js 3** (via CDN) to create a Single Page Application (SPA) feel within a Django template structure.
    * **Real-time Formatting:** It utilizes the `Intl.NumberFormat` API to standardize currency display (KES) across the entire platform dynamically.
    * **Asynchronous Data:** Dashboards fetch data via internal APIs, allowing for pagination of transaction history without page reloads.

3.  **Role-Based Access Control (RBAC):**
    * The system features **Three Distinct Portals** based on user status:
        * **Public Landing Page:** For unauthenticated users.
        * **User Dashboard:** For standard members to transact and apply for loans.
        * **Staff/Admin Portal:** A restricted interface for officers to approve loans, view total system assets, and simulate investing user capital into Government Bonds.

## What’s Contained in Each File

### Main Application Directory (`finance/`)

* **`models.py`**: Defines the database schema.
    * `Transaction`: Tracks all money movement.
    * `Loan`: Manages loan status (Pending/Approved/Paid) and interest math.
    * `LoanRepayment`: Records individual payments against loans.
* **`views.py`**: The core controller.
    * Contains API endpoints (`dashboard_api`, `transact_api`) that return JSON for Vue.js.
    * Contains the "Waterfall" logic for distributing loan repayments.
    * Contains decorators (`@staff_member_required`) to secure admin routes.
* **`urls.py`**: Handles routing, separating standard views from API endpoints (`/api/...`).
* **`tests.py`**: A comprehensive test suite containing 7 unit tests. It verifies model integrity (interest calculation, repayment status updates) and API security (preventing withdrawals exceeding balance).
* **`admin.py`**: Configuration for the default Django admin interface.

### Templates (`finance/templates/finance/`)

* **`layouts.html`**: The base template. Includes Tailwind CSS, Vue.js CDN, and a dynamic Navbar that changes links based on User/Staff status.
* **`landing.html`**: The marketing homepage with responsive hero and feature sections.
* **`index.html`**: The main User Dashboard. Contains the Vue.js instance for the user client.
* **`admin_dashboard.html`**: The Super-Admin interface. Features a dark-themed header and logic to invest "Share Pool" funds into bonds.
* **`staff_dashboard.html`**: The operational dashboard for approving/rejecting loans.
* **`loan_apply.html`**: Loan application form.
* **`login.html` / `register.html`**: Authentication pages with CSRF protection and "Back to Home" navigation.

## How to Run the Application

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Database Setup:**
    ```bash
    python manage.py makemigrations finance
    python manage.py migrate
    ```

3.  **Create Admin User:**
    You need a superuser to access the Staff/Admin portals.
    ```bash
    python manage.py createsuperuser
    ```

4.  **Run Tests (Optional but Recommended):**
    Verify the financial logic is working correctly.
    ```bash
    python manage.py test finance
    ```

5.  **Start Server:**
    ```bash
    python manage.py runserver
    ```

## Mobile Responsiveness
The application is fully mobile-responsive. It utilizes Tailwind CSS's grid system (`grid-cols-1 md:grid-cols-4`) and utility classes to ensure that dashboards, tables, and modals resize gracefully from desktop monitors down to mobile screens.