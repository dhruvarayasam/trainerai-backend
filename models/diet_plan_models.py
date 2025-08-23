from pydantic import BaseModel, Field
from typing import Dict, List


class DietSpecifications(BaseModel):
    calories_per_day: int = Field(..., gt=0, description="Target daily calorie intake")
    dietary_preference: str = Field(..., description="Diet type (e.g., vegetarian, vegan, keto)")
    meals_per_day: int = Field(..., gt=0, description="Number of meals per day")
    allergies: List[str] = Field(default_factory=list, description="Food allergies or restrictions")
    goal: str = Field(..., description="Fitness goal (e.g., weight loss, muscle gain)")


class Meal(BaseModel):
    name: str
    foods: List[str]
    calories: int


class DietPlan(BaseModel):
    days: Dict[str, List[Meal]]  # e.g. {"Monday": [Meal(...), Meal(...)]}


class DietPlanRequest(BaseModel):
    plan_specifications: DietSpecifications


class DietPlanResponse(BaseModel):
    diet_plan: DietPlan
