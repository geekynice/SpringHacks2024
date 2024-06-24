from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Preferences, UserModel
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
import os
import pandas as pd
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from groq import Groq


@login_required
def index(request):
    return render(request, 'index.html')

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Function to load CSV data
def load_csv(file_path):
    return pd.read_csv(file_path)

# Function to query the model
def query_model(prompt):
    messages = [{
        "role": "user",
        "content": prompt
    }]
    completion = client.chat.completions.create(
        model="llama3-70b-8192",  # Replace with your desired model
        messages=messages,
        temperature=1,  # Adjust temperature for more creative or conservative response
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    return completion

def parse_response(completion):
    ai_response = ""
    ingredients = []
    recipe_steps = []
    current_section = None
    
    for chunk in completion:
        ai_response += chunk.choices[0].delta.content or ""
        lines = ai_response.split("\n")
        
        for line in lines:
            if line.startswith("**Recipe:**"):
                current_section = "recipe"
            elif line.startswith("**Instructions:**"):
                current_section = "instructions"
            elif current_section == "recipe":
                if line.strip().startswith("*"):
                    ingredients.append(line.strip("* ").strip())
            elif current_section == "instructions":
                if line.strip().startswith("1.") or line.strip().startswith("2.") or line.strip().startswith("3.") or line.strip().startswith("4.") or line.strip().startswith("5.") or line.strip().startswith("6.") or line.strip().startswith("7."):
                    recipe_steps.append(line.strip())

    return ai_response.strip(), ingredients, recipe_steps

def MealSuggestionView(request):
    # Load the CSV file (replace with your path)
    csv_file_path = '/Users/nicebanjara/Desktop/Projects/quiz_ai/cleaned-data.csv'
    df = load_csv(csv_file_path)

    if request.method == 'POST':
        # Get form data
        diet_option = request.POST.get('diet_option')
        nut_allergic = request.POST.get('nut_allergic')
        goal = request.POST.get('goal')

        # Create the prompt for the model
        prompt = f"Generate a meal suggestion with the following details:\n"
        prompt += f"Meal Name:\n"
        prompt += f"Calories:\n"
        prompt += f"Price:\n"
        prompt += f"Health Benefits: []\n"
        prompt += f"Recipe: []\n\n"
        prompt += f"Based on the available dataset and your preferences:\n"
        prompt += f"Diet Option: {diet_option}\n"
        prompt += f"Nut Allergic: {nut_allergic}\n"
        prompt += f"Goal: {goal}\n"
        prompt += f"Dataset Preview:\n{df.head().to_string()}"

        # Query the model
        completion = query_model(prompt)

        related_data, ingredients, recipe_steps = parse_response(completion)

        meal_name = ""
        calories = ""
        price = ""
        for line in related_data.splitlines():
            if line.startswith("**Meal Name:**"):
                meal_name = line.split(":")[1].strip()
            elif line.startswith("**Calories:**"):
                calories = line.split(":")[1].strip()
            elif line.startswith("**Price:**"):
                price = line.split(":")[1].strip()

        context = {
            'meal_name': meal_name,
            'calories': calories,
            'price': price,
            'ingredients': ingredients,
            'recipe_steps': recipe_steps,
            'diet_option': diet_option,
            'nut_allergic': nut_allergic,
            'goal': goal,
            'dataset_preview': df.head().to_html(),  
        }

        return render(request, 'meal.html', context)

    # Return the initial page or handle GET request if not POST
    context = {
        'dataset_preview': df.head().to_html(),
    }
    return render(request, 'meal.html', context)

User = get_user_model()

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        date_of_birth = request.POST['date_of_birth']
        profile_photo = request.FILES.get('profile_photo', None)
        weight = request.POST['weight']
        height = request.POST['height']

        user = User.objects.create_user(username=username, password=password, first_name= first_name, last_name=last_name, email = email)

        custom_user = UserModel.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            profile_photo=profile_photo,
            weight=weight,
            height=height
        )

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('preferences')  

    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'login.html')

@login_required
def preferences_view(request):
    if request.method == 'POST':
        diet_option = request.POST.get('diet_option')
        nut_allergic = request.POST.get('nut_allergic') == 'on'
        goal = request.POST.get('goal')

        # Ensure the logged-in user has a CustomUser instance
        custom_user = UserModel.objects.get(user=request.user)

        # Save preferences for the user
        Preferences.objects.create(
            user=custom_user,
            diet_option=diet_option,
            nut_allergic=nut_allergic,
            goal=goal
        )

        return redirect('index')  # Redirect to a home page or another appropriate page

    return render(request, 'preferences.html')


def logout_view(request):
    logout(request)
    return redirect('login')