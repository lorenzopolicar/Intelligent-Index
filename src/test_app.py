import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

# Provided log data for testing.
LOG_DATA = [
    {
        "date": "2025-05-01T06:12:34Z",
        "content": (
            "INFO [2025-05-01 06:12:34] [thermostat.controller] Living Room temperature set to 22°C by user 'emma' via mobile app.\n"
            "DEBUG [2025-05-01 06:12:35] [thermostat.sensor] Current temp: 20.6°C. Target: 22°C. Heating ON.\n"
            "INFO [2025-05-01 06:13:01] [event.log] Thermostat reached desired temperature in 2m 18s."
        )
    },
    {
        "date": "2025-05-01T07:45:22Z",
        "content": (
            "WARN [2025-05-01 07:45:22] [security.camera] Motion detected at Front Door.\n"
            "INFO [2025-05-01 07:45:22] [camera.snapshot] Image saved to /storage/security/front_door/2025-05-01_074522.jpg.\n"
            "DEBUG [2025-05-01 07:45:23] [notification.service] Push alert sent to homeowner's device."
        )
    },
    {
        "date": "2025-05-01T08:03:45Z",
        "content": (
            "INFO [2025-05-01 08:03:45] [lighting.automation] Kitchen lights turned OFF via schedule 'weekday_morning_off'.\n"
            "DEBUG [2025-05-01 08:03:45] [lighting.controller] Light state changed: kitchen → OFF. Source: scheduler.\n"
            "INFO [2025-05-01 08:03:46] [energy.monitor] Estimated energy savings today: 0.4 kWh."
        )
    },
    {
        "date": "2025-05-01T09:00:12Z",
        "content": (
            "INFO [2025-05-01 09:00:12] [voice.assistant] Voice command received: 'Start vacuum in hallway'.\n"
            "DEBUG [2025-05-01 09:00:13] [vacuum.bot] Device 'roboVac' started cleaning: zone=hallway, duration=15m.\n"
            "INFO [2025-05-01 09:15:17] [vacuum.bot] Cleaning session complete. Battery level: 72%."
        )
    },
    {
        "date": "2025-05-01T10:35:00Z",
        "content": (
            "ERROR [2025-05-01 10:35:00] [garage.door] Sensor malfunction detected. Status: UNKNOWN.\n"
            "DEBUG [2025-05-01 10:35:01] [diagnostics] Last known state: CLOSED at 09:50:14. Attempting auto-recalibration.\n"
            "INFO [2025-05-01 10:35:10] [support.ticket] Issue logged for technician follow-up. Ticket ID: GH-51234."
        )
    }
]

def test_initial_invocation():
    """
    Sends an initial invocation with the provided log data as the 'data' field
    along with a namespace.
    """
    url = f"{BASE_URL}/invoke"
    payload = {
        "namespace": "log_data",
        "data": LOG_DATA
    }
    print("---- Testing Initial Invocation ----")
    response = requests.post(url, json=payload)
    print("Response:")
    pprint(response.json())
    print("\n")
    return response.json()

def test_human_response(feedback: str = None, approve: str = None):
    """
    Sends a human response payload (resume input) to the `/invoke` endpoint.
    Either feedback or an approve flag should be included (along with namespace).
    """
    url = f"{BASE_URL}/invoke"
    payload = {"namespace": "log_data"}
    if feedback is not None:
        payload["feedback"] = feedback
    if approve is not None:
        payload["approve"] = approve

    print("---- Testing Human Response ----")
    print("Request Payload:")
    pprint(payload)
    response = requests.post(url, json=payload)
    print("Response:")
    pprint(response.json())
    print("\n")
    return response.json()

def test_retrieve_short_term():
    """
    Sends a GET request to the /retrieve-short-term endpoint.
    """
    url = f"{BASE_URL}/retrieve-short-term"
    params = {"namespace": "log_data"}
    print("---- Testing Retrieve Short Term Endpoint ----")
    response = requests.get(url, params=params)
    print("Response:")
    pprint(response.json())
    print("\n")
    return response.json()

def test_retrieve():
    """
    Sends a GET request to the /retrieve endpoint with a sample query.
    """
    # For example, use the term "temperature" to search relevant logs.
    url = f"{BASE_URL}/retrieve"
    params = {"query": "What did emma set the temperature to"}
    print("---- Testing Retrieve Endpoint ----")
    response = requests.get(url, params=params)
    print("Response:")
    pprint(response.json())
    print("\n")
    return response.json()

def main():
    # Invoke the graph initially with log data.
    #test_initial_invocation()
    
    # If the graph is waiting for human input, simulate human responses.
    # First, simulate a response with feedback indicating non-approval.
    #feedback_response = test_human_response(feedback="I don't want recommendations")
    
    # Then simulate a response with approval.
    # approve_response = test_human_response(approve="True")

    # test_retrieve_short_term()
    # test_retrieve()
    pass

if __name__ == "__main__":
    main()
