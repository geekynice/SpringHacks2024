# admin.py

from django.contrib import admin
from .models import UserModel, Preferences, Meal

admin.site.register(UserModel)
admin.site.register(Preferences)
admin.site.register(Meal)
