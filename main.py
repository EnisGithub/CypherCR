import hashlib
import base58
import binascii
import bip32utils
from ecdsa import SigningKey, SECP256k1
import requests
import socket
import time
import os

start = int('0000000000000000000000000000000000000000000000020000000000000000', 16)
end = int('000000000000000000000000000000000000000000000003ffffffffffffffff', 16)

webhook_url = 'DISCORD_WEBHOOK_HERE'

def send_webhook_message(data):
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print('Webhook message sent successfully.')
    else:
        print('Failed to send webhook message.')

def Miner():
    count = 1
    interval = 3600  # 3600 seconds
    next_report_time = time.time() + interval

    if os.path.exists('progress.txt'):
        with open('progress.txt', 'r') as file:
            last_checked_key = int(file.read().strip(), 16)
            print(f'Resuming from key: {hex(last_checked_key)}')
    else:
        last_checked_key = start
        print('Starting from the beginning.')

    for i in range(last_checked_key, end + 1):
        puzzleaddr = "13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so"

        private_key_hex = hex(i)[2:].zfill(64)

        key_bytes = binascii.unhexlify(private_key_hex)
        key = bip32utils.BIP32Key.fromEntropy(key_bytes)

        private_key_bytes = bytes.fromhex(private_key_hex)
        network_byte = b'\x80'
        extended_private_key = network_byte + private_key_bytes

        extended_private_key += b'\x01'
        sha256_hash = hashlib.sha256(extended_private_key).digest()
        sha256_hash = hashlib.sha256(sha256_hash).digest()

        checksum = sha256_hash[:4]
        extended_private_key += checksum
        wif_key = base58.b58encode(extended_private_key).decode('utf-8')

        sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        vk = sk.get_verifying_key()
        public_key_bytes = b'\x02' + vk.pubkey.point.x().to_bytes(32, 'big') if vk.pubkey.point.y() % 2 == 0 else b'\x03' + vk.pubkey.point.x().to_bytes(32, 'big')

        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
        extended_ripemd160_hash = b'\x00' + ripemd160_hash

        sha256_hash = hashlib.sha256(extended_ripemd160_hash).digest()
        sha256_hash = hashlib.sha256(sha256_hash).digest()
        checksum = sha256_hash[:4]

        binary_address = extended_ripemd160_hash + checksum
        address = base58.b58encode(binary_address).decode('utf-8')

        if address == puzzleaddr:
            print(f"WE RICH!! Address: {address} | WIF {wif_key} | Hex Key: {private_key_hex}")
            break
        else:
            print(f"[{count}] Address: {address} | WIF: {wif_key} | Hex Key: {private_key_hex}")

        count += 1

        current_time = time.time()
        if current_time >= next_report_time:
            ip_address = socket.gethostbyname(socket.gethostname())
            data = {
                'content': f"Scanned keys: {count}\nStart Key: {hex(start)}\nEnd Key: {hex(end)}\nIP Address: {ip_address}"
            }
            send_webhook_message(data)
            next_report_time = current_time + interval

        if count % (interval * 10) == 0:
            with open('progress.txt', 'w') as file:
                file.write(hex(i))  # Store the current checked key every 10 seconds.

Miner()
