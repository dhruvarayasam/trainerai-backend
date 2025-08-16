from pydantic import BaseModel, Field
from typing import Dict, List


class PlanSpecifications(BaseModel):
    num_days_a_week: int = Field(..., gt=0, description="Number of workout days per week")
    fitness_goal: str = Field(..., description="User's fitness goal (e.g., weight loss, muscle gain)")
    avg_workout_length: int = Field(..., gt=0, description="Average workout length in minutes")
    experience_level: str = Field(..., description="User's experience level (e.g., beginner, intermediate, advanced)")
    intensity: str = Field(..., description="Desired workout intensity (e.g., low, medium, high)")

class WorkoutExercise(BaseModel):
    exercise: str
    sets: int
    reps: int
    rest: int

class WorkoutPlan(BaseModel):
    days: Dict[str, List[WorkoutExercise]]  # e.g., {"Monday": [WorkoutExercise, ...], ...}

class WorkoutPlanRequest(BaseModel):
    plan_specifications: PlanSpecifications

class WorkoutPlanResponse(BaseModel):
    workout_plan: WorkoutPlan
