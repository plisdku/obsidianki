import pathlib


def load_emoji():
    empath = pathlib.Path(__file__).parent / "good_mac_emoji.txt"
    with open(empath) as fh:
        ee = fh.read().splitlines()
    return ee


EMOJI = load_emoji()
