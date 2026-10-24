from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [('notifications','0004_hierarchy_notice_features')]
    operations = [migrations.AddField(model_name='notification',name='push_sent',field=models.BooleanField(default=False))]
