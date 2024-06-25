from django.urls import path,include
from NCT_HACKS_APP import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('', views.index, name="index"),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('preferences/', views.preferences_view, name='preferences'),
    path('meal-suggestion/', views.MealSuggestionView, name='meal_suggestion'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('photomeal/', views.meal_from_photo_view, name='meal_from_photo')
    path('generate/', views.generate_meals, name='generate_meal'),
]