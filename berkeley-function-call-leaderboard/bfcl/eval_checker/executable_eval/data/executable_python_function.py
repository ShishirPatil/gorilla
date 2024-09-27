import os
import math
import requests
from bfcl.eval_checker.executable_eval.custom_exception import NoAPIKeyError
import time

# Make sure the env variables are populated
ENV_VARS = ("GEOCODE_API_KEY", "RAPID_API_KEY", "OMDB_API_KEY", "EXCHANGERATE_API_KEY")
api_key = {}
for var in ENV_VARS:
    if os.getenv(var) == "":
        raise NoAPIKeyError()

    api_key[var.replace("_", "-")] = os.getenv(var)


def calculate_triangle_area(base, height):
    """
    Calculates the area of a triangle.
    Args:
        base (integer): The base of the triangle.
        height (integer): The height of the triangle.
    """
    return base * height / 2


def get_distance(pointA, pointB):
    """
    Calculates the distance between two 2D points.
    Args:
        pointA (tuple): The first point.
        pointB (tuple): The second point.
    """
    return ((pointA[0] - pointB[0]) ** 2 + (pointA[1] - pointB[1]) ** 2) ** 0.5


def math_factorial(n):
    """
    Calculates the factorial of a number.
    Args:
        n (integer): The number to calculate the factorial of.
    """
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result


def quadratic_roots(a, b, c):
    """
    Calculates the roots of a quadratic equation.
    Args:
        a (integer): The first coefficient.
        b (integer): The second coefficient.
        c (integer): The third coefficient.
    Returns:
        A list of roots, where each root is either a float or a dictionary
        with 'real' and 'imaginary' parts for complex roots.
    """
    discriminant = b**2 - 4 * a * c
    if discriminant >= 0:
        root1 = (-b + discriminant**0.5) / (2 * a)
        root2 = (-b - discriminant**0.5) / (2 * a)
        roots = [root1, root2]
    else:
        real_part = -b / (2 * a)
        imaginary_part = (abs(discriminant) ** 0.5) / (2 * a)
        roots = [
            {"real": real_part, "imaginary": imaginary_part},
            {"real": real_part, "imaginary": -imaginary_part},
        ]

    return roots


def geometry_area_circle(radius):
    """
    Calculates the area of a circle.
    Args:
        radius (integer): The radius of the circle.
    """
    return math.pi * radius**2


def get_prime_factors(number):
    """
    Calculates the prime factors of a number.
    Args:
        number (integer): The number to calculate the prime factors of.
    """
    factors = []
    divisor = 2
    while number > 1:
        while number % divisor == 0:
            factors.append(divisor)
            number /= divisor
        divisor += 1
    return factors


def math_gcd(a, b):
    """
    Calculates the greatest common divisor of two numbers.
    Args:
        a (integer): The first number. This should be the larger number.
        b (integer): The second number.
    """
    if b == 0:
        return a
    else:
        return math_gcd(b, a % b)


def math_lcm(a, b):
    """
    Calculates the least common multiple of two numbers.
    Args:
        a (integer): The first number. This should be the larger number.
        b (integer): The second number.
    """
    return a * b / math_gcd(a, b)


def calculate_final_velocity(initial_velocity, acceleration, time):
    """
    Calculates the final velocity of an object.
    Args:
        initial_velocity (integer): The initial velocity of the object.
        acceleration (integer): The acceleration of the object.
        time (integer): The time the object has been moving.
    """
    return initial_velocity + acceleration * time


def calculate_displacement(initial_velocity, acceleration, time):
    """
    Calculates the displacement of an object.
    Args:
        initial_velocity (integer): The initial velocity of the object.
        acceleration (integer): The acceleration of the object.
        time (integer): The time the object has been moving.
    """
    return initial_velocity * time + 0.5 * acceleration * time**2


