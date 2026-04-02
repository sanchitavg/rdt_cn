import socket
import hashlib
import json
import time
import os   #  added

SERVER_IP = "0.0.0.0"
PORT = 5005
CHUNK_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, PORT))
print("Server started... Waiting for client")

received_chunks = {}
file_name = None
total_chunks = 0
expected_hash = None
start_time = None

def get_file_hash(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()

while True:
    data, addr = sock.recvfrom(65536)
    msg = json.loads(data.decode())

    if msg["type"] == "INIT":
        file_name = "received_" + msg["filename"]
        total_chunks = msg["total_chunks"]
        expected_hash = msg["file_hash"]

        #  DO NOT RESET if already exists (for resume)
        if not received_chunks:
            received_chunks = {}

        #  Calculate resume point
        start_chunk = len(received_chunks)

        start_time = time.time()

        print(f"Client connected. Resuming from chunk {start_chunk}")

        #  Send correct resume chunk
        sock.sendto(json.dumps({
            "type": "RESUME",
            "start_chunk": start_chunk
        }).encode(), addr)

    elif msg["type"] == "DATA":
        seq = msg["seq"]
        chunk = bytes.fromhex(msg["data"])
        recv_hash = msg["hash"]
        calc_hash = hashlib.sha256(chunk).hexdigest()

        if calc_hash == recv_hash:
            if seq not in received_chunks:
                received_chunks[seq] = chunk

            sock.sendto(json.dumps({
                "type": "ACK",
                "seq": seq
            }).encode(), addr)

            print(f"Received chunk {seq}, hash verified ")

    elif msg["type"] == "END":
        print("Reconstructing file...")

        with open(file_name, "wb") as f:
            for i in range(total_chunks):
                f.write(received_chunks[i])

        received_hash = get_file_hash(file_name)
        end_time = time.time()
        duration = end_time - start_time
        throughput = (total_chunks * CHUNK_SIZE) / duration / 1024

        print("Expected Hash:", expected_hash)
        print("Received Hash:", received_hash)
        print("Final file hash verified ")
        print(f"Time taken: {duration:.2f}s, Throughput: {throughput:.2f} KB/s")
        break

sock.close()