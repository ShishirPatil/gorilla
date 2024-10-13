from typing import Dict, List, Union, Optional
from datetime import datetime

class FitnessTrackerAPI:
    """
    A class representing the Fitness Tracker API for managing fitness activities.

    Attributes:
        activities (List[Dict[str, Union[str, float]]]): List of logged activities which include name, and calories burned
        food_log (List[Dict[str, Union[str, float]]]): List of logged food intake include calories and protein eaten
        water_intake (float): Amount of water intake by user measured in liters
        calorie_goal (Optional[float]): User's daily calorie goal
        protein_goal (Optional[float]): User's daily protein goal
        water_goal (Optional[float]): User's daily water intake goal measured in liters
    """


    def __init__(self):
        """
        Initialize the FitnessTrackerAPI instance
        """
        self.activities: List[Dict[str, Union[str, float]]] = []
        self.food_log: List[Dict[str, Union[str, float]]] = []
        self.water_intake: float = 0.0
        self.calorie_goal: Optional[float] = None
        self.protein_goal: Optional[float] = None
        self.water_goal: Optional[float] = None
    
    def add_activity(self, activity_name: str, calories_burned: float) -> Dict[str, str]:
        """
        Log activity with the number of calories that were burned 

        Args:
            activity_name (str): The name of the activity
            calories_burned (float): The number of calories burned during the activity

        Returns:
            result (Dict[str, str]): Confirms the activity has been added
        """
        self.activities.append({
            "activity_name": activity_name,
            "calories_burned": calories_burned
        })
        return {"result": f"Activity '{activity_name}' added with {calories_burned} calories burned."}

    def calories_burned(self) -> float:
        """
        Calculate the total calories that were burned from the activities done

        Returns:
            total_calories (float): The total calories that were burned
        """
        return sum(activity['calories_burned'] for activity in self.activities)
    
    def log_food(self, food_name: str, calories: float, protein: float) -> Dict[str, str]:
        """
        Log the amount of calories and protein eaten via food

        Args:
            food_name (str): The name of the food item being logged
            calories (float): The amount of calories in the food
            protein: (float): The amount of protein in the food 
        
        Returns: 
            result (Dict[str, str]): Confirms food has been added
        """
        self.food_log.append({
            "food_name": food_name,
            "calories": calories,
            "protein": protein
        })
        return {"result": f"Food '{food_name}' added with {calories} calories and {protein}g of protein."}
    
    def calories_eaten(self) -> float:
        """
        Calculates the total calories consumed from the logged food items

        Returns:
            total_calories (float): The total calories consumed
        """
        return sum(food['calories'] for food in self.food_log)
    
    def protein_eaten(self) -> float:
        """
        Calculates the total protein consumed from the logged food items

        Returns:
            total_protein (float): The total protein consumed
        """
        return sum(food['protein'] for food in self.food_log)
    
    def add_water(self, amount: float) -> Dict[str, str]:
        """
        Logs the water intake in liters

        Args:
            amount (float): The amount of water drank in liters

        Returns:
            result (Dict[str, str]): Confirms water has been logged properly
        """
        self.water_intake += amount
        return {"result": f"{amount} liters of water added."}
    
    def set_goal(self, calorie_goal: float, protein_goal: float, water_goal: float) -> Dict[str, str]:
        """
        Set a daily goal for calorie, protein, and water consumption

        Args:
            calorie_goal (float): The calorie goal
            protein_goal (float): The protein goal
            water_goal (float): The water goal

        Returns:
            result (Dict[str, str]): Confirms the goal has been set
        """
        self.calorie_goal = calorie_goal
        self.protein_goal = protein_goal
        self.water_goal = water_goal
        return {"result": f"Goals added: {calorie_goal} calories, {protein_goal}g protein, {water_goal} liters of water."}
    
    def get_summary(self) -> Dict[str, Union[str, float]]:
        """
        Gets a summary of all the activities, food, and water logged

        Returns:
            summary (Dict[str, Union[str, float]]): Summary of activities, food, water, and goals.
        """
        total_burned = self.calories_burned()
        total_eaten = self.calories_eaten()
        total_protein = self.protein_eaten()
        return {
            "calories_burned": total_burned,
            "calories_eaten": total_eaten,
            "protein_eaten": total_protein,
            "water_intake": self.water_intake,
            "calorie_goal": self.calorie_goal,
            "protein_goal": self.protein_goal,
            "water_goal": self.water_goal,
            "message": "Summary of today's fitness activities and nutrition."
        }
    
    def check_goals(self) -> Dict[str, str]:
        """
        Check if the fitness goals have been met 

        Returns:
            goal_status (Dict[str, str]): Status report for each goal set
        """
        calorie_status = "met" if self.calorie_goal and self.calories_eaten() >= self.calorie_goal else "not met"
        protein_status = "met" if self.protein_goal and self.protein_eaten() >= self.protein_goal else "not met"
        water_status = "met" if self.water_goal and self.water_intake >= self.water_goal else "not met"

        return {
            "calorie_goal": f"Calorie goal is {calorie_status}.",
            "protein_goal": f"Protein goal is {protein_status}.",
            "water_goal": f"Water intake goal is {water_status}."
        }