def calculate_electrostatic_potential_energy(charge, voltage):
    """
    Calculates the electrostatic potential energy.
    Args:
        charge (integer): The charge of the object.
        voltage (integer): The voltage of the object.
    """
    return charge * voltage


def calculate_density(mass, volume):
    """
    Calculates the density of an object.
    Args:
        mass (integer): The mass of the object.
        volume (integer): The volume of the object.
    """
    return mass / volume


def mat_mul(matA, matB):
    """
    Multiplies two matrices.
    Args:
        matA (list): The first matrix.
        matB (list): The second matrix.
    """
    result = [[0 for i in range(len(matB[0]))] for j in range(len(matA))]
    for i in range(len(matA)):
        for j in range(len(matB[0])):
            for k in range(len(matB)):
                result[i][j] += matA[i][k] * matB[k][j]
    return result


def calculate_mean(numbers):
    """
    Calculates the mean of a list of numbers.
    Args:
        numbers (list): The list of numbers.
    """
    return sum(numbers) / len(numbers)


def calculate_standard_deviation(numbers):
    """
    Calculates the standard deviation of a list of numbers.
    Args:
        numbers (list): The list of numbers.
    """
    mean = calculate_mean(numbers)
    variance = sum((number - mean) ** 2 for number in numbers) / len(numbers)
    return variance**0.5


def calc_binomial_probability(n, k, p):
    """
    Calculates the probability of getting k successes in n trials.
    Args:
        n (integer): The number of trials.
        k (integer): The number of successes.
        p (integer): The probability of success.
    """
    return (
        math_factorial(n)
        / (math_factorial(k) * math_factorial(n - k))
        * (p**k * (1 - p) ** (n - k))
    )


def calculate_permutations(n, k):
    """
    Calculates the number of permutations of k elements from a set of n elements.
    Args:
        n (integer): The number of elements in the set.
        k (integer): The number of elements to choose.
    """
    return math_factorial(n) / math_factorial(n - k)


def get_fibonacci_sequence(n):
    """
    Calculates the n numbers of the Fibonacci.
    Args:
        n (integer): The number of Fibonacci numbers to calculate.
    """
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i - 1] + sequence[i - 2])
    return sequence


def get_fibonacci_number(n):
    """
    Calculates the nth Fibonacci number.
    Args:
        n (integer): The position of the Fibonacci number to calculate.
    Returns:
        integer: The nth Fibonacci number.
    """
    if n <= 0:
        return "Input should be a positive integer."
    elif n == 1:
        return 0
    elif n == 2:
        return 1
    
    a, b = 0, 1
    for i in range(2, n):
        a, b = b, a + b
    return b


def estimate_derivative(function, x):
    """
    Estimate the derivative of a function at a given point.
    Args:
        function (function): The function to calculate the derivative of.
        x (integer): The point to calculate the derivative at.
    """
    func = eval(function)
    h = 0.0000000001
    return (func(x + h) - func(x)) / h


def calculate_cosine_similarity(vectorA, vectorB):
    """
    Calculates the cosine similarity of two vectors.
    Args:
        vectorA (list): The first vector.
        vectorB (list): The second vector.
    """
    dot_product = sum(vectorA[i] * vectorB[i] for i in range(len(vectorA)))
    magnitudeA = (sum(vectorA[i] ** 2 for i in range(len(vectorA)))) ** 0.5
    magnitudeB = (sum(vectorB[i] ** 2 for i in range(len(vectorB)))) ** 0.5
    return dot_product / (magnitudeA * magnitudeB)


def mortgage_calculator(loan_amount, interest_rate, loan_period):
    """
    Calculates the monthly mortgage payment.
    Args:
        loan_amount (integer): The amount of the loan.
        interest_rate (integer): The interest rate of the loan.
        loan_period (integer): The period of the loan.
    """
    monthly_interest_rate = interest_rate / 12
    number_of_payments = loan_period * 12
    monthly_payment = (
        loan_amount
        * monthly_interest_rate
        * (1 + monthly_interest_rate) ** number_of_payments
        / ((1 + monthly_interest_rate) ** number_of_payments - 1)
    )
    return monthly_payment


