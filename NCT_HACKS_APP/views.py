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

def dashboard_view(request):
    return render(request, 'dashboard.html')

def meal_from_photo_view(request):
    return render(request, 'meal_from_photo.html' )

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
    print("Querying model with prompt:")
    print(prompt)
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
    instructions = []
    health_benefits = []
    current_section = None
    
    # Join all chunks into a single string
    for chunk in completion:
        ai_response += chunk.choices[0].delta.content or ""
    
    # Split by lines
    lines = ai_response.split("\n")
    
    # Process each line
    for line in lines:
        if line.startswith("**Health Benefits:**"):
            current_section = "health benefits"
        elif line.startswith("**Recipe:**"):
            current_section = "instructions"
        elif current_section == "health benefits" and line.strip().startswith("* "):
            health_benefits.append(line.strip("* ").strip())
        elif line.startswith("Instructions:"):
            current_section = "instructions"
        elif current_section == "instructions":
            if line.strip().startswith(("1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ")):
                recipe_steps.append(line.strip())
                instructions.append(line.strip())
                ingredients.append(line.strip("* ").strip())



    ingredients = [ingredient.strip() for ingredient in ingredients]
    instructions = [instruction.strip() for instruction in instructions]
    recipe_steps = [recipe.strip() for recipe in recipe_steps]
    health_benefits = [benefit.strip('*').strip() for benefit in health_benefits]
    print(ingredients)
    print(recipe_steps)
    print(instructions)
    print("Health Benefits: ", health_benefits)
    
    return ai_response.strip(), ingredients, recipe_steps, instructions, health_benefits

def MealSuggestionView(request):
    csv_file_path = r'C:\Users\prajw\Downloads\NCT Hackathon - Spring 2024\SpringHacks2024\cleaned-data.csv'
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

        print("Generated prompt:")
        print(prompt)

        # Query the model
        completion = query_model(prompt)

        print("Model completion received:")
        print(completion)

        # Parse model response
        related_data, ingredients, recipe_steps, instructions, health_benefits = parse_response(completion)

        print("Parsed response:")
        print(f"Related Data:\n{related_data}")
        print(f"Ingredients:\n{ingredients}")
        print(f"Recipe Steps:\n{recipe_steps}")
        print(f"Instructions:\n{instructions}")
        print(f"Health Benefits:\n{health_benefits}")

        # Extract meal details
        meal_name = ""
        calories = ""
        price = ""
        for line in related_data.splitlines():
            clean_line = line.strip()
            if clean_line.startswith("**Meal Name:**"):
                meal_name = clean_line.replace("**Meal Name:**", "").strip('*').strip()
            elif clean_line.startswith("**Calories:**"):
                calories = clean_line.replace("**Calories:**", "").strip('*').strip()
            elif clean_line.startswith("**Price:**"):
                price = clean_line.replace("**Price:**", "").strip('*').strip()

        print(f"Extracted Meal Name: {meal_name}")
        print(f"Extracted Calories: {calories}")
        print(f"Extracted Price: {price}")

        # Prepare context for rendering template
        context = {
            'meal_name': meal_name,
            'calories': calories,
            'price': price,
            'ingredients': ingredients,
            'recipe_steps': recipe_steps,
            'instructions': instructions,
            'health_benefits': health_benefits,
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

    print("Rendering initial page with dataset preview:")
    print(context)

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
            return redirect('meal')
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