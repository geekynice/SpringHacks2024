from django.urls import path,include
from NCT_HACKS_APP import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('', views.index, name="index"),
]