def calculate_future_value(present_value, interest_rate, periods):
    """
    Calculates the future value of an investment.
    Args:
        present_value (integer): The present value of the investment.
        interest_rate (integer): The interest rate of the investment.
        periods (integer): The number of periods.
    """
    return present_value * (1 + interest_rate) ** periods


def sort_array(array, reverse=False):
    """
    Sorts an array of numbers.
    Args:
        array (list): The array of numbers.
        reverse (optional bool): Whether to sort the array in reverse order, i.e., descending order.
    """
    return sorted(array, reverse=reverse)


def get_weather_data(coordinates):
    """
    Fetches weather data from the Open-Meteo API for the given latitude and longitude.

    Args:
    coordinates (tuple): The latitude of the location.

    Returns:
    float: The current temperature in the coordinates you've asked for
    """
    lat, long = coordinates
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": long,
        "current": "temperature_2m",
        "temperature_unit": "fahrenheit",
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()["current"]["temperature_2m"]
    else:
        return "Failed to fetch data with status code: {}".format(response.status_code)


def get_coordinates_from_city(city_name):
    """
    Fetches the latitude and longitude of a given city name using the Maps.co Geocoding API.

    Args:
    city_name (str): The name of the city.

    Returns:
    tuple: The latitude and longitude of the city.
    """
    time.sleep(2)  # To avoid rate limiting
    url = "https://geocode.maps.co/search"
    params = {"q": city_name, "api_key": api_key["GEOCODE-API-KEY"]}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]["lat"], data[0]["lon"]
        else:
            return "No data found for the given city name."
    else:
        return "Failed to fetch data with status code: {}".format(response.status_code)


def convert_currency(amount, from_currency, to_currency):
    """
    Converts a given amount from one currency to another using the ExchangeRate-API.

    Args:
    amount (float): The amount of money to convert.
    from_currency (str): The ISO currency code for the base currency.
    to_currency (str): The ISO currency code for the target currency.

    Returns:
    float: The converted amount in the target currency.
    """
    key = api_key["EXCHANGERATE-API-KEY"]
    base_url = f"https://v6.exchangerate-api.com/v6/{key}/latest/{from_currency}"
    response = requests.get(base_url)

    if response.status_code == 200:
        data = response.json()
        rates = data.get("conversion_rates", {})
        if to_currency in rates:
            converted_amount = amount * rates[to_currency]
            return converted_amount
        else:
            return "Target currency code not found."
    else:
        return "Failed to fetch data with status code: {}".format(response.status_code)


def find_term_on_urban_dictionary(term):
    """
    Finds the definition of a term on Urban Dictionary.
    Args:
        term (str): The term to find the definition of.
    """
    url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"

    querystring = {"term": term}

    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "mashape-community-urban-dictionary.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()["list"][0]["definition"]


def get_coordinate_by_ip_address(ip_address):
    """
    Finds the latitude and longitude of an IP address.
    Args:
        ip_address (str): The IP address to find the location of.
    """
    url = f"http://ip-api.com/json/{ip_address}"
    response = requests.get(url)
    try:
        return (response.json()["lat"], response.json()["lon"])
    except:
        return response.json()["message"]


def get_zipcode_by_ip_address(ip_address):
    """
    Finds the zipcode of an IP address.
    Args:
        ip_address (str): The IP address to find the location of.
    """
    url = f"http://ip-api.com/json/{ip_address}"
    response = requests.get(url)
    try:
        return response.json()["zip"]
    except:
        return response.json()["message"]


def get_covid_death_by_country(country):
    """
    Finds the most up to date total deaths of a country result from COVID.
    Args:
        country (str): The country to find the total deaths of, in the format of the country's full name.
    """
    url = "https://covid-193.p.rapidapi.com/statistics"

    querystring = {"country": country}

    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "covid-193.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    try:
        return response.json()["response"][0]["deaths"]["total"]
    except:
        return response.json()


