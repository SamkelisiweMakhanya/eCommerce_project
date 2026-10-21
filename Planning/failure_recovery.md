# Failure Handling and Recovery Plan

The application should handle unexpected behaviour without exposing sensitive information or corrupting database data.

## Invalid Login

If a user enters an incorrect username or password, the application should display an appropriate error message and allow the user to try again.

## Invalid Form Data

Forms should validate submitted information. Invalid data should be rejected and the user should be shown which information needs to be corrected.

## Insufficient Stock

If a buyer attempts to purchase more products than are available, the order should not be created and the buyer should receive an appropriate error message.

## Invalid or Missing Products

If a requested product does not exist, the application should return an appropriate error rather than crashing.

## Unauthorised Access

If a user attempts to access functionality that belongs to another role or another vendor, access should be denied.

For API requests, appropriate HTTP error responses such as 401, 403, 404, and 400 should be returned depending on the problem.

## Order Cancellation

When a pending order is cancelled, the quantities reserved for the order should be returned to the products' stock.

Orders that are already completed or cancelled should not be changed incorrectly.

## Database Errors

Database operations that affect multiple related records should use database transactions where appropriate. This helps prevent partial updates if an error occurs during an operation.

## External Service Failure

If an external service such as Reddit is unavailable, the API should return an appropriate error response rather than causing the entire application to fail.

## Password Reset Failure

Invalid or expired password reset links should not allow a password to be changed. The user should be informed that they need to request a new reset link.

## Unexpected Application Errors

Unexpected errors should be handled gracefully. Users should receive a useful error page or message rather than sensitive debugging information.

## Recovery

The application should maintain regular database backups so that data can be restored after serious database failure or data loss.

