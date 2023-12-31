# Create simple CLI which is capable of encrypting and decrypting files using the Pretty Good Scheme
# Group Members: James Pope, Aaron, Roche, Bryan Montalvan
# Technologies used: Pycryptodome, argprarse

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from os import urandom
import argparse
import json
import base64


class Message:
    def __init__(self, ciphertext, tag, nonce, sessionKey):
        self.ciphertext = ciphertext
        self.tag = tag
        self.nonce = nonce
        self.sessionKey = sessionKey

    def to_json(self):
        return json.dumps({
            "ciphertext": base64.b64encode(self.ciphertext).decode('utf-8'),
            "tag": base64.b64encode(self.tag).decode('utf-8'),
            "nonce": base64.b64encode(self.nonce).decode('utf-8'),
            "sessionKey": base64.b64encode(self.sessionKey).decode('utf-8')
        })

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)

        return cls(
            base64.b64decode(data["ciphertext"]),
            base64.b64decode(data["tag"]),
            base64.b64decode(data["nonce"]),
            base64.b64decode(data["sessionKey"])
        )


def encrypt(public_key_path, plaintext_file_path, encrypted_file_path):
    # get random 128 bit key
    session_key = urandom(16)

    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    with open(plaintext_file_path, 'rb') as f:
        plaintext = f.read()
    ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext)

    # encrypt with RSA by using the pub key
    recipient_key = RSA.import_key(open(public_key_path, "rb").read())
    rsa_obj = PKCS1_OAEP.new(recipient_key)
    encrypted_key = rsa_obj.encrypt(session_key)

    # Create a Message object
    message = Message(ciphertext, tag, cipher_aes.nonce, encrypted_key)

    # Save the JSON string to the file
    with open(encrypted_file_path, 'wb') as f_enc:
        f_enc.write(str.encode(message.to_json()))

    print("Encryption Successful.")


def decrypt(private_key_path, encrypted_file_path, decrypted_file_path):

    # get the encrypted file contents in a json obj
    with open(encrypted_file_path, 'rb') as f_enc:
        message = Message.from_json(f_enc.read())

    # decrypt the encrypted session key
    private_key = RSA.import_key(open(private_key_path, "rb").read())
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(message.sessionKey)

    # decrypt the ciphertext
    cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce=message.nonce)
    plaintext = cipher_aes.decrypt_and_verify(message.ciphertext, message.tag)

    with open(decrypted_file_path, 'wb') as f_dec:
        f_dec.write(plaintext)

    print("Decryption Successful.")


if __name__ == '__main__':
    # argparse
    parser = argparse.ArgumentParser(
        description="PGP-like file encryption and decryption (task 4).")

    # Use add_mutually_exclusive_group to ensure only one of --encrypt or --decrypt is provided
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--encrypt", action="store_true",
                       help="Encrypt the file.")
    group.add_argument("--decrypt", action="store_true",
                       help="Decrypt the file.")

    parser.add_argument(
        "key_path", help="Path to public key (for encryption) or private key (for decryption).")
    parser.add_argument("input_file", help="Path to input file.")
    parser.add_argument("output_file", help="Path to output file.")

    args = parser.parse_args()

    # Encrypt and Decrypt
    if args.encrypt:
        encrypt(args.key_path, args.input_file, args.output_file)
    elif args.decrypt:
        decrypt(args.key_path, args.input_file, args.output_file)
