import streamlit_authenticator as stauth
import pickle
from pathlib import Path

# Nomes e usuários para autenticação
names = ["Michel Daros", "Gustavo Pelissaro", "Alex Sandoval", "Alexsandra Mendes", "Marco Lamim", "Guilherme Grandesi", "Henrique Riego", "Rogerio Ishikawa", "David Andrade", "Fabiana Garcia", "Gabriela Souza", "Andre Hiroshi", "Rafael Pereira", "Gisele Duarte", "Bruna Rufino", "Hellen Vitali", "Rosana Bretzel", "Maria Araujo"]
usernames = ["mdaros", "gpelissaro", "asandoval", "amendes", "mlamim", "ggrandesi", "hriego", "rishikawa", "dandrade", "fgarcia", "gsouza", "ahiroshi", "rpereira", "gduarte", "brufino", "hvitali", "rbretzel", "maraujo"]

# Definir as senhas (não hashadas) que serão usadas
passwords = ["michelpassword", "gustavopassword", "alexpassword", "alexsandrapassword", "marcopassword", "guilherme123", "henrique123", "rogerio123", "david123", "fabiana123", "gabriela123", "andre123", "rafael123", "giselepassword", "brunapassword", "hellenpassword", "rosanapassword","mariapassword"]

# Hashear as senhas usando o bcrypt via streamlit-authenticator
hashed_passwords = stauth.Hasher(passwords).generate()

# Armazenar as senhas hasheadas em um arquivo pickle
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)

print("Senhas hasheadas geradas e armazenadas em 'hashed_pw.pkl'")
