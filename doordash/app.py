# https://developer.doordash.com/en-US/api/drive/#tag/Delivery/operation/CancelDelivery 

from os import access
import jwt.utils
import time
import math
import requests

accessKey = {
  "developer_id": "86d7f25d-a10e-4091-935a-449db30b5f70",
  "key_id": "c9613cc0-3572-4c4d-be7e-cd38f372a17f",
  "signing_secret": "YjD_zYVpGrXITD3kGjOJ6zSk_hNpyP7jZOQTId9btJk"
}

external_delivery_id = "D-23421"
pickup_address = "901 Market Street 6th Floor San Francisco, CA 94103"
pickup_business_name = "Wells Fargo SF Downtown"
pickup_phone_number =  "+16505555555"
pickup_instructions = "Enter gate code 1234 on the callbox."
dropoff_address = "901 Market Street 6th Floor San Francisco, CA 94103"
dropoff_business_name = "Wells Fargo SF Downtown"
dropoff_phone_number = "+16505555555"
dropoff_instructions = "Enter gate code 1234 on the callbox."
order_value = 1999

token = jwt.encode(
    {
        "aud": "doordash",
        "iss": accessKey["developer_id"],
        "kid": accessKey["key_id"],
        "exp": str(math.floor(time.time() + 300)),
        "iat": str(math.floor(time.time())),
    },
    jwt.utils.base64url_decode(accessKey["signing_secret"]),
    algorithm="HS256",
    headers={"dd-ver": "DD-JWT-V1"})

print(token)

endpoint = "https://openapi.doordash.com/drive/v2/deliveries/"

headers = {"Accept-Encoding": "application/json",
           "Authorization": "Bearer " + token,
           "Content-Type": "application/json"}

request_body = { # Modify pickup and drop off addresses below
    "external_delivery_id": external_delivery_id,
    "pickup_address": pickup_address,
    "pickup_business_name": pickup_business_name,
    "pickup_phone_number": pickup_phone_number,
    "pickup_instructions": pickup_instructions,
    "dropoff_address": dropoff_address,
    "dropoff_business_name": dropoff_business_name,
    "dropoff_phone_number": dropoff_phone_number,
    "dropoff_instructions": dropoff_instructions,
    "order_value": order_value
}

#post req
create_delivery = requests.post(endpoint, headers=headers, json=request_body)
print(create_delivery)
print(create_delivery.headers)
print(create_delivery.status_code)
print(create_delivery.text)
print(create_delivery.reason)

# get req
# get_delivery = requests.get(endpoint + external_delivery_id, headers=headers) 
# print(get_delivery.status_code)
# print(get_delivery.text)
# print(get_delivery.url)

#cancel req
cancel_delivery = requests.put(endpoint + external_delivery_id + "/cancel", headers=headers)

print("Status Code:", cancel_delivery.status_code)
print("Response Text:", cancel_delivery.text)
print("Reason:", cancel_delivery.reason)