# Titulo y descripción
st.title("🦷 Asistente Virtual Dental 3M")
st.markdown("""
Este asistente te ayudará a encontrar el producto dental 3M más adecuado para tus necesidades.
""")

# Inicializar el chatbot
@st.cache_resource
def get_chatbot():
    return DentalProductChatbot(api_key=os.getenv('OPENAI_API_KEY'))

chatbot = get_chatbot()

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
