import random
from typing import Dict, List, Union

from .long_context import (
    CAR_STATUS_METADATA_EXTENSION,
    INTERMEDIARY_CITIES,
    LONG_WEATHER_EXTENSION,
    PARKING_BRAKE_INSTRUCTION,
)

MAX_FUEL_LEVEL = 50
MIN_FUEL_LEVEL = 0.0
MILE_PER_GALLON = 20.0
MAX_BATTERY_VOLTAGE = 14.0
MIN_BATTERY_VOLTAGE = 10.0


class VehicleControlAPI:

    def __init__(self):
        """
        Initializes the vehicle control API with default values.
        """
        self.fuelLevel: float
        self.batteryVoltage: float
        self.engine_state: str
        self.remainingUnlockedDoors: int
        self.doorStatus: Dict[str, str]

        self.acTemperature: float
        self.fanSpeed: int
        self.acMode: str
        self.humidityLevel: float
        self.headLightStatus: str
        self.brakeStatus: str
        self.brakeForce: float
        self.slopeAngle: float
        self.distanceToNextVehicle: float
        self.cruiseStatus: str
        self.destination: str
        self.frontLeftTirePressure: float
        self.frontRightTirePressure: float
        self.rearLeftTirePressure: float
        self.rearRightTirePressure: float

    def _load_scenario(self, scenario: dict, long_context=False) -> None:
        """
        Loads the scenario for the vehicle control.
        Args:
            scenario (dict): The scenario to load.
        """
        self._random = random.Random((scenario.get("random_seed", 140337)))
        self.fuelLevel = scenario.get("fuelLevel", 0.0)  # in gallons
        self.batteryVoltage = scenario.get("batteryVoltage", 12.6)  # in volts
        self.engine_state = scenario.get("engineState", "stopped")  # running, stopped
        self.remainingUnlockedDoors = scenario.get(
            "remainingUnlockedDoors", 4
        )  # driver, passenger, rear_left, rear_right
        self.doorStatus = scenario.get(
            "doorStatus",
            {
                "driver": "unlocked",
                "passenger": "unlocked",
                "rear_left": "unlocked",
                "rear_right": "unlocked",
            },
        )
        self.remainingUnlockedDoors = 4 - len(
            [1 for door in self.doorStatus.keys() if self.doorStatus[door] == "locked"]
        )
        self.acTemperature = scenario.get("acTemperature", 25.0)  # in degree Celsius
        self.fanSpeed = scenario.get("fanSpeed", 50)  # 0 to 100
        self.acMode = scenario.get("acMode", "auto")  # auto, cool, heat, defrost
        self.humidityLevel = scenario.get("humidityLevel", 50.0)  # in percentage
        self.headLightStatus = scenario.get("headLightStatus", "off")  # on, off
        self.brakeStatus = scenario.get("brakeStatus", "released")  # released, engaged
        self.brakeForce = scenario.get("brakeForce", 0.0)  # in Newtons
        self.slopeAngle = scenario.get("slopeAngle", 0.0)  # in degrees
        self.distanceToNextVehicle = scenario.get(
            "distanceToNextVehicle", 50.0
        )  # in meters
        self.cruiseStatus = scenario.get("cruiseStatus", "inactive")  # active, inactive
        self.destination = scenario.get("destination", "None")
        self.frontLeftTirePressure = scenario.get("frontLeftTirePressure", 32.0)
        self.frontRightTirePressure = scenario.get("frontRightTirePressure", 32.0)
        self.rearLeftTirePressure = scenario.get("rearLeftTirePressure", 30.0)
        self.rearRightTirePressure = scenario.get("rearRightTirePressure", 30.0)

        self.long_context = long_context

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, VehicleControlAPI):
            return False

        for attr_name in vars(self):
            if attr_name.startswith("_"):
                continue
            model_attr = getattr(self, attr_name)
            ground_truth_attr = getattr(value, attr_name)

            if model_attr != ground_truth_attr:
                return False

        return True

    def startEngine(self, ignitionMode: str) -> Dict[str, Union[str, float]]:
        """
        Starts the engine of the vehicle.
        Args:
            ignitionMode (str): The ignition mode of the vehicle. Possible values are "START" and "STOP".
        Returns:
            engineState (str): The state of the engine. Possible values are "running" and "stopped".
            fuelLevel (float): The fuel level of the vehicle in gallons.
            batteryVoltage (float): The battery voltage of the vehicle in volts.
        """
        if self.remainingUnlockedDoors > 0:
            return {
                "error": "All doors must be locked before starting the engine. Here are the unlocked doors: "
                + ", ".join(
                    [
                        door
                        for door, status in self.doorStatus.items()
                        if status == "unlocked"
                    ]
                )
            }
        if self.brakeStatus == "released":
            return {"error": "Press the parking brake before starting the engine."}
        if self.fuelLevel < MIN_FUEL_LEVEL:
            return {"error": "Fuel tank is empty."}
        if ignitionMode == "START":
            self.engine_state = "running"
        elif ignitionMode == "STOP":
            self.engine_state = "stopped"
        else:
            return {"error": "Invalid ignition mode."}

        return {
            "engineState": self.engine_state,
            "fuelLevel": self.fuelLevel,
            "batteryVoltage": self.batteryVoltage,
        }

    def fillFuelTank(self, fuelAmount: float) -> Dict[str, Union[str, float]]:
        """
        Fills the fuel tank of the vehicle. The fuel tank can hold up to 50 gallons.
        Args:
            fuelAmount (float): The amount of fuel to fill in gallons.
        Returns:
            fuelLevel (float): The fuel level of the vehicle in gallons.
        """
        if fuelAmount < 0:
            return {"error": "Fuel amount cannot be negative."}
        if self.fuelLevel + fuelAmount > MAX_FUEL_LEVEL:
            return {"error": "Cannot fill gas above the tank capacity."}
        if self.fuelLevel + fuelAmount < MIN_FUEL_LEVEL:
            return {"error": "Fuel tank is empty. Min fuel level is 0 gallons."}
        self.fuelLevel += fuelAmount
        return {"fuelLevel": self.fuelLevel}

    def lockDoors(self, unlock: bool, door: list[str]) -> Dict[str, Union[str, int]]:
        """
        Locks the doors of the vehicle.
        Args:
            unlock (bool): True if the doors are to be unlocked, False otherwise.
            door (list[str]): The list of doors to lock or unlock. Possible values are "driver", "passenger", "rear_left", "rear_right".
        Returns:
            lockStatus (str): The status of the lock. Possible values are "locked" and "unlocked".
            remainingUnlockedDoors (int): The number of remaining unlocked doors.
        """
        if unlock:
            for d in door:
                self.doorStatus[d] = "unlocked"
                self.remainingUnlockedDoors += 1
            return {
                "lockStatus": "unlocked",
                "remainingUnlockedDoors": self.remainingUnlockedDoors,
            }
        else:
            for d in door:
                self.doorStatus[d] = "locked"
                self.remainingUnlockedDoors -= 1
            return {
                "lockStatus": "locked",
                "remainingUnlockedDoors": self.remainingUnlockedDoors,
            }

    def adjustClimateControl(
        self,
        temperature: float,
        unit: str = "celsius",
        fanSpeed: int = 50,
        mode: str = "auto",
    ) -> Dict[str, Union[str, float]]:
        """
        Adjusts the climate control of the vehicle.
        Args:
            temperature (float): The temperature to set in degree. Default to be celsius.
            unit (str): The unit of temperature. Possible values are "celsius" or "fahrenheit". Default is "celsius".
            fanSpeed (int): The fan speed to set from 0 to 100. Default is 50.
            mode (str): The climate mode to set. Possible values are "auto", "cool", "heat", "defrost". Default is "auto".
        Returns:
            currentTemperature (float): The current temperature set in degree Celsius.
            climateMode (str): The current climate mode set.
            humidityLevel (float): The humidity level in percentage.
        """
        if not (0 <= fanSpeed <= 100):
            return {"error": "Fan speed must be between 0 and 100."}
        self.acTemperature = temperature
        if unit == "fahrenheit":
            self.acTemperature = (temperature - 32) * 5 / 9
        self.fanSpeed = fanSpeed
        self.acMode = mode
        return {
            "currentACTemperature": temperature,
            "climateMode": mode,
            "humidityLevel": self.humidityLevel,
        }

    def get_outside_temperature_from_google(self) -> Dict[str, float]:
        """
        Gets the outside temperature.
        Returns:
            outsideTemperature (float): The outside temperature in degree Celsius.
        """
        if self.long_context:
            LONG_WEATHER_EXTENSION["outsideTemperature"] = self._random.uniform(-10.0, 40.0)
            return LONG_WEATHER_EXTENSION
        return {"outsideTemperature": self._random.uniform(-10.0, 40.0)}

    def get_outside_temperature_from_weather_com(self) -> Dict[str, float]:
        """
        Gets the outside temperature.
        Returns:
            outsideTemperature (float): The outside temperature in degree Celsius.
        """
        return {"error": 404}

    def setHeadlights(self, mode: str) -> Dict[str, str]:
        """
        Sets the headlights of the vehicle.
        Args:
            mode (str): The mode of the headlights. Possible values are "on", "off", "auto".
        Returns:
            headlightStatus (str): The status of the headlights. Possible values are "on" and "off".
        """
        if mode not in ["on", "off", "auto"]:
            return {"error": "Invalid headlight mode."}
        if mode == "on":
            self.headLightStatus = "on"
            return {"headlightStatus": "on"}
        else:
            self.headLightStatus = "off"
            return {"headlightStatus": "off"}

    def displayCarStatus(self, option: str) -> Dict[str, Union[str, float, Dict[str, str]]]:
        """
        Displays the status of the vehicle based on the provided display option.
        Args:
            option (str): The option to display. Possible values are "fuel", "battery", "doors", "climate", "headlights", "brake", "engine".
        Returns:
            status (dict): The status of the vehicle based on the option.
        """
        status = {}
        if self.long_context:
            status["metadata"] = CAR_STATUS_METADATA_EXTENSION
        if option == "fuel":
            status["fuelLevel"] = self.fuelLevel
        elif option == "battery":
            status["batteryVoltage"] = self.batteryVoltage
        elif option == "doors":
            status["doorStatus"] = self.doorStatus
        elif option == "climate":
            status["currentACTemperature"] = self.acTemperature
            status["fanSpeed"] = self.fanSpeed
            status["climateMode"] = self.acMode
            status["humidityLevel"] = self.humidityLevel
        elif option == "headlights":
            status["headlightStatus"] = self.headLightStatus
        elif option == "brake":
            status["brakeStatus"] = self.brakeStatus
            status["brakeForce"] = (self.brakeForce,)
            status["slopeAngle"] = (self.slopeAngle,)
        elif option == "engine":
            status["engineState"] = self.engine_state
        else:
            status["error"] = "Invalid option"
        return status

    def activateParkingBrake(self, mode: str) -> Dict[str, Union[str, float]]:
        """
        Activates the parking brake of the vehicle.
        Args:
            mode (str): The mode to set. Possible values are "engage", "release".
        Returns:
            brakeStatus (str): The status of the brake. Possible values are "engaged" and "released".
            brakeForce (float): The force applied to the brake in Newtons.
            slopeAngle (float): The slope angle in degrees.
        """
        if mode not in ["engage", "release"]:
            return {"error": "Invalid mode"}
        if mode == "engage":
            self.brakeStatus = "engaged"
            self.brakeForce = 500.0
            self.slopeAngle = 10.0
            if self.long_context:
                return {
                    "parkingBrakeInstruction": PARKING_BRAKE_INSTRUCTION,
                    "brakeStatus": "engaged",
                    "brakeForce": 500.0,
                    "slopeAngle": 10.0,
                }
            return {"brakeStatus": "engaged", "brakeForce": 500.0, "slopeAngle": 10.0}
        else:
            self.brakeStatus = "released"
            self.brakeForce = 0.0
            self.slopeAngle = 10.0
            if self.long_context:
                return {
                    "parkingBrakeInstruction": PARKING_BRAKE_INSTRUCTION,
                    "brakeStatus": "released",
                    "brakeForce": 0.0,
                    "slopeAngle": 10.0,
                }
            return {"brakeStatus": "released", "brakeForce": 0.0, "slopeAngle": 10.0}

    def setCruiseControl(
        self, speed: float, activate: bool, distanceToNextVehicle: float
    ) -> Dict[str, Union[str, float]]:
        """
        Sets the cruise control of the vehicle.
        Args:
            speed (float): The speed to set in m/h. The speed should be between 0 and 120 and a multiple of 5.
            activate (bool): True to activate the cruise control, False to deactivate.
            distanceToNextVehicle (float): The distance to the next vehicle in meters.
        Returns:
            cruiseStatus (str): The status of the cruise control. Possible values are "active" and "inactive".
            currentSpeed (float): The current speed of the vehicle in km/h.
            distanceToNextVehicle (float): The distance to the next vehicle in meters.
        """
        if self.engine_state == "stopped":
            return {"error": "Start the engine before activating the cruise control."}
        if activate:
            self.distanceToNextVehicle = distanceToNextVehicle
            if speed < 0 or speed > 120 or speed % 5 != 0:
                return {"error": "Invalid speed"}
            self.cruiseStatus = "active"
            return {
                "cruiseStatus": "active",
                "currentSpeed": speed,
                "distanceToNextVehicle": distanceToNextVehicle,
            }
        else:
            self.cruiseStatus = "inactive"
            self.distanceToNextVehicle = distanceToNextVehicle
            return {
                "cruiseStatus": "inactive",
                "currentSpeed": speed,
                "distanceToNextVehicle": distanceToNextVehicle,
            }

    def get_current_speed(self) -> Dict[str, float]:
        """
        Gets the current speed of the vehicle.
        Returns:
            currentSpeed (float): The current speed of the vehicle in km/h.
        """
        return {"currentSpeed": self._random.uniform(0.0, 120.0)}

    def display_log(self, messages: list[str]):
        """
        Displays the log messages.
        Args:
            messages (list[str]): The list of messages to display.
        Returns:
            log (list[str]): The list of messages displayed.
        """
        return {"log": messages}

    def estimate_drive_feasibility_by_mileage(self, distance: float) -> Dict[str, bool]:
        """
        Estimates the milage of the vehicle given the distance needed to drive.
        Args:
            distance (float): The distance to travel in miles.
        Returns:
            canDrive (bool): True if the vehicle can drive the distance, False otherwise.
        """
        if self.fuelLevel * MILE_PER_GALLON < distance:
            return {"canDrive": False}
        else:
            return {"canDrive": True}

    def liter_to_gallon(self, liter: float) -> float:
        """
        Converts the liter to gallon.
        Args:
            liter (float): The amount of liter to convert.
        Returns:
            gallon (float): The amount of gallon converted.
        """
        return liter * 0.264172

    def gallon_to_liter(self, gallon: float) -> float:
        """
        Converts the gallon to liter.
        Args:
            gallon (float): The amount of gallon to convert.
        Returns:
            liter (float): The amount of liter converted.
        """
        return gallon * 3.78541

    def estimate_distance(self, cityA: str, cityB: str) -> Dict[str, float]:
        """
        Estimates the distance between two cities.
        Args:
            cityA (str): The zipcode of the first city.
            cityB (str): The zipcode of the second city.
        Returns:
            distance (float): The distance between the two cities in km.
        """
        if (cityA == "83214" and cityB == "74532") or (
            cityA == "74532" and cityB == "83214"
        ):
            distance = {"distance": 750.0}
        elif (cityA == "56108" and cityB == "62947") or (
            cityA == "62947" and cityB == "56108"
        ):
            distance = {"distance": 320.0}
        elif (cityA == "71354" and cityB == "83462") or (
            cityA == "83462" and cityB == "71354"
        ):
            distance = {"distance": 450.0}
        elif (cityA == "47329" and cityB == "52013") or (
            cityA == "52013" and cityB == "47329"
        ):
            distance = {"distance": 290.0}
        elif (cityA == "69238" and cityB == "51479") or (
            cityA == "51479" and cityB == "69238"
        ):
            distance = {"distance": 630.0}
        elif (cityA == "94016" and cityB == "83214") or (
            cityA == "83214" and cityB == "94016"
        ):
            distance = {"distance": 980.0}
        elif (cityA == "94016" and cityB == "94704") or (
            cityA == "94704" and cityB == "94016"
        ):
            distance = {"distance": 600.0}
        elif (cityA == "94704" and cityB == "08540") or (
            cityA == "08540" and cityB == "94704"
        ):
            distance = {"distance": 2550.0}
        elif (cityA == "94016" and cityB == "08540") or (
            cityA == "08540" and cityB == "94016"
        ):
            distance = {"distance": 1950.0}
        else:
            distance = {"distance": 0.0}

        if self.long_context:
            distance["intermediaryCities"] = INTERMEDIARY_CITIES
        return distance

    def get_zipcode_based_on_city(self, city: str) -> Dict[str, str]:
        """
        Gets the zipcode based on the city.
        Args:
            city (str): The name of the city.
        Returns:
            zipcode (str): The zipcode of the city.
        """
        if city == "Rivermist":
            return {"zipcode": "83214"}
        elif city == "Stonebrook":
            return {"zipcode": "74532"}
        elif city == "Maplecrest":
            return {"zipcode": "56108"}
        elif city == "Silverpine":
            return {"zipcode": "62947"}
        elif city == "Shadowridge":
            return {"zipcode": "71354"}
        elif city == "Sunset Valley":
            return {"zipcode": "83462"}
        elif city == "Oakendale":
            return {"zipcode": "47329"}
        elif city == "Willowbend":
            return {"zipcode": "52013"}
        elif city == "Crescent Hollow":
            return {"zipcode": "69238"}
        elif city == "Autumnville":
            return {"zipcode": "51479"}
        elif city == "San Francisco":
            return {"zipcode": "94016"}
        else:
            return {"zipcode": "00000"}

    def set_navigation(self, destination: str) -> Dict[str, str]:
        """
        Navigates to the destination.
        Args:
            destination (str): The destination to navigate in the format of street, city, state.
        Returns:
            status (dict): The status of the navigation.
        """
        self.destination = destination
        return {"status": "Navigating to " + destination}

    def check_tire_pressure(self):
        """
        Checks the tire pressure of the vehicle.
        Returns:
            tirePressure (dict): The tire pressure of the vehicle.
        """
        healthy_tire_pressure = (
            self.frontLeftTirePressure
            + self.frontRightTirePressure
            + self.rearLeftTirePressure
            + self.rearRightTirePressure
        ) / 4 < 35
        tire_status = {
            "frontLeftTirePressure": self.frontLeftTirePressure,
            "frontRightTirePressure": self.frontRightTirePressure,
            "rearLeftTirePressure": self.rearLeftTirePressure,
            "rearRightTirePressure": self.rearRightTirePressure,
            "healthy_tire_pressure": healthy_tire_pressure,
        }

        if self.long_context:
            tire_status["car_info"] = CAR_STATUS_METADATA_EXTENSION
        return tire_status

    def find_nearest_tire_shop(self) -> Dict[str, str]:
        """
        Finds the nearest tire shop.
        Returns:
            shopLocation (str): The location of the nearest tire shop.
        """
        return {"shopLocation": "456 Oakwood Avenue, Rivermist, 83214"}
