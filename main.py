import time
from receiver import Receiver
from sender import Sender

# TODO stracanie bajtov
# TODO public ip testing

while True:
    msg = input("Client (1) Server (2) End of program (3): ")
    if msg == "3":
        break

    if msg == "1":
        user = Sender()
    elif msg == "2":
        user = Receiver()
    else:
        print("Wrong input")
        continue

    switch_status = user.request() if msg == "1" else user.listen()

    while switch_status is not None:
        if msg == "1":
            user = Receiver(switch_status)
        else:
            time.sleep(5)
            user = Sender(switch_status)

        switch_status = user.listen() if msg == "1" else user.request()
        msg = "2" if msg == "1" else "1"
