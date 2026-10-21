# Database Design Plan

The eCommerce application uses a relational database.

## Main Entities

### User

Stores authentication information for registered users.

Important information includes:

- Username
- Email
- Password
- Account information

### Profile

Stores additional information about a user, including their role.

Roles include:

- Buyer
- Vendor

### Store

Represents a store owned by a vendor.

A store is associated with one vendor, while a vendor can own one or more stores.

### Product

Represents an item sold through a store.

Each product belongs to a store and contains information such as:

- Name
- Description
- Price
- Stock
- Image

### Order

Represents a buyer's purchase.

An order belongs to a buyer and contains information such as:

- Order date
- Total
- Status

### OrderItem

Connects products to orders and records:

- Product
- Quantity
- Price at the time of purchase

Using a separate OrderItem entity allows one order to contain multiple products.

### Review

Stores customer reviews for products.

A review is associated with:

- Buyer
- Product
- Rating
- Review text
- Verification status

The verification status indicates whether the buyer has previously purchased the product.

## Relationships

- One User can have one Profile.
- One Vendor can own multiple Stores.
- One Store can contain multiple Products.
- One Buyer can create multiple Orders.
- One Order can contain multiple OrderItems.
- One Product can appear in multiple OrderItems.
- One Buyer can create reviews for Products.
- One Product can have multiple Reviews.

## Data Integrity

Foreign-key relationships should be used to maintain relationships between related records.

Database transactions should be used for important operations such as creating orders and updating stock so that related changes are completed together.

## Migrations

Django migrations are used to create and update the database schema when models change.

The database should be backed up regularly to support recovery from serious failures.

