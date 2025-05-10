import importlib.resources


def load_emoji():
    # Use importlib.resources to load the resource from the package
    with importlib.resources.open_text("obsidianki", "good_mac_emoji.txt") as file:
        ee = file.read().splitlines()
    return ee


EMOJI = load_emoji()
