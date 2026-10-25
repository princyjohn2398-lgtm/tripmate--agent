"""Command-line entry point for TripMate."""
import logging
from agent import run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

def main():
    print("TripMate Travel Assistant (type 'exit' to quit)")
    print("Note: the weather dataset is mock data, not a live forecast.")
    while True:
        try:
            query = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if query.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        result = run_agent(query)
        print(f"\nTripMate: {result['answer']}")
        if result["trace"]:
            print("\n--- Visible tool trace ---")
            for item in result["trace"]:
                print(f"Tool: {item['tool']}")
                print(f"Arguments: {item['arguments']}")
                print(f"Result: {item['result']}")
            print("--------------------------")

if __name__ == "__main__":
    main()
