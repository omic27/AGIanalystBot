from .utils import parse_packages

def get_wallet_for_network(settings, network: str) -> str:
    if network == "USDT_TON":
        return settings.WALLET_USDT_TON
    if network == "USDT_TRON":
        return settings.WALLET_USDT_TRON
    if network == "TON":
        return settings.WALLET_TON
    return ""

def get_packages(settings) -> list[tuple[int,int]]:
    return parse_packages(settings.PACKAGES_USD)

def is_ton(network: str) -> bool:
    return network == "TON"
