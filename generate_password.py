import streamlit_authenticator as stauth
import pickle
from pathlib import Path

# Nomes e usuários para autenticação
names = ["Peter Parker", "Rebecca Miller", "Michel Daros", "Gustavo Pelissaro", "Alex Sandoval", "Alexsandra Mendes", "Marco Lamim"]
usernames = ["pparker", "rmiller", "mdaros", "gpelissaro", "asandoval", "amendes", "mlamim"]

# Definir as senhas (não hashadas) que serão usadas
passwords = ["abc123", "def456", "michelpassword", "gustavopassword", "alexpassword", "alexsandrapassword", "marcopassword"]

# Hashear as senhas usando o bcrypt via streamlit-authenticator
hashed_passwords = stauth.Hasher(passwords).generate()

# Armazenar as senhas hasheadas em um arquivo pickle
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)

print("Senhas hasheadas geradas e armazenadas em 'hashed_pw.pkl'")