def get_active_covid_case_by_country(country):
    """
    Finds the most up to date active cases of a country result from COVID.
    Args:
        country (str): The country to find the active cases of.
    """
    url = "https://covid-193.p.rapidapi.com/statistics"

    querystring = {"country": country}

    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "covid-193.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    try:
        return response.json()["response"][0]["cases"]["active"]
    except:
        return response.json()


def get_rating_by_amazon_ASIN(ASIN):
    url = "https://real-time-amazon-data.p.rapidapi.com/product-details"
    querystring = {"asin": ASIN, "country": "US"}
    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com",
    }

    retries = 0
    max_retries = 5
    while retries < max_retries:
        response = requests.get(url, headers=headers, params=querystring)
        try:
            return response.json()["data"]["product_star_rating"]
        except KeyError:
            wait_time = 2**retries  # Exponential backoff: 1, 2, 4 seconds
            time.sleep(wait_time)
            retries += 1

    return None


def get_price_by_amazon_ASIN(ASIN):
    url = "https://real-time-amazon-data.p.rapidapi.com/product-details"
    querystring = {"asin": ASIN, "country": "US"}
    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com",
    }

    retries = 0
    max_retries = 5
    while retries < max_retries:
        response = requests.get(url, headers=headers, params=querystring)
        try:
            return response.json()["data"]["product_price"]
        except KeyError:
            wait_time = 2**retries  # Exponential backoff: 1, 2, 4 seconds
            time.sleep(wait_time)
            retries += 1

    return None


def get_product_name_by_amazon_ASIN(ASIN):
    url = "https://real-time-amazon-data.p.rapidapi.com/product-details"
    querystring = {"asin": ASIN, "country": "US"}
    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com",
    }

    retries = 0
    max_retries = 5
    while retries < max_retries:
        response = requests.get(url, headers=headers, params=querystring)
        try:
            return response.json()["data"]["product_title"]
        except KeyError:
            wait_time = 2**retries  # Exponential backoff: 1, 2, 4 seconds
            time.sleep(wait_time)
            retries += 1

    return None


def get_company_name_by_stock_name(stock_name):
    """
    Finds the company name of a stock by its stock name.
    Args:
        stock_name (str): The stock name of the product.
    """
    url = "https://yahoo-finance15.p.rapidapi.com/api/v1/markets/search"

    querystring = {"search": stock_name}

    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "yahoo-finance15.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    try:
        return response.json()["body"][0]["name"]
    except:
        return response.json()


def get_stock_price_by_stock_name(stock_name):
    """
    Finds the price of a stock by its stock name.
    Args:
        stock_name (str): The stock name of the product.
    """
    url = "https://yahoo-finance15.p.rapidapi.com/api/v1/markets/stock/quotes"

    querystring = {"ticker": stock_name}

    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "yahoo-finance15.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    try:
        return float(response.json()["body"][0]["regularMarketPrice"])
    except:
        return response.json()


def get_stock_history(stock_name, interval, diffandsplits="true"):
    """
    Finds the price of a stock by its stock name.
    Args:
        stock_name (str): The stock name of the product.
        interval (str): The interval of the stock history. Allows one of following : 5m|15m|30m|1h|1d|1wk|1mo|3mo
        diffandsplits (optional str): The diff and splits of the stock history. Allows one of following : 'true'|'false'
    """
    url = "https://yahoo-finance15.p.rapidapi.com/api/v1/markets/stock/history"

    querystring = {
        "symbol": stock_name,
        "interval": interval,
        "diffandsplits": diffandsplits,
    }

    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "yahoo-finance15.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    try:
        data = response.json()["body"]
        return {key: data[key] for key in list(data)[-10:]}
    except:
        return response.json()


