# SAMKY TECH SHOP

SAMKY TECH SHOP is a Django-based eCommerce application for browsing technology products, managing a shopping cart, placing orders, and managing products through Django Admin.

## Features

* User registration and login
* User logout
* Product catalogue
* Product search
* Product sorting
* Product detail pages
* Product images
* Shopping cart
* Checkout
* Order management
* Buyer dashboard
* Customer reviews
* Product stock management
* Django Admin
* REST API
* API documentation with Swagger
* MariaDB database

## Technologies

* Python
* Django
* MariaDB
* MySQLclient
* Pillow
* Django REST Framework
* drf-spectacular
* python-dotenv

## Project Setup

### 1. Create and activate the virtual environment

Windows PowerShell:

python -m venv venv
.\venv\Scripts\Activate.ps1

### 2. Install dependencies

pip install -r requirements.txt

### 3. Configure environment variables

Create a .env file in the project root.

The file should contain:

DJANGO_SECRET_KEY=your-secret-key
DB_NAME=ecommerce_db
DB_USER=root
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=3306

Do not commit the .env file to source control.

### 4. Apply migrations

python manage.py makemigrations
python manage.py migrate

### 5. Start the development server

python manage.py runserver

The application will be available at:

http://127.0.0.1:8000/

## Main Pages

* Home: /
* Products: /products/
* Cart: /cart/
* Orders: /orders/
* Buyer Dashboard: /buyer/
* Vendor Dashboard: /vendor/
* Admin: /admin/
* API Documentation: /api/docs/
* API Schema: /api/schema/

## Media Files

Uploaded product images are stored in the media/products/ directory during development.

## Database

The project uses MariaDB through Django's MySQL database backend.

Database credentials are loaded from environment variables defined in .env.

## API

The project provides REST API endpoints for authentication, stores, products, orders, vendor order management, reviews, and Reddit data.

Interactive API documentation is available at:

/api/docs/

The OpenAPI schema is available at:

/api/schema/

## Development Note

The Django development server is intended for development and testing. Production deployment requires appropriate security settings, a production web server, HTTPS, secure secret management, and production database configuration.
