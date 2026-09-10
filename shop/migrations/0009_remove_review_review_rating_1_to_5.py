from typing import ClassVar

from django.db import migrations


class Migration(migrations.Migration):
    dependencies: ClassVar[list[tuple[str, str]]] = [
        ("shop", "0008_alter_review_options_and_more"),
    ]

    operations: ClassVar[list[migrations.Operation]] = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[],
        ),
    ]
