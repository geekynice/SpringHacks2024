# admin.py

from django.contrib import admin
from .models import UserModel, Preferences

admin.site.register(UserModel)
admin.site.register(Preferences)
