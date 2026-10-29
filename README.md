# DriveNow Car Rental Management System

## Overview
DriveNow is a comprehensive car rental management application designed to streamline vehicle browsing, customer account registration, secure reservations, and administrative fleet control. Developed as part of CP317 Software Engineering, this project utilizes a Python-based user interface, a secure MySQL relational database backend, and role-based access control.

---

## Team & Roles (Group 22)
* **Aryan Kainth** – Scrum Master & Dataset Designer / Backend Integration
* **Albina Qureshi** – Backend Developer
* **Sadaf Faizi** – Frontend Developer & Product Backlog
* **Dheeraj Bashal** – Product Owner & Requirements Analyst

---

## Tech Stack & Architecture
* **Database Management System:** MySQL (v8.0+) accessed via MySQL Workbench.
* **Backend & Logic:** Python (utilizing built-in `tkinter` for UI prototyping and secure hashing tools for user authentication).
* **Security & Compliance:** 
  * Cryptographic password hashing (preventing plaintext storage).
  * Tokenized payment records (`transaction_token`) to ensure PII and financial data security compliance.
  * Strict Role-Based Access Control (`Customer` vs. `Administrator`).

---

## Database Architecture (`drivenow_db`)
The relational schema comprises five core tables designed with strict referential integrity (`ON DELETE RESTRICT` / `ON DELETE CASCADE`) and optimized search indexes (`idx_car_search`, `idx_reservation_dates`):
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
3. Import or run your self-contained `.sql` database dump file (e.g., `drivenow_seed_data.sql`) to automatically create the `drivenow_db` schema, tables, indexes, and initial test data (including branch locations, test admin/customer accounts, and the vehicle inventory).

### 2. Running the Python Application UI
1. Ensure you have **Python 3.x** installed on your system.
2. Clone or download the project repository to your local machine.
3. Open your terminal or command prompt inside the project folder.
4. Launch the application UI script:
   ```bash
   python app_ui.py