def retrieve_city_based_on_zipcode(zipcode):
    """
    Finds the city of a zipcode.
    Args:
        zipcode (str): The zipcode of the city.
    """
    url = f"http://ziptasticapi.com/{zipcode}"
    response = requests.get(url)
    try:
        return response.json()["city"]
    except:
        return response.json()


def retrieve_holiday_by_year(country, year):
    """
    Finds the holidays of a year.
    Args:
        year (str): The year of the holidays.
        country (str): The country of the holidays. Possible options: US, AT, DE, ES, FR, GB, IT, NL, PL, RO, SK, UA.
    """
    url = f"https://date.nager.at/api/v3/publicholidays/{year}/{country}"
    response = requests.get(url)
    return response.json()


def get_time_zone_by_coord(long, lat):
    """
    Finds the timezone of a coordinate.
    Args:
        long (str): The longitude of the coordinate.
        lat (str): The latitude of the coordinate.
    """
    url = "https://timezone-by-location.p.rapidapi.com/timezone"

    querystring = {"lat": lat, "lon": long, "c": "1", "s": "0"}

    headers = {
        "X-RapidAPI-Key": api_key["RAPID-API-KEY"],
        "X-RapidAPI-Host": "timezone-by-location.p.rapidapi.com",
    }

    response = requests.get(url, headers=headers, params=querystring)
    try:
        return response.json()["Zones"][0]["TimezoneId"]
    except:
        return response.json()


def linear_regression(x, y, point):
    """
    Finds the linear regression of a set of points.
    Args:
        x (list): The x coordinates of the points.
        y (list): The y coordinates of the points.
        point (int): The point to calculate the linear regression at.
    """
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_x_squared = sum(x_i**2 for x_i in x)
    sum_xy = sum(x[i] * y[i] for i in range(n))
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x**2)
    intercept = (sum_y - slope * sum_x) / n
    return slope * point + intercept


def add_binary_numbers(a, b):
    """
    Adds two binary numbers.
    Args:
        a (str): The first binary number.
        b (str): The second binary number.
    """
    return bin(int(a, 2) + int(b, 2))[2:]


def maxPoints(points) -> int:
    """
    Finds the maximum number of points on a line.
    Args:
        points (list): The list of points. points are 2 element lists.
    """
    counter = 1
    if len(points) < 2:
        return 1
    for i in range(len(points)):
        lst = {}
        for j in range(i + 1, len(points)):
            y = points[j][1] - points[i][1]
            x = points[j][0] - points[i][0]
            if x != 0:
                lst[y / x] = 1 + lst.get(y / x, 0)
            else:
                lst["inf"] = 1 + lst.get("inf", 0)
        for key, value in lst.items():
            counter = max(counter, value)
    return counter + 1


def calculate_investment_value(
    initial_investment,
    annual_contribution,
    years,
    annual_return,
    inflation_rate,
    adjust_for_inflation=True,
):
    """
    Calculates the value of an investment over time.
    Args:
        initial_investment (integer): The initial investment amount.
        annual_contribution (integer): The annual contribution amount.
        years (integer): The number of years to calculate the investment value for.
        annual_return (float): The annual return rate, ranging from 0 to 1.
        inflation_rate (list): The inflation rate for each year in percentage, ranging from 0 to 1.
        adjust_for_inflation (optional bool): Whether to adjust the investment value for inflation.
    """
    current_value = initial_investment
    real_value = initial_investment  # Adjusted for inflation

    for year in range(1, years + 1):
        # Apply annual return
        current_value = current_value * (1 + annual_return) + annual_contribution

        # Adjust for inflation if requested
        if adjust_for_inflation:
            inflation_adjustment = (
                1 - inflation_rate[year - 1]
                if year <= len(inflation_rate)
                else 1 - inflation_rate[-1]
            )
            real_value = (
                real_value * (1 + annual_return - inflation_rate[year - 1])
                + annual_contribution * inflation_adjustment
            )
        else:
            real_value = current_value

    final_value = real_value if adjust_for_inflation else current_value
    return final_value


