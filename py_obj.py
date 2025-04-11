from pydantic import BaseModel
from typing import List, Dict

class MealItem(BaseModel):
    name: str
    ingredients: List[str]
    calories: int

class Meals(BaseModel):
    breakfast: List[MealItem]
    lunch: List[MealItem]
    dinner: List[MealItem]
    snacks: List[MealItem]

class MealPlanDay(BaseModel):
    day: str
    calories: int
    macronutrients: Dict[str, int]
    meals: Meals

class DietResponse(BaseModel):
    dailyCalorieDistribution: Dict[str, str]
    dailyNutritionAverage: Dict[str, str]
    dailyWaterIntake: str
    primaryGoal: str
    dietpreference: str
    workoutRoutine: Dict[str, str]
    mealPlans: List[MealPlanDay]