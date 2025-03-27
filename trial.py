import datetime

now = datetime.datetime.now()
print(now.weekday())
today = now.date()
from_date = today.strftime("%Y-%m-%d") + " 09:15"
to_date = now.strftime("%Y-%m-%d %H:%M")