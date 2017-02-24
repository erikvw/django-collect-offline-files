from rest_framework import serializers

from edc_sync_files.models import history


class HistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = history
