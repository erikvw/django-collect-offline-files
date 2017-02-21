from datetime import date

from django.conf import settings
from django.core.files import File

from model_mommy.recipe import Recipe

from .models import UploadTransactionFile, UploadSkipDays


path = (settings.MEDIA_ROOT + '/bcpp_otse_201702162025.json')
f = open(path, 'r')
djangoFile = File(f)

transaction = Recipe(
    UploadTransactionFile,
    transaction_file=djangoFile,
    consume=True,
)

skip_date = Recipe(
    UploadSkipDays,
    skip_date=date(2017, 2, 17),
    skip_until_date=date(2017, 2, 17),
    identifier='otse',
)
