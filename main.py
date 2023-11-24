import time
from receiver import Receiver
from sender import Sender


# TODO posielanie sprav
# TODO error making
# TODO public ip testing


while True:
    msg = input("Receiver of Sender: ")
    if msg == "1":
        user = Sender()
        switch_status = user.request()

        while switch_status is not None:
            if msg == "1":
                user = Receiver(switch_status)
                switch_status = user.listen()
                msg = "2"
            else:
                time.sleep(5)
                user = Sender(switch_status)
                switch_status = user.request()
                msg = "1"

    elif msg == "2":
        user = Receiver()
        switch_status = user.listen()

        while switch_status is not None:
            if msg == "1":
                user = Receiver(switch_status)
                switch_status = user.listen()
                msg = "2"
            else:
                time.sleep(5)
                user = Sender(switch_status)
                switch_status = user.request()
                msg = "1"

    elif msg == "3":
        break
    else:
        print("Wrong input")
