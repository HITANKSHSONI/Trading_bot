import http.client

conn = http.client.HTTPSConnection("apiconnect.angelone.in")
payload = "{\r\n     \"exchange\": \"NSE\",\r\n    \"symboltoken\": \"3045\",\r\n     \"interval\": \"ONE_MINUTE\",\r\n  \"fromdate\": \"2021-02-08 09:00\",\r\n     \"todate\": \"2021-02-08 09:16\"\r\n}"
headers = {
  'X-PrivateKey': '7Ee2qnqp',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
  'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
  'X-MACAddress': 'MAC_ADDRESS',
  'X-UserType': 'USER',
  'Authorization': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJ1c2VybmFtZSI6Ikg3NjQ5MyIsInJvbGVzIjowLCJ1c2VydHlwZSI6IlVTRVIiLCJ0b2tlbiI6ImV5SmhiR2NpT2lKU1V6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUoxYzJWeVgzUjVjR1VpT2lKamJHbGxiblFpTENKMGIydGxibDkwZVhCbElqb2lkSEpoWkdWZllXTmpaWE56WDNSdmEyVnVJaXdpWjIxZmFXUWlPallzSW5OdmRYSmpaU0k2SWpNaUxDSmtaWFpwWTJWZmFXUWlPaUpsWVdZMVpqZGpZUzB4T0daa0xUTTJORGt0WVRkbE15MDRPRFpoWVRoa1pUTXpOVGtpTENKcmFXUWlPaUowY21Ga1pWOXJaWGxmZGpJaUxDSnZiVzVsYldGdVlXZGxjbWxrSWpvMkxDSndjbTlrZFdOMGN5STZleUprWlcxaGRDSTZleUp6ZEdGMGRYTWlPaUpoWTNScGRtVWlmU3dpYldZaU9uc2ljM1JoZEhWeklqb2lZV04wYVhabEluMTlMQ0pwYzNNaU9pSjBjbUZrWlY5c2IyZHBibDl6WlhKMmFXTmxJaXdpYzNWaUlqb2lTRGMyTkRreklpd2laWGh3SWpveE56UXlPVEl3TlRZeUxDSnVZbVlpT2pFM05ESTRNek01T0RJc0ltbGhkQ0k2TVRjME1qZ3pNems0TWl3aWFuUnBJam9pTWpNM05UY3pNbUV0TnpKaVpTMDBNalF3TFdFM09XSXRaakpoT0dOak5qSmlOelkzSWl3aVZHOXJaVzRpT2lJaWZRLmNZVWxjbFRrTm9NRm43UGFnTlNMckpadTN0SDN4cHBRSjBCcjh3c0JZNjRGUFBIVmNHdUVyRGhoSGxGN3lPYWkwdGhKRVpiMXptWnp1c1F6OXp3ZkoyRVRCRTR6M3ZoX24tV2lsdFN1MGxoYmRlME9kNzBjWk95YkJsYk9pMVFjNjh3aVM4Sl85YUZTOWZsRVJpNmhvSjAzT21WMktCNllPRGhiZzJGQl9hdyIsIkFQSS1LRVkiOiI3RWUycW5xcCIsImlhdCI6MTc0MjgzNDE2MiwiZXhwIjoxNzQyOTIwNTYyfQ.SVKypuoizgHRlVRkU2HlaiN8pzXWRybuB3bEDFc-hnJ8o36QZt5A16o63HPymYN3Y4FoyNbsDuoffkkr9Z62pg',
  'Accept': 'application/json',
  'X-SourceID': 'WEB',
  'Content-Type': 'application/json'
}
conn.request("POST", "/rest/secure/angelbroking/historical/v1/getCandleData", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
