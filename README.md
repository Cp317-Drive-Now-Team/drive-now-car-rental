# DriveNow Car Rental Management System

## Overview
DriveNow is a comprehensive car rental management application designed to streamline vehicle browsing, customer account registration, secure reservations, and administrative fleet control. Developed as part of CP317 Software Engineering (Group 22), this project utilizes a Python-based interface, a secure MySQL relational database backend, and strict role-based access control.

---

## Team & Roles (Group 22)
* **Aryan Kainth** – Scrum Master & Dataset Designer / Backend Integration
* **Albina Qureshi** – Backend Developer
* **Sadaf Faizi** – Frontend Developer & Product Owner
* **Dheeraj Bashal** – Product Owner & Requirements Analyst

---

## Tech Stack & Architecture
* **Database Management System:** MySQL (v8.0+) accessed via MySQL Workbench.
* **Backend & Logic:** Python (utilizing secure password hashing tools for user authentication and database connectors).
* **Security & Compliance:** 
  * Cryptographic password hashing preventing plaintext credential storage.
  * Tokenized payment records (`transaction_token`) ensuring PII and financial security compliance.
  * Strict Role-Based Access Control (`Customer` vs. `Administrator`).

---

## Database Architecture (`drivenow_db`)
The relational schema comprises core tables designed with strict referential integrity and optimized search indexes:
1. **`users`**: Stores user profiles, credentials, driver's license details, and role types.
2. **`locations`**: Manages physical branch locations for vehicle pick-up and drop-off.
3. **`cars`**: Tracks the vehicle inventory pool (make, model, year, type, daily rate, and status).
4. **`reservations`**: Handles customer bookings, date ranges, total costs, and status tracking while protecting against double-booking race conditions.
5. **`payments`**: Records payment receipts, amounts, and external gateway transaction tokens.

---

## Setup & Installation Instructions

### 1. Database Setup (MySQL Workbench)
1. Open **MySQL Workbench** and connect to your local MySQL server instance.
2. Open a new SQL query tab.
3. Import or run the self-contained `.sql` database dump file (e.g., `drivenow_db_updated_data.sql`) to automatically create the `drivenow_db` schema, tables, indexes, and initial test data (including branch locations, test admin/customer accounts with verified password hashes, and vehicle inventory).

### 2. Database Configuration (`config.py`)
To allow the application to connect to your local MySQL instance, configure your database credentials:

1. Copy the provided configuration template:
   * Copy `config.example.py` and save it as `config.py` in the root directory.
2. Update your credentials:
   * Open `config.py` and replace `"YOUR_PASSWORD"` with your actual local MySQL root password.
   * *Alternative:* If you prefer using environment variables to keep credentials secure, you can set an environment variable named `DRIVENOW_DB_PASSWORD` on your system instead of modifying the file.

### 3. Running the Application UI
1. Ensure you have **Python 3.x** installed on your system.
    1a. You must install Dependencies (Section 4)
2. Clone or download the project repository to your local machine.
3. Open your terminal or command prompt inside the project folder.
4. Launch the application script:
   ```bash
   python app_ui.py
   ```
### 4. Dependencies
To install the required Python packages for the backend database and security modules (`SQLAlchemy`, `PyMySQL`, and `Werkzeug`), run the following command:

```bash
pip install sqlalchemy pymysql werkzeug
```
