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
        running_start_time (Optional[datetime]): Logs user's run start time of the user's most recent run
        running_duration (Optional[float]): Logs user's most recent run duration in minutes
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
        self.running_start_time: Optional[datetime] = None
        self.running_duration: Optional[float] = None
    
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
        if calories <= 0:
            return {"error": "Calories per serving must be greater than zero."}
        
        if protein <= 0:
            return {"error": "Calories per serving must be greater than zero."}
        
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
    
    def remaining_calories(self) -> float:
        """
        Calculate the remaining calories needed to meet the calorie goal

        Returns:
            remaining_calories (float): The number of calories left to be consumed to meet the goal
        """
        if self.calorie_goal is None:
            return 0.0
        remaining = self.calorie_goal - self.calories_eaten()
        return max(0.0, remaining)
    
    def eat_until_calorie_goal(self, food_name: str) -> Dict[str, Union[str, float, int]]:
        """
        Continue to eat specified food item repeatedly until daily calorie goal is met

        Args:
            food_name (str): The name of the food item to eat
        
        Returns:
            result (Dict[str, Union[str, float, int]]): Number of servings ate to reach calorie goal
        """
        if not self.calorie_goal:
            return {"error": "Calorie goal not set."}
        
        food_item = next((food for food in self.food_log if food['food_name'] == food_name), None)
    
        if not food_item or not food_item.get('calories'):
            return {"error": f"Food item '{food_name}' is not in the food log or no calorie information."}
    
        calories_per_serving = food_item['calories']
        protein_per_serving = food_item['protein']
        
        calories_needed = self.calorie_goal - self.calories_eaten()
        servings = 0

        while calories_needed > 0:
            self.log_food(food_name, calories=calories_per_serving, protein=protein_per_serving)
            calories_needed -= calories_per_serving
            servings += 1
        
        return {
            "result": f"Ate {servings} servings of {food_name} to meet your calorie goal.",
            "servings": servings,
            "total_calories": servings * calories_per_serving
        }
    
    def eat_until_protein_goal(self, food_name: str) -> Dict[str, Union[str, float, int]]:
        """
        Continue to eat specified food item repeatedly until daily protein goal is met

        Args:
            food_name (str): The name of the food item to eat
        
        Returns:
            result (Dict[str, Union[str, float, int]]): Number of servings ate to reach protein goal
        """
        if not self.protein_goal:
            return {"error": "Protein goal not set."}
        food_item = next((food for food in self.food_log if food['food_name'] == food_name), None)
    
        if not food_item or not food_item.get('protein'):
            return {"error": f"Food item '{food_name}' is not in the food log or no protein information."}
    
        calories_per_serving = food_item['calories']
        protein_per_serving = food_item['protein']
        
        protein_needed = self.protein_goal - self.protein_eaten()
        servings = 0

        while protein_needed > 0:
            self.log_food(food_name, calories=calories_per_serving, protein=protein_per_serving)
            protein_needed -= protein_per_serving
            servings += 1
        
        return {
            "result": f"Ate {servings} servings of {food_name} to meet your protein goal.",
            "servings": servings,
            "total_protein": servings * protein_per_serving
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
    
    def start_running(self) -> Dict[str, str]:
        """
        User starts their run by logging their start time
        
        Returns:
            result (Dict[str, str]): Confirms the user has started running
        """
        self.running_start_time = datetime.now()
        return {"result": "Running session started."}
    
    def stop_running(self) -> Dict[str, Union[str, float]]:
        """
        Stop the running session and calculates the total run time
        
        Returns:
            result (Dict[str, Union[str, float]]): The total time in minutes of the run
        """
        if not self.running_start_time:
            return {"error": "No run in progress."}
        
        running_end_time = datetime.now()
        duration = (running_end_time - self.running_start_time).total_seconds() / 60 
        self.running_duration = duration
        self.running_start_time = None
        return {"result": f"Running session ended. You ran for {duration:.2f} minutes."}

    def calculate_distance(self, pace: float) -> Dict[str, Union[str, float]]:
        """
        Calculate the total distance covered based on running time and pace

        Args:
            pace (float): Running pace in miles per minute.
        
        Returns:
            result (Dict[str, Union[str, float]]): The total distance ran in miles
        """
        if self.running_duration is None:
            return {"error": "Run not started or still in progess."}
        distance = self.running_duration * pace
        return {"result": f"You ran {distance:.2f} miles."}
    