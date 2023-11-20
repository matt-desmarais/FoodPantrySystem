import datetime as dt
import os

# Get the current date and time
now = dt.datetime.now()
print(now)

todayfile = "/home/pi/files/" + str(now.strftime("%Y-%m-%d")) + ".txt"
todayfruit = "/home/pi/files/" + str(now.strftime("%Y-%m-%d")) + "fruit.txt"

# Check if the files exist before attempting to delete them
if os.path.exists(todayfile):
    os.remove(todayfile)
    print(f"Deleted {todayfile}")
else:
    print(f"{todayfile} does not exist.")

if os.path.exists(todayfruit):
    os.remove(todayfruit)
    print(f"Deleted {todayfruit}")
else:
    print(f"{todayfruit} does not exist.")
