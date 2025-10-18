from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os, base64, json

class HybridEncryptor:
    def __init__(self):
        # Generate RSA key pair (used for encrypting AES key)
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()

    def encrypt(self, plaintext: str):
        # Generate a random AES key
        aes_key = os.urandom(32)  # 256-bit key
        iv = os.urandom(16)       # Initialization vector

        # Encrypt the plaintext using AES
        cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(plaintext.encode()) + encryptor.finalize()

        # Encrypt the AES key using RSA public key
        encrypted_key = self.public_key.encrypt(
            aes_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

        # Return encrypted bundle (AES key + data)
        bundle = {
            "encrypted_key": base64.b64encode(encrypted_key).decode(),
            "iv": base64.b64encode(iv).decode(),
            "data": base64.b64encode(encrypted_data).decode(),
        }
        return json.dumps(bundle)

    def decrypt(self, encrypted_bundle: str):
        bundle = json.loads(encrypted_bundle)
        encrypted_key = base64.b64decode(bundle["encrypted_key"])
        iv = base64.b64decode(bundle["iv"])
        encrypted_data = base64.b64decode(bundle["data"])

        # Decrypt AES key using RSA private key
        aes_key = self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

        # Decrypt data using AES
        cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        return decrypted_data.decode()
