import http.client
import json  # Import json to serialize the payload

conn = http.client.HTTPSConnection("apiconnect.angelone.in")

# Convert dictionary to JSON and encode it to bytes
payload = json.dumps({
    "mode": "FULL",
    "exchangeTokens": {
        "NSE": ["17388"]
    }
}).encode('utf-8')

headers = {
    'X-PrivateKey': 'yFmmdtf1',  # AngelOne API key
    'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6Ikg3NjQ5MyIsInJvbGVzIjowLCJ1c2VydHlwZSI6IlVTRVIiLCJ0b2tlbiI6ImV5SmhiR2NpT2lKU1V6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUoxYzJWeVgzUjVjR1VpT2lKamJHbGxiblFpTENKMGIydGxibDkwZVhCbElqb2lkSEpoWkdWZllXTmpaWE56WDNSdmEyVnVJaXdpWjIxZmFXUWlPallzSW5OdmRYSmpaU0k2SWpNaUxDSmtaWFpwWTJWZmFXUWlPaUppTkdZMk5UWXpZaTA1T0dFMkxUTmtZMlF0T0RZNE5TMWtNamc1WTJaaVkyUTJZamNpTENKcmFXUWlPaUowY21Ga1pWOXJaWGxmZGpJaUxDSnZiVzVsYldGdVlXZGxjbWxrSWpvMkxDSndjbTlrZFdOMGN5STZleUprWlcxaGRDSTZleUp6ZEdGMGRYTWlPaUpoWTNScGRtVWlmU3dpYldZaU9uc2ljM1JoZEhWeklqb2lZV04wYVhabEluMTlMQ0pwYzNNaU9pSjBjbUZrWlY5c2IyZHBibDl6WlhKMmFXTmxJaXdpYzNWaUlqb2lTRGMyTkRreklpd2laWGh3SWpveE56UXdPVEEzTkRFNUxDSnVZbVlpT2pFM05EQTRNakE0TXprc0ltbGhkQ0k2TVRjME1EZ3lNRGd6T1N3aWFuUnBJam9pTURCbFlXSmxOVGt0TWpKa1lpMDBaakJoTFRsa1lXWXRZamt3WVRreU5qTTROMlF5SWl3aVZHOXJaVzRpT2lJaWZRLnRxcjBMU2I2Y0M4V0dLbGJGcEJkOWs0TWJKUkxaS2xsb1VUQS1QQjh0VjdORXhDQ2d6ZWlRQ2NJcjJ0eFBWSmhheDVQOFlDSmJkdXhlVXVHS3loQktFUzVUaUlkdGZDb1phLTBtM0M5dnVQZVZLTkkwYU9rdGpMc1NuOExHckUwV1U1eGF6X0FNRFV5d1pMVTdkVkJvS25hT01DY1VLRXdQQTJBRElrSXlkdyIsIkFQSS1LRVkiOiJ5Rm1tZHRmMSIsImlhdCI6MTc0MDgyMTAxOSwiZXhwIjoxNzQwOTA3NDE5fQ.eGT-hBAH2Vo14_4srDoNhAdkqn1vxSs7oRHUY5WXe0RCYPQEK8mKO9OQFRK_wMVVXv3dkyNukrS2NoRkpcVIoA',  # Use the actual JWT Token here
    'Content-Type': 'application/json'
}


# Fix: Ensure the endpoint starts with "/"
conn.request("POST", "/rest/secure/angelbroking/market/v1/quote/", payload, headers)

# Get response
res = conn.getresponse()
data = res.read()

# Print the response as a decoded string
print(data.decode("utf-8"))
