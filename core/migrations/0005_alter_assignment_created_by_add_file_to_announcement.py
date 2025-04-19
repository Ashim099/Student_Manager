from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_auto_20250418_1055'),
    ]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model('core', 'Announcement').objects.filter(created_by_id__isnull=True).update(created_by_id=6),
            reverse_code=lambda apps, schema_editor: None,
        ),
        migrations.AlterField(
            model_name='Announcement',
            name='created_by',
            field=models.ForeignKey(on_delete=models.CASCADE, to='core.user'),
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model('core', 'Assignment').objects.filter(created_by_id__isnull=True).update(created_by_id=6),
            reverse_code=lambda apps, schema_editor: None,
        ),
        migrations.AlterField(
            model_name='Assignment',
            name='created_by',
            field=models.ForeignKey(on_delete=models.CASCADE, to='core.user'),
        ),
        # Add file to Announcement
        migrations.AddField(
            model_name='Announcement',
            name='file',
            field=models.FileField(null=True, blank=True, upload_to='announcements/'),
        ),
    ]