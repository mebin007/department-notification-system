import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [('notifications','0003_notification_semester'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name='profile',name='is_approved',field=models.BooleanField(default=True)),
        migrations.AddField(model_name='profile',name='created_by',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='created_profiles',to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='notification',name='is_pinned',field=models.BooleanField(default=False)),
        migrations.AddField(model_name='notification',name='is_college_wide',field=models.BooleanField(default=False)),
        migrations.AddField(model_name='notification',name='approval_status',field=models.CharField(choices=[('PUBLISHED','Published'),('PENDING','Awaiting principal approval')],default='PUBLISHED',max_length=12)),
        migrations.AddField(model_name='notification',name='publish_at',field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AddField(model_name='notification',name='author',field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name='dnms_notifications',to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name='notification',name='related_links',field=models.JSONField(blank=True,default=list,help_text='List of {label, url} objects')),
        migrations.AddField(model_name='notification',name='contact_name',field=models.CharField(blank=True,max_length=150)),
        migrations.AddField(model_name='notification',name='contact_email',field=models.EmailField(blank=True,max_length=254)),
        migrations.AddField(model_name='notification',name='contact_phone',field=models.CharField(blank=True,max_length=40)),
        migrations.CreateModel(name='NotificationAttachment',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('file',models.FileField(upload_to='notice_pdfs/%Y/%m/')),('uploaded_at',models.DateTimeField(auto_now_add=True)),('notification',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='attachments',to='notifications.notification'))]),
        migrations.CreateModel(name='PushSubscription',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('endpoint',models.URLField(max_length=1000,unique=True)),('p256dh',models.CharField(max_length=255)),('auth',models.CharField(max_length=255)),('created_at',models.DateTimeField(auto_now_add=True)),('user',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='push_subscriptions',to=settings.AUTH_USER_MODEL))]),
    ]
