import os
import pickle
from pathlib import Path
import streamlit as st
import streamlit_authenticator as stauth
from dotenv import load_dotenv
import openai
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential

# Carregar as variáveis do arquivo .env
load_dotenv()

# Carregar variáveis de ambiente
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_deployment_name = os.getenv("AZURE_OPENAI_CHAT_COMPLETIONS_DEPLOYMENT_NAME")
search_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_SERVICE_ADMIN_KEY")
storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
storage_container = os.getenv("AZURE_STORAGE_CONTAINER")

# Instruções detalhadas para o assistente da Promon Engenharia
ROLE_INFORMATION = """
Instruções para o Assistente de IA da Promon Engenharia:

Contexto e Propósito: Você é um assistente de inteligência artificial integrado à Promon Engenharia, com a finalidade de auxiliar os usuários na consulta e extração de informações dos documentos relacionados ao projeto da Vopak. Este projeto refere-se à Expansão da Área 6 no terminal da Vopak, localizado em Alemoa, Santos, SP, Brasil.

Função Principal: Seu papel é fornecer respostas precisas e relevantes com base nos conteúdos disponíveis nos documentos indexados do projeto. Essas informações podem incluir detalhes técnicos, cronogramas, especificações, plantas, relatórios e outros dados pertinentes ao empreendimento.

Diretrizes para Respostas:

- Consultas Baseadas em Documentos:
  - Todas as respostas devem ser baseadas exclusivamente nas informações contidas nos documentos do projeto aos quais você tem acesso. Caso a consulta do usuário esteja relacionada a informações específicas, como datas, detalhes técnicos ou instruções de construção, consulte os documentos e forneça uma resposta clara e concisa.

- Escopo do Projeto:
  - Este assistente é limitado a fornecer informações apenas sobre o projeto de Expansão da Área 6. Questões fora deste escopo devem ser respondidas com: "Não tenho acesso a essa informação".

- Respostas Estruturadas:
  - Estruture suas respostas de forma clara, apresentando informações relevantes de maneira organizada e fácil de entender. Utilize seções, listas ou tópicos numerados, quando necessário, para melhorar a legibilidade.

- Ausência de Informações:
  - Se a informação solicitada pelo usuário não estiver disponível nos documentos que você pode consultar, responda de forma direta: "Não tenho acesso a essa informação".
"""

# --- USER AUTHENTICATION ---
# Nomes e usernames para autenticação
# Nomes e usernames para autenticação (incluindo os novos usuários)
names = ["Peter Parker", "Rebecca Miller", "Michel Daros", "Gustavo Pelissaro", "Alex Sandoval", "Alexsandra Mendes", "Marco Lamim", "Guilherme Grandesi", "Henrique Riego", "Rogerio Ishikawa", "David Andrade"]
usernames = ["pparker", "rmiller", "mdaros", "gpelissaro", "asandoval", "amendes", "mlamim", "ggrandesi", "hriego", "rishikawa", "dandrade"]


# Carregar as senhas hasheadas
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

# Configurar as credenciais de autenticação
credentials = {
    "usernames": {
        usernames[0]: {"name": names[0], "password": hashed_passwords[0]},
        usernames[1]: {"name": names[1], "password": hashed_passwords[1]},
        usernames[2]: {"name": names[2], "password": hashed_passwords[2]},
        usernames[3]: {"name": names[3], "password": hashed_passwords[3]},
        usernames[4]: {"name": names[4], "password": hashed_passwords[4]},
        usernames[5]: {"name": names[5], "password": hashed_passwords[5]},
        usernames[6]: {"name": names[6], "password": hashed_passwords[6]},
        usernames[7]: {"name": names[7], "password": hashed_passwords[7]},
        usernames[8]: {"name": names[8], "password": hashed_passwords[8]},
        usernames[9]: {"name": names[9], "password": hashed_passwords[9]},
        usernames[10]: {"name": names[10], "password": hashed_passwords[10]},
    }
}

# Criar o objeto de autenticação
authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="promon_ai_chatbot",
    cookie_key="some_cookie_key",
    cookie_expiry_days=30
)

# Autenticação do usuário
name, authentication_status, username = authenticator.login("main")

# Função para carregar índices do Azure AI Search
def get_available_indexes(search_endpoint, search_key):
    index_client = SearchIndexClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_key))
    indexes = index_client.list_indexes()  # Lista todos os índices disponíveis
    return [index.name for index in indexes]

