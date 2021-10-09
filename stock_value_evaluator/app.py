import sys

from evaluate import evaluate
import matplotlib.pyplot as plt

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Please enter a ticker")
        sys.exit()
    ticket = sys.argv[1]
    evaluate(ticket)
    plt.show()
