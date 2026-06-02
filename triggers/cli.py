"""Interactive CLI trigger — uv run jarvis"""
import os
from dotenv import load_dotenv

load_dotenv()

from agent.loop import run
import memory.store as store


def main():
    print("Jarvis CLI — digita 'exit' per uscire, 'clear' per resettare la storia\n")
    while True:
        try:
            user = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCiao!")
            break

        if not user:
            continue
        if user.lower() == "exit":
            break
        if user.lower() == "clear":
            store.clear_history()
            print("Storia resettata.\n")
            continue

        reply = run(user)
        store.append_message("user", user)
        store.append_message("assistant", reply)
        print(f"\nJarvis: {reply}\n")
