
class Chip:
    def __init__(self, name = "",
        path = "", description = "",
        price = "", location = "", rarity = ""):
        self.name = name
        self.path = path
        self.description = description
        self.price = price
        self.location = location
        self.rarity = rarity

chips = {}

def get_all_chips_obj(chips_dir):
    for chip_name in chips_dir:
        chip = Chip(
            chip_name,
            chips_dir[chip_name]["path"],
            chips_dir[chip_name]["description"],
            chips_dir[chip_name]["price"],
            chips_dir[chip_name]["location"],
            chips_dir[chip_name]["rarity"]
        )
        chips[chip_name] = chip


        