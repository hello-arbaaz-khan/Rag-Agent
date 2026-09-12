from rest_framework import serializers
from apps.integrations.models import GoogleDriveAccount

class GoogleDriveAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleDriveAccount
        fileds = ['user', 'google_email', 'created_at', 'google_account_id']