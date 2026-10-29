# SAMKY TECH SHOP

SAMKY TECH SHOP is a Django-based eCommerce application for browsing technology products, managing a shopping cart, placing orders, and managing products through Django Admin.

## Features

- User registration, login, and logout
- Product catalogue, search, sorting, and product details
- Product images
- Shopping cart and checkout
- Order management and buyer dashboard
- Customer reviews and product stock management
- Django Admin
- REST API and Swagger API documentation

## Technologies

- Python
- Django
- MariaDB
- MySQLclient
- Pillow
- Django REST Framework
- drf-spectacular
- python-dotenv

## Prerequisites

Install Python, MariaDB Server, and Git before setting up the project.

## Project Setup

### 1. Clone or download the project

Open a terminal in the project directory.

### 2. Create and activate a virtual environment

Windows PowerShell:

python -m venv venv
.\venv\Scripts\Activate.ps1

### 3. Install dependencies

python -m pip install -r requirements.txt

### 4. Create the MariaDB database

Log in to MariaDB using an account with permission to create databases:

CREATE DATABASE ecommerce_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

The application requires a dedicated MariaDB account with privileges on `ecommerce_db`. If that account does not already exist, create one and grant it access using a locally chosen password:

CREATE USER 'ecommerce_app'@'localhost'
    IDENTIFIED BY 'choose-a-password-for-this-installation';

GRANT ALL PRIVILEGES ON ecommerce_db.*
    TO 'ecommerce_app'@'localhost';

If the account already exists, do not run `CREATE USER` again; use the existing account and its configured credentials.

### 5. Configure environment variables

Create a `.env` file in the project root, alongside `manage.py`.

Add the following settings, supplying your own Django secret key and the existing database account's password:

DJANGO_SECRET_KEY=your-django-secret-key
DB_NAME=ecommerce_db
DB_USER=ecommerce_app
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=3306

Do not commit `.env` to GitHub or share it publicly.

### 6. Recreate the database tables

Run Django migrations to create the tables in MariaDB:

python manage.py migrate

Migrations create the database schema. They do not automatically restore existing products, customer accounts, orders, or other data from a previous database.

### 7. Check the project

python manage.py check

### 8. Start the development server

python manage.py runserver

Open the application at:

http://127.0.0.1:8000/

## Main Pages

- Home: `/`
- Products: `/products/`
- Cart: `/cart/`
- Orders: `/orders/`
- Buyer Dashboard: `/buyer/`
- Vendor Dashboard: `/vendor/`
- Admin: `/admin/`
- API Documentation: `/api/docs/`
- API Schema: `/api/schema/`

## Database

The application uses MariaDB through Django's MySQL database backend. Database connection settings are read from environment variables in `.env`.

The SQLite database file is not required for the submitted project. To recreate the database structure, create the MariaDB database and run `python manage.py migrate`.

## Media Files

Uploaded product images are stored in the `media/` directory during development. Include any required sample assets in the submission, but do not include private uploads or sensitive user data.

## API

The project provides REST API endpoints for application functionality. Interactive API documentation is available at `/api/docs/`, and the OpenAPI schema is available at `/api/schema/`.

## Running Checks and Migrations

python manage.py check
python manage.py migrate
python manage.py runserver

## Project Structure

- `project/` — Django settings and URL configuration
- `shop/` — Application models, views, serializers, and migrations
- `static/` — Static assets
- `media/` — Uploaded media files
- `api_examples/` — Sample API requests and responses
- `manage.py` — Django management utility
- `requirements.txt` — Python dependencies
- `.env` — Local environment variables; do not commit this file

## Security

- Never commit `.env`, passwords, private database files, or sensitive backups.
- Use a dedicated database account instead of the MariaDB administrator account.
- Use secure settings, HTTPS, and a production-ready server when deploying.
- The Django development server is intended for local development and testing only.
