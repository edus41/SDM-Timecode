BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
RESET = "\033[0m"

def log(*messages, color=WHITE):
    if messages and messages[-1] in (BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE):
        color = messages[-1]
        messages = messages[:-1]
    print(color + " ".join(str(message) for message in messages) + RESET)
