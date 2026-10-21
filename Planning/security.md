# Security and Access Control Plan

## Authentication

Users must register and log in before accessing protected functionality. The application supports two user roles:

- Buyer
- Vendor

Passwords are handled using Django's built-in authentication system, which stores passwords securely using password hashing rather than plain text.

## Authorisation

Access to functionality is controlled according to the user's role and authentication status.

### Buyers

Buyers can:

- Browse stores and products
- Add products to their cart
- Checkout
- View their orders
- Leave product reviews
- Reset forgotten passwords

### Vendors

Vendors can:

- Create and manage their own stores
- Add and manage products belonging to their stores
- View orders containing products from their stores
- Update the status of appropriate orders

A vendor must not be able to modify another vendor's stores or products.

## Protected Views and APIs

Django authentication and permissions are used to protect restricted functionality.

Unauthenticated users should be prevented from accessing protected views.

The REST API uses authentication and permissions for protected endpoints. Token authentication is used for API requests that require authentication.

## Data Protection

Sensitive information such as passwords should never be stored in plain text.

Environment variables are used for sensitive configuration such as secret keys and email credentials.

Database access is controlled through Django's ORM.

## Input Validation

Forms and serializers validate user input before data is saved.

The application should reject invalid data, invalid quantities, unavailable products, and unauthorised actions.

## Session Security

Django sessions are used to maintain user state and the shopping cart while users browse the application.

## Password Recovery

Forgotten-password functionality uses time-limited password reset tokens. This prevents old reset links from remaining valid indefinitely.

## Ownership Checks

Vendor actions perform ownership checks to ensure that a vendor can only manage stores and products belonging to that vendor.

## API Security

Protected API endpoints require authentication. Requests without valid authentication credentials should be rejected.

Role-specific API endpoints verify that the authenticated user has the required role before allowing the operation.
