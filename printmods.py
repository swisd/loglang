import colorama
from colorama import Fore


def fprint(text: object, aux: object, col: object, bck: object = '') -> None:
    """Print using color
    :param bck:
    :param text
    :param aux
    :param col"""
    print((f'{col}{bck}[{aux}] {text}{Fore.WHITE}' if aux != '' else f"{col}{text}{Fore.WHITE}"))


def fprint_s(text, aux, stat) -> None:
    """Print using status"""
    if 100 <= stat <= 299:
        color = Fore.GREEN
    elif 300 <= stat <= 399:
        color = Fore.YELLOW
    elif 400 <= stat <= 599:
        color = Fore.RED

    print((f'{color}[{aux}] {text}{Fore.WHITE}' if aux != '' else f"{color}{text}{Fore.WHITE}"))


Back = colorama.Back
