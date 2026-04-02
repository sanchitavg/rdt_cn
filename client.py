import socket
import hashlib
import json
import os
import time

SERVER_IP = "127.0.0.1"
PORT = 5005
CHUNK_SIZE = 1024
WINDOW_SIZE = 8
TIMEOUT = 0.5

file_path = "test.txt"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(TIMEOUT)

def get_file_hash(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()

# Prepare file chunks
file_size = os.path.getsize(file_path)
total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
file_hash = get_file_hash(file_path)

chunks = []
for i in range(total_chunks):
    with open(file_path, "rb") as f:
        f.seek(i * CHUNK_SIZE)
        data = f.read(CHUNK_SIZE)
        h = hashlib.sha256(data).hexdigest()
        chunks.append((data, h))

# Send INIT
sock.sendto(json.dumps({
    "type": "INIT",
    "filename": os.path.basename(file_path),
    "total_chunks": total_chunks,
    "file_hash": file_hash
}).encode(), (SERVER_IP, PORT))

# Receive RESUME info
data, _ = sock.recvfrom(65536)
resume_msg = json.loads(data.decode())

start_chunk = resume_msg.get("start_chunk", 0)

print(f"Resuming from chunk {start_chunk}")

# Sliding window variables
base = start_chunk
next_seq = start_chunk
acks_received = set(range(start_chunk))   # ✅ mark old chunks as already ACKed
start_time = time.time()                 # ✅ fix

def print_window():
    window_display = ""
    for i in range(base, min(base + WINDOW_SIZE, total_chunks)):
        if i in acks_received:
            window_display += f"[{i}:ACK] "
        else:
            window_display += f"[{i}:SENT] "
    print("Sliding Window:", window_display)

while base < total_chunks:
    # Send packets in window
    while next_seq < base + WINDOW_SIZE and next_seq < total_chunks:
        chunk, chunk_hash = chunks[next_seq]
        sock.sendto(json.dumps({
            "type": "DATA",
            "seq": next_seq,
            "data": chunk.hex(),
            "hash": chunk_hash
        }).encode(), (SERVER_IP, PORT))
        next_seq += 1

    print_window()

    try:
        while True:
            ack_data, _ = sock.recvfrom(65536)
            ack_msg = json.loads(ack_data.decode())
            seq = ack_msg.get("seq")

            if seq not in acks_received:
                acks_received.add(seq)
                print(f"ACK received for chunk {seq}")

    except socket.timeout:
        # Resend only missing packets
        for i in range(base, min(base + WINDOW_SIZE, next_seq)):
            if i not in acks_received:
                chunk, chunk_hash = chunks[i]
                sock.sendto(json.dumps({
                    "type": "DATA",
                    "seq": i,
                    "data": chunk.hex(),
                    "hash": chunk_hash
                }).encode(), (SERVER_IP, PORT))

    # Slide window
    while base in acks_received:
        base += 1

# Send END
sock.sendto(json.dumps({"type": "END"}).encode(), (SERVER_IP, PORT))

end_time = time.time()
duration = end_time - start_time
throughput = (file_size / duration) / 1024

print("File transfer complete")
print(f"Time taken: {duration:.2f}s, Throughput: {throughput:.2f} KB/s")

sock.close()