from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_alter_assignment_created_by_add_file_to_announcement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='Program',
            name='created_by',
            field=models.ForeignKey(on_delete=models.CASCADE, to='core.user'),
        ),
    ]