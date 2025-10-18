from modules.encryptor import HybridEncryptor

encryptor = HybridEncryptor()

# Encrypt data
text = "Sensitive patient record: John Doe, Diagnosis - Hypertension"
encrypted_bundle = encryptor.encrypt(text)
print("🔒 Encrypted data:\n", encrypted_bundle)

# Decrypt data
decrypted_text = encryptor.decrypt(encrypted_bundle)
print("\n🔓 Decrypted data:\n", decrypted_text)