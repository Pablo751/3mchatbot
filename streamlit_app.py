import streamlit as st
import os
import sys
from pathlib import Path

# Configurar página
st.set_page_config(
    page_title="Chatbot Dental 3M",
    page_icon="🦷",
    layout="centered"
)

# Añadir el directorio src al path
root_path = Path(__file__).parent.absolute()
sys.path.append(str(root_path))

# Título y descripción
st.title("🦷 Asistente Virtual Dental 3M")
st.markdown("""
Este asistente te ayudará a encontrar el producto dental 3M más adecuado para tus necesidades.
""")

try:
    from dotenv import load_dotenv
    from src.chatbot import DentalProductChatbot
except ImportError as e:
    st.error(f"Error importando módulos necesarios: {str(e)}")
    st.stop()

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
        # Verificar que el archivo CSV existe
        csv_path = Path(__file__).parent / "src" / "data" / "Dentistas 2 - Hoja 1.csv"
        if not csv_path.exists():
            st.error(f"No se encontró el archivo CSV en: {csv_path}")
            return None
            
        chatbot = DentalProductChatbot(api_key=api_key)
        return chatbot
    except Exception as e:
        st.error(f"Error inicializando el chatbot: {str(e)}")
        st.error("Detalles del error para debugging:")
        st.code(str(e))
        return None

# Inicializar el chatbot
chatbot = get_chatbot()

# Verificar si el chatbot se inicializó correctamente
if chatbot is None:
    st.error("No se pudo inicializar el chatbot. Por favor, verifica los logs para más detalles.")
    st.stop()

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
    
    try:
        # Obtener respuesta del chatbot
        with st.chat_message("assistant"):
            with st.spinner('Procesando tu consulta...'):  # Add loading indicator
                response = chatbot.process_query(prompt)
                st.markdown(response)
            
        # Agregar respuesta del asistente al historial
        st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"Error procesando la consulta: {str(e)}")
        # Log detailed error for debugging
        st.error("Detalles del error:")
        st.code(str(e))

# Botón para limpiar el historial
if st.sidebar.button("Limpiar conversación"):
    st.session_state.messages = []
    st.rerun()

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

    # Mostrar estado de la configuración
    st.markdown("### Estado del Sistema")
    if api_key:
        st.success("✅ API Key configurada")
    else:
        st.error("❌ API Key no configurada")
    
    if chatbot:
        st.success("✅ Chatbot inicializado")
    else:
        st.error("❌ Chatbot no inicializado")
