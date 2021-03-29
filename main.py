from pynput import keyboard
from libs import coin


def onPress(key):
    if str(key) == "'`'":
        coin1.set_safe_stop(True)
        coin2.set_safe_stop(True)
        print('-----SAFE STOP IS ON ROLL-----')


listener = keyboard.Listener(on_press=onPress, )
#0.0003
coin1 = coin.Coin('zil', 5, 0.0001, 0.0001, 0.5)
coin2 = coin.Coin('bat', 5, 0.0002, 0.0007, 0.5)

coin1.start()
coin2.start()
listener.start()

coin1.join()
coin2.join()
listener.join()