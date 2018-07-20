from django_collect_offline.site_offline_models import site_offline_models
from django_collect_offline.offline_model import OfflineModel

offline_models = ['django_collect_offline_files.testmodel']
site_offline_models.register(offline_models, OfflineModel)
