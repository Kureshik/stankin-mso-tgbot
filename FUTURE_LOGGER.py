import logging

logging.basicConfig(
    filename="test.txt",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

while True:
    data = input("Enter something: ")
    if data == "exit":
        break
    logging.info(data)
