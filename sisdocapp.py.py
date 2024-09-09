import pickle
from pathlib import Path
import streamlit as st
import streamlit_authenticator as stauth
import openai

# Usar st.secrets para acessar as variáveis de ambiente
aoai_endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"]
aoai_key = st.secrets["AZURE_OPENAI_API_KEY"]
aoai_deployment_name = st.secrets["AZURE_OPENAI_CHAT_COMPLETIONS_DEPLOYMENT_NAME"]
search_endpoint = st.secrets["AZURE_SEARCH_SERVICE_ENDPOINT"]
search_key = st.secrets["AZURE_SEARCH_SERVICE_ADMIN_KEY"]
search_index_name = st.secrets["SEARCH_INDEX_NAME"]
storage_account = st.secrets["AZURE_STORAGE_ACCOUNT"]
storage_container = st.secrets["AZURE_STORAGE_CONTAINER"]

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
names = ["Peter Parker", "Rebecca Miller", "Michel Daros", "Gustavo Pelissaro", "Alex Sandoval", "Alexsandra Mendes", "Marco Lamim"]
usernames = ["pparker", "rmiller", "mdaros", "gpelissaro", "asandoval", "amendes", "mlamim"]

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

# Verificar o status da autenticação
if authentication_status == False:
    st.error("Nome de usuário ou senha incorretos")

if authentication_status == None:
    st.warning("Por favor, insira o nome de usuário e a senha")

if authentication_status:
    # --- SE O USUÁRIO ESTIVER AUTENTICADO ---
    st.title(f"Bem-vindo, {name}!")

    # Função para criar o chat sem dados externos
    def create_chat_completion(aoai_deployment_name, messages, aoai_endpoint, aoai_key):
        client = openai.AzureOpenAI(
            api_key=aoai_key,
            api_version="2024-06-01",
            azure_endpoint=aoai_endpoint
        )
        return client.chat.completions.create(
            model=aoai_deployment_name,
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],
            stream=True
        )

    # Função para criar o chat com dados do Azure AI Search
    def create_chat_with_data_completion(aoai_deployment_name, messages, aoai_endpoint, aoai_key, search_endpoint, search_key, search_index_name):
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
                            "index_name": search_index_name,
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
    def handle_chat_prompt(prompt, aoai_deployment_name, aoai_endpoint, aoai_key, search_endpoint, search_key, search_index_name, model_type):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Exibir a resposta do chatbot
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            documents_used = []

            if model_type == "Usar modelo GPT-4 base":
                for response in create_chat_completion(aoai_deployment_name, st.session_state.messages, aoai_endpoint, aoai_key):
                    if response.choices:
                        full_response += (response.choices[0].delta.content or "")
                        message_placeholder.markdown(full_response + "▌")
            else:
                for response in create_chat_with_data_completion(aoai_deployment_name, st.session_state.messages, aoai_endpoint, aoai_key, search_endpoint, search_key, search_index_name):
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
        # Chatbot Promon Engenharia - Projeto Vopak
        """)

        # Inicializar o histórico de mensagens
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Selecionar o tipo de modelo
        model_type = st.sidebar.radio(label="Selecione o tipo de modelo", options=["Usar modelo GPT-4 base", "Usar modelo GPT-4 com Azure AI Search"])

        # Exibir o histórico de mensagens
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Caixa de entrada do chat
        if prompt := st.chat_input("Digite sua pergunta:"):
            handle_chat_prompt(prompt, aoai_deployment_name, aoai_endpoint, aoai_key, search_endpoint, search_key, search_index_name, model_type)

    if __name__ == "__main__":
        main()

    # Botão de logout
    authenticator.logout("Logout", "sidebar")
