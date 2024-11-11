import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import (WebBaseLoader, YoutubeLoader, CSVLoader, PyPDFLoader, TextLoader)
from loaders import *
import tempfile
from langchain.prompts import ChatPromptTemplate


Tipos_arquivos_validos = [
    'Site','Youtube','PDF','CSV','TXT'
]

select_models = {'Groq':{'modelos':['gemma2-9b-it','llama-3.1-70b-versatile','mixtral-8x7b-32768'],
                         'chat':ChatGroq},
                 'OpenAI':{'modelos':['gpt-4o-mini','gpt-4o','o1-preview','o1-mini'],
                           'chat':ChatOpenAI}
}

Memoria = ConversationBufferMemory()

def carrega_arquivo(tipo_arquivo,arquivo):
    if tipo_arquivo == 'Site':
        documento = carrega_site(arquivo)
    if tipo_arquivo == 'Youtube':
        documento = carrega_youtube(arquivo)
    if tipo_arquivo == 'PDF':
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_pdf(nome_temp)
    if tipo_arquivo == 'CSV':
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_csv(nome_temp)
    if tipo_arquivo == 'TXT':
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_txt(nome_temp)
    return documento

def carrega_modelo(provedor, modelo, api_key, tipo_arquivo, arquivo):
    documento = carrega_arquivo(tipo_arquivo,arquivo)

    system_message = '''Você é um assistente amigável chamado Gauss.
    Você possui acesso às seguintes informações vindas 
    de um documento {}: 

    ####
    {}
    ####

    Utilize as informações fornecidas para basear as suas respostas.

    Sempre que houver $ na sua saída, substita por S.

    Se a informação do documento for algo como "Just a moment...Enable JavaScript and cookies to continue" 
    sugira ao usuário carregar novamente o Gauss!'''.format(tipo_arquivo, documento)
        
    template = ChatPromptTemplate.from_messages([
        ('system', system_message),
        ('placeholder', '{chat_history}'),
        ('user', '{input}')
    ])

    chat = select_models[provedor]['chat'](model = modelo, api_key=api_key)
    chain = template | chat

    st.session_state['chain'] = chain 

def pagina_chat():
    st.header('🤖 Bem-vindo ao (Gauss) Chat da d²(ia) 🎲 ', divider = True)

    chain = st.session_state.get('chain')

    if chain is None:
        st.error('Carregue o Gauss')
        st.stop()

    memoria = st.session_state.get('memoria',Memoria)

    for mensagem in memoria.buffer_as_messages:
        chat = st.chat_message(mensagem.type)
        chat.markdown(mensagem.content)

    input_usuario = st.chat_input('Fale com o Gauss')
    if input_usuario:
        chat = st.chat_message('human')
        chat.markdown(input_usuario)

        chat = st.chat_message('ai')
        resposta = chat.write_stream(chain.stream({
            'input': input_usuario, 
            'chat_history': memoria.buffer_as_messages
            }))

        memoria.chat_memory.add_user_message(input_usuario)
        memoria.chat_memory.add_ai_message(resposta)
        st.session_state['memoria'] = memoria


def sidebar():
    tabs = st.tabs(['Upload de Arquivos', 'Seleção de Modelos'])
    with tabs[0]:
        tipo_arquivo = st.selectbox('Selecione o tipo de arquivo', Tipos_arquivos_validos)
        if tipo_arquivo == 'Site':
            arquivo = st.text_input('Digite a url do site')
        if tipo_arquivo == 'Youtube':
            arquivo = st.text_input('Digite a url do vídeo')
        if tipo_arquivo == 'PDF':
            arquivo = st.file_uploader('Faça o upload do arquivo pdf', type = ['.pdf'])
        if tipo_arquivo == 'CSV':
            arquivo = st.file_uploader('Faça o upload do arquivo csv', type = ['.csv'])
        if tipo_arquivo == 'TXT':
            arquivo = st.file_uploader('Faça o upload do arquivo txt', type = ['.txt'])
    with tabs[1]:
        provedor = st.selectbox('Selecione o provedor dos modelo', select_models.keys())
        modelo = st.selectbox('Selecione o modelo', select_models[provedor]['modelos'])
        api_key = st.text_input(f'Adicione a api key para o provedor {provedor}', value=st.session_state.get(f'api_key_{provedor}'))

        st.session_state[f'api_key_{provedor}'] = api_key
    
    if st.button('Inicializar Gauss', use_container_width= True):
        carrega_modelo(provedor, modelo, api_key,tipo_arquivo, arquivo)
    if st.button('Apagar Histórico de Conversa', use_container_width=True):
        st.session_state['memoria'] = Memoria

def main():
    with st.sidebar:
        sidebar()
    pagina_chat()


if __name__ == '__main__':
    main()