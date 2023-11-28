import time
from receiver import Receiver
from sender import Sender

while True:
    msg = input("Client (1) Server (2) End of program (3): ")
    if msg == "3":
        break

    if msg == "1":                      # If input is '1', initiate as a Sender
        user = Sender()
    elif msg == "2":                    # If input is '2', initiate as a Receiver
        user = Receiver()
    else:
        print("Wrong input")
        continue

    switch_status = user.request() if msg == "1" else user.listen()     # Perform initial action based on user input

    while switch_status is not None:
        if msg == "1":                                                  # If previous input was Sender
            user = Receiver(switch_status)                              # Create a Receiver object with the received status
        else:
            time.sleep(5)                                               # If previous input was Receiver
            user = Sender(switch_status)                                # Create a Sender object with the received status

        switch_status = user.listen() if msg == "1" else user.request()     # Update the switch_status based on the action taken by the user
        msg = "2" if msg == "1" else "1"                                    # Switch the message between Client and Server

# 169.254.95.251