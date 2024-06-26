from django.db import models
from django.contrib.auth.models import User

class UserModel(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    profile_photo = models.ImageField(upload_to='static/profile/', blank=True, null=True)
    weight = models.FloatField() 
    height = models.FloatField()  
    preference = models.TextField(max_length=500, null=True, default='')
    REQUIRED_FIELDS = ['date_of_birth', 'email']

    def __str__(self):
        return self.user.username

class Preferences(models.Model):
    DIET_OPTIONS = [
        ('Vegan', 'Vegan'),
        ('Non-veg', 'Non-veg'),
        ('Veg', 'Veg'),
        ('Gluten free', 'Gluten free'),
    ]
    GOAL_OPTIONS = [
        ('lose_weight', 'Lose weight'),
        ('gain_mass', 'Gain mass'),
        ('maintain_weight', 'Maintain weight'),
    ]

    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='preferences') # instead of this, use the same id to make relation
    diet_option = models.CharField(max_length=50, choices=DIET_OPTIONS)
    nut_allergic = models.BooleanField(default=False)
    goal = models.CharField(max_length=50, choices=GOAL_OPTIONS)

    def __str__(self):
        return f"{self.user.id}'s Preferences"


class Meal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    price = models.DecimalField(max_digits=10, decimal_places=2)
    name = models.CharField(max_length=255)
    calories = models.CharField(max_length=255)  
    desc = models.TextField()
    health_benefits = models.JSONField(default=list)  
    recipe = models.JSONField(default=list)  
    date_added = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.user.username}'s Meal: {self.name}"
    