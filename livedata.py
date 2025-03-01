import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n     \"exchange\": \"NSE\",\r\n    \"symboltoken\": \"3045\",\r\n     \"interval\": \"ONE_MINUTE\",\r\n  \"fromdate\": \"2021-02-08 09:00\",\r\n     \"todate\": \"2021-02-08 09:16\"\r\n}"
headers = {
  'X-PrivateKey': 'yFmmdtf1',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-UserType': 'USER',
  'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6Ikg3NjQ5MyIsInJvbGVzIjowLCJ1c2VydHlwZSI6IlVTRVIiLCJ0b2tlbiI6ImV5SmhiR2NpT2lKU1V6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUoxYzJWeVgzUjVjR1VpT2lKamJHbGxiblFpTENKMGIydGxibDkwZVhCbElqb2lkSEpoWkdWZllXTmpaWE56WDNSdmEyVnVJaXdpWjIxZmFXUWlPallzSW5OdmRYSmpaU0k2SWpNaUxDSmtaWFpwWTJWZmFXUWlPaUppTkdZMk5UWXpZaTA1T0dFMkxUTmtZMlF0T0RZNE5TMWtNamc1WTJaaVkyUTJZamNpTENKcmFXUWlPaUowY21Ga1pWOXJaWGxmZGpJaUxDSnZiVzVsYldGdVlXZGxjbWxrSWpvMkxDSndjbTlrZFdOMGN5STZleUprWlcxaGRDSTZleUp6ZEdGMGRYTWlPaUpoWTNScGRtVWlmU3dpYldZaU9uc2ljM1JoZEhWeklqb2lZV04wYVhabEluMTlMQ0pwYzNNaU9pSjBjbUZrWlY5c2IyZHBibDl6WlhKMmFXTmxJaXdpYzNWaUlqb2lTRGMyTkRreklpd2laWGh3SWpveE56UXdPVEEzTkRFNUxDSnVZbVlpT2pFM05EQTRNakE0TXprc0ltbGhkQ0k2TVRjME1EZ3lNRGd6T1N3aWFuUnBJam9pTURCbFlXSmxOVGt0TWpKa1lpMDBaakJoTFRsa1lXWXRZamt3WVRreU5qTTROMlF5SWl3aVZHOXJaVzRpT2lJaWZRLnRxcjBMU2I2Y0M4V0dLbGJGcEJkOWs0TWJKUkxaS2xsb1VUQS1QQjh0VjdORXhDQ2d6ZWlRQ2NJcjJ0eFBWSmhheDVQOFlDSmJkdXhlVXVHS3loQktFUzVUaUlkdGZDb1phLTBtM0M5dnVQZVZLTkkwYU9rdGpMc1NuOExHckUwV1U1eGF6X0FNRFV5d1pMVTdkVkJvS25hT01DY1VLRXdQQTJBRElrSXlkdyIsIkFQSS1LRVkiOiJ5Rm1tZHRmMSIsImlhdCI6MTc0MDgyMTAxOSwiZXhwIjoxNzQwOTA3NDE5fQ.eGT-hBAH2Vo14_4srDoNhAdkqn1vxSs7oRHUY5WXe0RCYPQEK8mKO9OQFRK_wMVVXv3dkyNukrS2NoRkpcVIoA',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'Content-Type': 'application/json'
}
conn.request("POST", "/rest/secure/angelbroking/historical/v1/getCandleData", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