def calculate_nutritional_needs(weight, height, age, gender, activity_level, goal):
    """
    Calculates the nutritional needs of a person based on their weight, height
    Args:
        weight (integer): The weight of the person.
        height (integer): The height of the person.
        age (integer): The age of the person
        gender (str): The gender of the person. Possible options [male,female,other]
        activity_level (integer): The activity level of the person. Possible options [1,2,3,4,5]
        goal (str): The goal of the person. Possible options [lose,gain,maintain]
    """
    if gender == "male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

    # Total Daily Energy Expenditure (TDEE) Calculation
    activity_multipliers = [1.2, 1.375, 1.55, 1.725, 1.9]
    tdee = bmr * activity_multipliers[activity_level - 1]

    # Adjust TDEE based on goal
    if goal == "lose":
        tdee -= 500  # Creating a deficit to lose weight
    elif goal == "gain":
        tdee += 500  # Creating a surplus to gain weight

    # Macronutrient Distribution
    proteins = (tdee * 0.30) / 4  # 30% of calories from protein, 4 calories per gram
    fats = (tdee * 0.25) / 9  # 25% of calories from fat, 9 calories per gram
    carbohydrates = (tdee * 0.45) / 4  # 45% of calories from carbs, 4 calories per gram

    return {
        "calories": tdee,
        "proteins_g": proteins,
        "fats_g": fats,
        "carbohydrates_g": carbohydrates,
    }


def book_room(
    room_type, price, check_in_date, check_out_date, customer_id, discount_code=None
):
    """
    Books a room for a customer.
    Args:
        room_type (dict): The room type to book.
        check_in_date (str): The check-in date.
        check_out_date (str): The check-out date.
        customer_id (str): The customer ID.
        discount_code (str): The discount code (if any).
    """
    # Assume the first available room is booked (for simplicity)
    booked_room = room_type

    # Calculate price and apply discount if applicable
    if discount_code and discount_code == "DISCOUNT10":
        price *= 0.9  # Apply 10% discount

    booking_details = {
        "customer_id": customer_id,
        "room_number": room_type,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "total_price": price,
    }

    return booking_details


def order_food(item, quantity, price):
    """
    Orders food for a customer.
    Args:
        item (list): The item to order.
        quantity (list): The quantity of the item.
        price (list): The price of the item.
    """
    # Calculate total price
    total_price = sum([quantity[i] * price[i] for i in range(len(item))])
    return total_price


def get_movie_rating(movie_name):
    """
    Fetches the age rating of a movie from the OMDB API.
    Args:
        movie_name (str): The name of the movie.
    """
    url = "http://www.omdbapi.com/"
    params = {"t": movie_name, "apikey": api_key["OMDB-API-KEY"]}
    response = requests.get(url, params=params)
    return response.json()["Rated"]


def get_movie_director(movie_name):
    """
    Fetches the director of a movie from the OMDB API.
    Args:
        movie_name (str): The name of the movie.
    """
    url = "http://www.omdbapi.com/"
    params = {"t": movie_name, "apikey": api_key["OMDB-API-KEY"]}
    response = requests.get(url, params=params)
    return response.json()["Director"]


def polygon_area(vertices):
    """
    Calculate the area of a polygon given its vertices using the shoelace formula.
    Args:
        vertices (list): The vertices of the polygon. Vertices are 2 element lists.
    """
    n = len(vertices)
    if n < 3:
        raise ValueError("A polygon must have at least 3 vertices.")

    # Append the first vertex to the end to complete the loop
    vertices.append(vertices[0])

    # Apply the shoelace formula
    area = 0
    for i in range(n):
        area += (vertices[i][0] * vertices[i + 1][1]) - (
            vertices[i + 1][0] * vertices[i][1]
        )

    area = abs(area) / 2.0
    return area
