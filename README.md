# ZED Capital - Sacco Management System

## Distinctiveness and Complexity

ZED Capital is a comprehensive financial technology application designed to digitize the operations of a Kenyan Savings and Credit Cooperative Organization (SACCO). Unlike standard web applications that focus on content management or social interaction, this project is built around **institutional financial logic** and **Asset Liability Management (ALM)**. The distinctiveness of this project lies in its implementation of a "Dual-Account System" (FOSA and BOSA), which is a specific banking structure requiring separate ledgers for liquid cash (Savings) and non-withdrawable equity (Share Capital). This structure forces the application to handle transactions not just as simple updates, but as immutable ledger entries that must be aggregated dynamically to calculate user balances.

The complexity of the application is demonstrated through its sophisticated backend algorithms and reactive frontend architecture. On the backend, I implemented a **"Waterfall Repayment Algorithm"** for loan management. When a user makes a generic repayment, the system does not simply deduct a balance; it fetches all active loans, orders them by approval date, and distributes the payment sequentially—paying off the oldest debts first before carrying the remainder to newer loans. Additionally, the system overrides standard Django model methods to automate financial calculations, such as computing simple interest using `Decimal` precision to prevent floating-point errors before writing to the database.

Furthermore, the project creates a hybrid architecture by integrating **Vue.js** directly into Django templates. Instead of relying on Django's server-side template rendering for all views, the dashboards utilize asynchronous API calls to fetch JSON data. This allows for real-time currency formatting (converting raw numbers to KES currency client-side) and seamless pagination of transaction histories without page reloads. The application also enforces strict Role-Based Access Control (RBAC), distinguishing between standard members who transact and staff/admins who have a completely separate portal for simulating institutional investments into Government Bonds.

## What’s Contained in Each File

### Main Application Directory (`finance/`)

* **`models.py`**: This file defines the core database schema.
    * `Transaction`: A polymorphic model that tracks four distinct financial event types (Deposits, Withdrawals, Share Transfers, and Bond Investments). It links users to their financial history.
    * `Loan`: Manages the lifecycle of a loan application. It includes a custom `save()` method that automatically calculates the total amount due based on principal, interest rate, and duration whenever a loan is created.
    * `LoanRepayment`: Acts as a sub-ledger for loans, tracking every individual installment paid against a specific loan ID to ensure auditability.

* **`views.py`**: This file contains the application controller logic and API endpoints.
    * `dashboard_api` & `transact_api`: These are JSON endpoints that power the Vue.js frontend, handling data aggregation (using Django's `Sum` and `Filter`) to calculate live balances for Savings, Shares, and Loans on the fly.
    * `transact_api`: specifically contains the **Waterfall Algorithm**, iterating through active loans to allocate repayment funds correctly.
    * `admin_dashboard_api`: Aggregates the entire platform's capital to show the super-admin the total "Share Pool" available for investment.
    * Standard views like `login`, `register`, and `index` handle authentication and page routing.

* **`urls.py`**: Defines the URL routing for the application. It explicitly separates standard template routes (e.g., `/dashboard`) from API data routes (e.g., `/api/dashboard-data/`) to maintain a clean architecture.

* **`tests.py`**: Contains a suite of unit tests to verify the integrity of the financial logic.
    * `ModelTests`: Verifies that interest calculations in `models.py` are accurate and that loan statuses update to 'PAID' automatically when the balance hits zero.
    * `ViewTests`: Tests the API endpoints to ensure users cannot withdraw more money than they have (preventing overdrafts) and cannot take multiple loans simultaneously.

* **`admin.py`**: Registers the models with the built-in Django admin panel, primarily used for debugging and superuser oversight during development.

### Templates (`finance/templates/finance/`)

* **`layouts.html`**: The base template that loads the Tailwind CSS and Vue.js libraries via CDN. It includes a dynamic Navigation Bar that conditionally renders links (e.g., hiding "Apply for Loan" for staff members) based on the authenticated user's role.

* **`index.html` (User Dashboard)**: A hybrid template that mounts a Vue.js application. It contains the JavaScript logic to:
    * Fetch user financial data asynchronously.
    * Handle the logic for four different transaction modals (Deposit, Withdraw, Pay Loan, Buy Shares).
    * Implement client-side pagination for the transaction table.

* **`admin_dashboard.html` (Admin Portal)**: A specialized interface for superusers. It includes a Vue.js instance that fetches system-wide aggregates. It allows the admin to visualize the "Share Capital Pool" and simulate investing that pool into Government Bonds to generate returns for the Sacco.

* **`staff_dashboard.html`**: An operational dashboard for loan officers. It renders a table of pending loan applications and provides server-side actions to Approve or Reject loans. It includes JavaScript to handle the "Reason for Rejection" modal.

* **`landing.html`**: The public-facing marketing page. It features a responsive Hero section and an FAQ accordion to explain the Sacco's services to unregistered visitors.

* **`loan_apply.html`**: A functional form for users to request new loans. It includes front-end validation to ensure loan amounts and durations are positive numbers.

* **`login.html`** & **`register.html`**: Standard authentication templates styled with Tailwind CSS, including error message handling and "Back to Home" navigation for better user experience.

## How to Run the Application

1.  **Install Dependencies:**
    Navigate to the project directory and install the required packages.
    ```bash
    pip install -r requirements.txt
    ```

2.  **Apply Database Migrations:**
    Initialize the SQLite database schema.
    ```bash
    python manage.py makemigrations finance
    python manage.py migrate
    ```

3.  **Create a Superuser (Admin):**
    A superuser account is required to access the Staff and Admin portals.
    ```bash
    python manage.py createsuperuser
    ```

4.  **Run the Server:**
    Start the development server.
    ```bash
    python manage.py runserver
    ```

5.  **Access the Application:**
    * **User Portal:** Visit `http://127.0.0.1:8000/` to register and transact as a standard member.
    * **Admin Portal:** Login with your superuser credentials to be automatically redirected to the Admin Dashboard for capital management.