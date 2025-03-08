import http.client
import mimetypes
conn = http.client.HTTPSConnection(
    "apiconnect.angelone.in"
    )
payload = "{\n \"exchange\": \"NSE\",\n    \"tradingsymbol\": \"SBIN-EQ\",\n \"symboltoken\": \"3045\",\n   \"quantity\": 5,\n    \"disclosedquantity\": 3,\n    \"transactiontype\": \"BUY\",\n    \"ordertype\": \"MARKET\",\n    \"variety\": \"STOPLOSS\",\n    \"producttype\": \"INTRADAY\"\n}"
headers = {
  'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6Ikg3NjQ5MyIsInJvbGVzIjowLCJ1c2VydHlwZSI6IlVTRVIiLCJ0b2tlbiI6ImV5SmhiR2NpT2lKU1V6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUoxYzJWeVgzUjVjR1VpT2lKamJHbGxiblFpTENKMGIydGxibDkwZVhCbElqb2lkSEpoWkdWZllXTmpaWE56WDNSdmEyVnVJaXdpWjIxZmFXUWlPallzSW5OdmRYSmpaU0k2SWpNaUxDSmtaWFpwWTJWZmFXUWlPaUppTkdZMk5UWXpZaTA1T0dFMkxUTmtZMlF0T0RZNE5TMWtNamc1WTJaaVkyUTJZamNpTENKcmFXUWlPaUowY21Ga1pWOXJaWGxmZGpJaUxDSnZiVzVsYldGdVlXZGxjbWxrSWpvMkxDSndjbTlrZFdOMGN5STZleUprWlcxaGRDSTZleUp6ZEdGMGRYTWlPaUpoWTNScGRtVWlmU3dpYldZaU9uc2ljM1JoZEhWeklqb2lZV04wYVhabEluMTlMQ0pwYzNNaU9pSjBjbUZrWlY5c2IyZHBibDl6WlhKMmFXTmxJaXdpYzNWaUlqb2lTRGMyTkRreklpd2laWGh3SWpveE56UXdPVEEzTkRFNUxDSnVZbVlpT2pFM05EQTRNakE0TXprc0ltbGhkQ0k2TVRjME1EZ3lNRGd6T1N3aWFuUnBJam9pTURCbFlXSmxOVGt0TWpKa1lpMDBaakJoTFRsa1lXWXRZamt3WVRreU5qTTROMlF5SWl3aVZHOXJaVzRpT2lJaWZRLnRxcjBMU2I2Y0M4V0dLbGJGcEJkOWs0TWJKUkxaS2xsb1VUQS1QQjh0VjdORXhDQ2d6ZWlRQ2NJcjJ0eFBWSmhheDVQOFlDSmJkdXhlVXVHS3loQktFUzVUaUlkdGZDb1phLTBtM0M5dnVQZVZLTkkwYU9rdGpMc1NuOExHckUwV1U1eGF6X0FNRFV5d1pMVTdkVkJvS25hT01DY1VLRXdQQTJBRElrSXlkdyIsIkFQSS1LRVkiOiJ5Rm1tZHRmMSIsImlhdCI6MTc0MDgyMTAxOSwiZXhwIjoxNzQwOTA3NDE5fQ.eGT-hBAH2Vo14_4srDoNhAdkqn1vxSs7oRHUY5WXe0RCYPQEK8mKO9OQFRK_wMVVXv3dkyNukrS2NoRkpcVIoA',
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-UserType': 'USER',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-PrivateKey': 'yFmmdtf1'
}
conn.request("POST", "/rest/secure/angelbroking/order/v1/placeOrder", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))