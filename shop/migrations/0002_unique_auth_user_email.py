
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0001_initial"),
        migrations.swappable_dependency("auth.User"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE UNIQUE INDEX auth_user_email_unique "
                "ON auth_user (email)"
            ),
            reverse_sql=(
                "DROP INDEX auth_user_email_unique ON auth_user"
            ),
        ),
    ]
