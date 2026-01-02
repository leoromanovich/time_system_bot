"""Entrypoint to launch the Telegram bot."""
from time_bot.bot.main import main as bot_main


def main() -> None:
    bot_main()


if __name__ == "__main__":
    main()
