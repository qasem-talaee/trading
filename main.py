from pynput import keyboard
from libs import coin


def onPress(key):
    if str(key) == "'`'":
        chz.set_safe_stop(True)
        hot.set_safe_stop(True)
        print('-----SAFE STOP IS ON ROLL-----')


listener = keyboard.Listener(on_press=onPress, )

chz = coin.Coin('chz', 5, 0.00001, 0.00005, 0.0002)
hot = coin.Coin('hot', 5, 0.00001, 0.00005, 0.0002)

chz.start()
hot.start()
listener.start()

chz.join()
hot.join()
listener.join()