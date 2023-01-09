import RPi.GPIO as gp
import time


class Button:
    def __init__(self, button_list, verbose=False):
        """array of [(pin, name),..]"""
        self.verbose = verbose
        self.button_list = button_list
        self.button_pins = [button[0] for button in button_list]
        gp.setmode(gp.BCM)
        gp.setup(self.button_pins, gp.IN, pull_up_down=gp.PUD_UP)
        for button in self.button_list:
            gp.add_event_detect(
                button[0], gp.FALLING, callback=self.button_pressed, bouncetime=250
            )

    def button_pressed(self, pin):
        for button in self.button_list:
            if pin == button[0]:
                if self.verbose is True:
                    print(f"{button[1]} at pin {button[0]} pressed!")
                button[2]()

    def cleanup(self):
        for button in self.button_list:
            gp.remove_event_detect(button[0])


if __name__ == "__main__":

    def button_blue():
        print("The blue func")

    def button_black():
        print("The black func")

    bt = Button([(27, "blue", button_blue), (22, "black", button_black)], True)

    while True:
        time.sleep(0.1)
