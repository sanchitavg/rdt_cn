**Reliable UDP File Transfer**

A Python project that implements a reliable file transfer system over UDP, with features like resume support, integrity checking, and efficient data transmission.

**Overview**

UDP is fast but unreliable (no guarantee of delivery or order). This project builds a custom reliability layer to ensure correct and complete file transfer.

**Features**

Chunk-Based Transfer – File split into 1024-byte chunks 
Resume Support – Continues from last received chunk using progress.txt 
Integrity Check – SHA-256 hash verifies file correctness 
Efficient Transfer – Selective Repeat with sliding window 

RELIABLEUDP/ client.py server.py file.txt received_file.txt progress.txt

**How to Run**

python3 server.py python3 client.py

**Concepts Used**

Reliable Data Transfer
Selective Repeat ARQ
Sliding Window Protocol
UDP Socket Programming

**Tech Stack**

Python &
Socket Programming