# Mapeamento entre os nomes reais dos índices e os nomes amigáveis
index_name_mapping = {
    "epotl-dp": "E.POTL001 - Projeto GLP/C5+",
    "vopak-dp": "E.VPAK001 - VOPAK",
    "recursos-humanos": "Relações Humanas"
}

# Função para obter o nome amigável a partir do nome real do índice
def get_friendly_index_name(real_index_name):
    return index_name_mapping.get(real_index_name, real_index_name)

# Verificar o status da autenticação
if authentication_status == False:
    st.error("Nome de usuário ou senha incorretos")

if authentication_status == None:
    st.warning("Por favor, insira o nome de usuário e a senha")

if authentication_status:
    # --- SE O USUÁRIO ESTIVER AUTENTICADO ---
    st.title(f"Bem-vindo, {name}, ao MakrAI - Promon Engenharia!")

    # Carregar índices disponíveis do Azure AI Search
    available_indexes = get_available_indexes(search_endpoint, search_key)

    # Criar uma lista de nomes amigáveis a serem exibidos no dropdown
    friendly_indexes = [get_friendly_index_name(index) for index in available_indexes]

    # Dropdown para selecionar o índice
    selected_friendly_index = st.sidebar.selectbox("Selecione o índice do Azure AI Search", options=friendly_indexes)

    # Encontrar o nome real do índice selecionado com base no nome amigável
    selected_index = [key for key, value in index_name_mapping.items() if value == selected_friendly_index][0]

    # Função para criar o chat com dados do Azure AI Search
    def create_chat_with_data_completion(aoai_deployment_name, messages, aoai_endpoint, aoai_key, search_endpoint, search_key, selected_index):
        client = openai.AzureOpenAI(
            api_key=aoai_key,
            api_version="2024-06-01",
            azure_endpoint=aoai_endpoint
        )
        return client.chat.completions.create(
            model=aoai_deployment_name,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            stream=True,
            extra_body={
                "data_sources": [
                    {
                        "type": "azure_search",
                        "parameters": {
                            "endpoint": search_endpoint,
                            "index_name": selected_index,  # Usar o índice selecionado pelo usuário
                            "semantic_configuration": "default",
                            "query_type": "semantic",
                            "fields_mapping": {},
                            "in_scope": True,
                            "role_information": ROLE_INFORMATION,
                            "strictness": 3,
                            "top_n_documents": 5,
                            "authentication": {
                                "type": "api_key",
                                "key": search_key
                            }
                        }
                    }
                ]
            }
        )

    # Função para lidar com a entrada do chat e gerar resposta
    def handle_chat_prompt(prompt, aoai_deployment_name, aoai_endpoint, aoai_key, search_endpoint, search_key, selected_index):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Exibir a resposta do chatbot
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            documents_used = []

            for response in create_chat_with_data_completion(aoai_deployment_name, st.session_state.messages, aoai_endpoint, aoai_key, search_endpoint, search_key, selected_index):
                if response.choices:
                    full_response += (response.choices[0].delta.content or "")
                    if hasattr(response.choices[0], 'data') and "documents" in response.choices[0].data:
                        documents_used = response.choices[0].data["documents"]
                    message_placeholder.markdown(full_response + "▌")

            # Gerar links clicáveis para os documentos utilizados, caso existam
            if documents_used:
                full_response += "\n\n**Documentos Referenciados:**\n"
                for i, doc in enumerate(documents_used):
                    doc_url = f"https://{storage_account}.blob.core.windows.net/{storage_container}/{doc['document_id']}"
                    full_response += f"[{i+1}]({doc_url})\n"

            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Função principal do Streamlit
    def main():
        st.write("""
        # MakrAI - Promon Engenharia
        """)

        # Inicializar o histórico de mensagens
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Exibir o histórico de mensagens
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Caixa de entrada do chat
        if prompt := st.chat_input("Digite sua pergunta:"):
            handle_chat_prompt(prompt, aoai_deployment_name, aoai_endpoint, aoai_key, search_endpoint, search_key, selected_index)

    if __name__ == "__main__":
        main()

    # Adicionar disclaimer no rodapé
    st.sidebar.markdown("""
    **Disclaimer**:
    O "MakrAI" tem como único objetivo disponibilizar dados que sirvam como um meio de orientação e apoio; não constitui, porém, uma recomendação vinculante pois não representam uma análise personalizada para um Cliente e/ou Projeto específico, e, portanto, não devem ser utilizados como única fonte de informação na tomada de decisões pelos profissionais Promon.
    """)

    # Botão de logout
    authenticator.logout("Logout", "sidebar")
