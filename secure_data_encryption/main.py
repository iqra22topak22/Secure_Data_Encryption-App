
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import os
from cryptography.fernet import Fernet

KEY_FILE = "simple_secret.key"

# Load or generate encryption key
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key

cipher = Fernet(load_key())

# Initialize the database
def init_db():
    conn = sqlite3.connect("simple_data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS VAULT (
            label TEXT PRIMARY KEY,
            encrypted_text TEXT,
            passkey TEXT
        )
    """)
    conn.commit()
    conn.close()

# Hash the passkey
def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

# Encrypt a message
def encrypt(text):
    return cipher.encrypt(text.encode()).decode()

# Decrypt a message
def decrypt(encrypted_text):
    return cipher.decrypt(encrypted_text.encode()).decode()

# Initialize the DB
init_db()

# Streamlit UI
st.title("🔐 Secure Data Encryption App")
menu = ["Store Secret", "Retrieve Secret"]
choice = st.sidebar.selectbox("Choose Option", menu)

if choice == "Store Secret":
    st.header("Store a New Secret")

    label = st.text_input("Label (Unique ID):")
    secret = st.text_area("Your Secret")
    passkey = st.text_input("Passkey (to protect it):", type="password")

    if st.button("Encrypt and Save"):
        if label and secret and passkey:
            conn = sqlite3.connect("simple_data.db")
            c = conn.cursor()

            encrypted = encrypt(secret)
            hashed_key = hash_passkey(passkey)

            try:
                c.execute("INSERT INTO VAULT(label, encrypted_text, passkey) VALUES (?, ?, ?)", 
                          (label, encrypted, hashed_key))
                conn.commit()
                st.success("✅ Secret Stored Successfully")
            except sqlite3.IntegrityError:
                st.error("❌ Label already exists. Choose a different label.")
            conn.close()
        else:
            st.warning("⚠️ Please fill all fields")

elif choice == "Retrieve Secret":
    st.header("Retrieve Your Secret")

    label = st.text_input("Label:")
    passkey = st.text_input("Enter Passkey:", type="password")

    if st.button("Decrypt"):
        conn = sqlite3.connect("simple_data.db")
        c = conn.cursor()
        c.execute("SELECT encrypted_text, passkey FROM VAULT WHERE label = ?", (label,))
        result = c.fetchone()
        conn.close()

        if result:
            encrypted_text, stored_hash = result
            if hash_passkey(passkey) == stored_hash:
                decrypted = decrypt(encrypted_text)
                st.success("🔓 Here is your Secret")
                st.code(decrypted)
            else:
                st.error("❌ Incorrect Passkey")
        else:
            st.warning("⚠️ No such label found")


                