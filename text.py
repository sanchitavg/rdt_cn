with open("test.txt", "w") as f:
    for i in range(500):
        f.write(f"This is line {i}\n")

print("test.txt created")