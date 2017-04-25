import os

from django.conf import settings
from django.core.files import File

from model_mommy.recipe import Recipe

from .models import UploadTransactionFile


path = os.path.join(settings.MEDIA_ROOT, 'bcpp_otse_201702162025.json')

transaction = Recipe(
    UploadTransactionFile,
    transaction_file=File(open(path)),
    consume=True,
)
