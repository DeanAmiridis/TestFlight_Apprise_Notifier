from colorama import Fore, Style, init

# Initialize colorama for Windows compatibility
init(autoreset=True)

def print_green(message: str):
    """Print message in green color."""
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_cyan(message: str):
    """Print message in cyan color."""
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")