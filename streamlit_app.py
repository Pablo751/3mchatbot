import streamlit as st
import os
import sys
from pathlib import Path

# Añadir el directorio src al path
root_path = Path(__file__).parent.absolute()
sys.path.append(str(root_path))

try:
    from dotenv import load_dotenv
    from src.chatbot import DentalProductChatbot
except ImportError as e:
    st.error(f"Error importando módulos necesarios: {str(e)}")
    st.stop()

# Configurar página
st.set_page_config(
    page_title="Chatbot Dental 3M",
    page_icon="🦷",
    layout="centered"
)

# Manejo de variables de entorno
def get_api_key():
    # Intentar cargar de .env primero
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Si no está en .env, intentar obtener de Streamlit Secrets
    if not api_key and 'OPENAI_API_KEY' in st.secrets:
        api_key = st.secrets['OPENAI_API_KEY']
    
    return api_key

# Verificar API key
api_key = get_api_key()
if not api_key:
    st.error("No se encontró la API key de OpenAI. Por favor, configura la variable de entorno OPENAI_API_KEY.")
    st.stop()

# Inicializar el chatbot con manejo de errores
@st.cache_resource
def get_chatbot():
    try:
        return DentalProductChatbot(api_key=api_key)
    except Exception as e:
        st.error(f"Error inicializando el chatbot: {str(e)}")
        return None

chatbot = get_chatbot()

# Título y descripción
st.title("🦷 Asistente Virtual Dental 3M")
st.markdown("""
Este asistente te ayudará a encontrar el producto dental 3M más adecuado para tus necesidades.
""")

# Inicializar el historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar el historial de chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
    # Agregar mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Obtener respuesta del chatbot
    with st.chat_message("assistant"):
        response = chatbot.process_query(prompt)
        st.markdown(response)
        
    # Agregar respuesta del asistente al historial
    st.session_state.messages.append({"role": "assistant", "content": response})

# Botón para limpiar el historial
if st.sidebar.button("Limpiar conversación"):
    st.session_state.messages = []
    st.experimental_rerun()

# Información adicional en la barra lateral
with st.sidebar:
    st.markdown("### Acerca de")
    st.markdown("""
    Este chatbot está especializado en productos dentales 3M.
    Puede ayudarte a:
    - Encontrar el producto adecuado para tu necesidad
    - Resolver dudas sobre instrucciones de uso
    - Proporcionar información técnica
    - Comparar productos similares
    """)
