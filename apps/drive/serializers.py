from rest_framework import serializers
from apps.drive.models import DriveDocument, GoogleDriveAccount

class DriveDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriveDocument
        fileds = '__all__'