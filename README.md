# Dove TV - IT Operations & Approval Portal

An internal, centralized management system built for the Dove TV Engineering and IT departments. This portal streamlines day-to-day station operations by replacing scattered paperwork with a unified, role-based digital approval workflow.

## 🚀 Key Features

*   **Role-Based Access Control (RBAC):** Granular permission structuring across `STAFF`, `HOU` (Head of Unit), `MANAGER`, and `EXECUTIVE` roles paired with department-level grouping.
*   **Approval Delegation ("Switch of Power"):** Intelligent routing that automatically shifts approval authority to secondary managers if the primary Admins toggle their "Out of Office" status.
*   **Studio Bookings & Clash Detection:** Allows staff to securely request studio time. Automatically detects schedule overlaps and prevents double-booking. Includes printable, hierarchically formatted Stage 1 / Final Approval physical Memos.
*   **Gear Vault (Inventory Hub):** Real-time tracking of broadcast equipment (Cameras, Monitors, Streamboxes). Staff can checkout equipment while managers digitally track return dates and stock depletion.
*   **Marketing Job Orders:** Streamlined pipeline for requesting and assigning marketing personnel.
*   **Fault Reporting Hub:** A lightweight ticketing system to report, assign, and track technical faults across various broadcast locations (e.g., Studio B, Main Auditorium).
*   **Engineering Duty Roster:** An interactive monthly view mapping out Audio Engineers, Streaming Technicians, broadcast IT, and generic duty assignments.
*   **Midnight Glassmorphism UI:** A highly polished, custom-built, responsive CSS interface emphasizing contrast, dark/light modes, and modern translucent overlays.

---

## 🛠️ Technology Stack

*   **Backend framework:** Django (Python 3.x)
*   **Database:** SQLite (Default for rapid deployment)
*   **Frontend Design:** HTML5, Custom "Midnight" CSS, FontAwesome 6 icons
*   **Server Logic:** Django Template Engine (DTE)

---

## ⚙️ Local Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/dove-tv-approval-portal.git
cd dove-tv-approval-portal
```

### 2. Create the Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
Make sure Django is installed (add `requirements.txt` if you have one later):
```bash
pip install django
```

### 4. Database Migrations
Initialize the schema and structure:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create the Superuser (Admin)
You need at least one Admin account to assign roles to everyone else.
```bash
python manage.py createsuperuser
```

### 6. Run the Server
```bash
python manage.py runserver
```

Navigate to `http://127.0.0.1:8000` in your web browser. 

---

## 🛡️ User Roles & Profile Configuration
Once logged in as an Admin, navigate to **Settings** on the left panel. From there, you can view all registered staff and manually assign them to:
1. **Access Role**: `ADMIN`, `STAFF`, `USER`
2. **Designation**: `HOU`, `MANAGER`, etc.
3. **Department**: `EDITING_SUITE`, `MCR_LIBRARIAN`, etc.

Only profiles flagged with Administrator capabilities or explicit HOU clearance will see the **Manager Action Queue** on their dashboard and process incoming requests.
