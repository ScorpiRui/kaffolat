from django.db import migrations, models


def set_existing_repairs_ready(apps, schema_editor):
    QrItem = apps.get_model("main", "QrItem")
    QrItem.objects.filter(item_type="repair", is_completed=False).update(repair_ready_to_finish=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0007_qritem_is_completed_qritem_item_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="qritem",
            name="repair_ready_to_finish",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(set_existing_repairs_ready, noop_reverse),
    ]
