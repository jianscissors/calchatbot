import os
import requests

CAL_API_BASE = "https://api.cal.com/v2"
CAL_API_KEY = os.getenv("CAL_API_KEY")
headers = {
    "cal-api-version": "2024-08-13",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {CAL_API_KEY}"
}

def book_event(args):
    eventTypeId = args.get("eventTypeId")
    start = args.get("start")
    attendee_name = args.get("name")
    attendee_email = args.get("email")

    payload = {
        "start": start,
        "attendee": {
            "name": attendee_name,
            "email": attendee_email,
            "timeZone": "America/Los_Angeles",
            "phoneNumber": "2132455256",
            "language": "en"
        },
        "bookingFieldsResponses": { "customField": "customValue" },
        "eventTypeId": int(eventTypeId),
        "eventTypeSlug": "my-event-type",
        "username": "zhang-jian-scissors",
        "teamSlug": "zhang-jian-scissors",
        "organizationSlug": "acme-corp",
        "guests": ["guest1@example.com", "guest2@example.com"],
        "meetingUrl": "https://example.com/meeting",
        "location": {
            "type": "integration",
            "integration": "cal-video"
        },
        "metadata": { "key": "value" },
        "routing": {
            "responseId": 123,
            "teamMemberIds": [101, 102]
        },
        "emailVerificationCode": "123456"
    }
    res = requests.post(f"{CAL_API_BASE}/bookings", headers=headers, json=payload)
    res_json = res.json()
    print("Calling Cal.com API with payload:", payload)
    print("Cal.com API response: %s", res.text)
    print("Cal.com API status code:", res.status_code)
    if res.status_code == 201:
        return "Meeting booked successfully!"
    return f"Failed to book meeting: {res.text}"

def list_bookings(args):
    email = args["email"]
    querystring = {"attendeeEmail": email}

    res = requests.get(f"{CAL_API_BASE}/bookings", headers=headers, params=querystring)
    print("Calling Cal.com API with querystring:", querystring)
    print("Cal.com API response: %s", res.text)
    print("Cal.com API status code:", res.status_code)

    if res.status_code == 200:

        data = res.json()
        return data
        
        bookings = data.get("data", [])
        print("bookings:", bookings)
        if not bookings:
            return "No bookings found."

        # 生成一个简单的摘要文本
        return "\n".join([
            f"📅 {b['title']} with {b['hosts'][0]['name']} at {b['start']}"
            for b in bookings
        ])

    return f"❌ Failed to list bookings: {res.status_code} - {res.text}"

