from libs import coin

chz = coin.Coin('chz', 4)
hot = coin.Coin('hot', 3)

chz.start()
hot.start()

chz.join()
hot.join()