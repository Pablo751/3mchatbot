import openai
from typing import Tuple, List, Dict
import pandas as pd
from pathlib import Path

class DentalProductChatbot:
    def __init__(self, api_key: str):
        # Inicialización simplificada del cliente OpenAI
        self.client = openai.OpenAI(
            api_key=api_key
        )
        
        # Cargar el CSV usando rutas relativas
        try:
            csv_path = Path(__file__).parent / "data" / "Dentistas 2 - Hoja 1.csv"
            self.df = pd.read_csv(csv_path)
            self.create_search_indices()
            self.conversation_history = []
            self.last_product_index = None
        except Exception as e:
            raise Exception(f"Error cargando el CSV: {str(e)}")
        
    def create_search_indices(self):
        """Crea índices para búsqueda eficiente"""
        self.df['search_text'] = (
            self.df['Nombre del producto'].str.lower() + ' ' +
            self.df['Principal objetivo'].str.lower() + ' ' +
            self.df['Ventajas'].str.lower()
        )
        
    def find_relevant_product(self, query: str) -> int:
        # Añadir logs al inicio
        print(f"Iniciando búsqueda para query: {query}")
        print(f"DataFrame shape: {self.df.shape}")
        print(f"Primeras filas del DataFrame:")
        print(self.df.head())
        
        system_prompt = """
        Eres un asistente especializado en productos dentales. Tu tarea es identificar 
        qué producto del catálogo es más relevante para la consulta del usuario.
        Si la pregunta parece ser una contrapregunta sobre el último producto discutido,
        mantén ese mismo producto. Si es una nueva consulta, busca un nuevo producto relevante.
        Debes responder SOLO con el número de índice (0-based) del producto más relevante.
        Si no estás seguro, responde con -1.
        """
        
        # Preparar el contexto con los productos y la conversación anterior
        products_context = "\n\n".join([
            f"Índice {i}:\nNombre: {row['Nombre del producto']}\n"
            f"Objetivo: {row['Principal objetivo']}\n"
            f"Ventajas: {row['Ventajas']}"
            for i, row in self.df.iterrows()
        ])
        
        print(f"Número de productos en contexto: {len(self.df)}")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cambiado a un modelo más común
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contexto del catálogo:\n{products_context}\n\n"
                                              f"Consulta actual del usuario: {query}"}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            print(f"Respuesta de la API: {result}")
            
            try:
                index = int(result)
                print(f"Índice encontrado: {index}")
                return index
            except ValueError as ve:
                print(f"Error convirtiendo respuesta a índice: {ve}")
                return -1
                
        except Exception as e:
            print(f"Error en la API de OpenAI: {str(e)}")
            return -1

    def get_product_response(self, product_index: int, query: str) -> str:
        """
        Segunda llamada a la API: Genera una respuesta detallada sobre el producto
        considerando el contexto de la conversación
        """
        if product_index < 0 or product_index >= len(self.df):
            return "Lo siento, no pude encontrar un producto que coincida con tu consulta. Por favor, intenta ser más específico o visita nuestra página web para más información."
        
        product = self.df.iloc[product_index]
        
        system_prompt = """
        Eres un experto en productos dentales de 3M. Proporciona respuestas precisas y profesionales 
        basadas en la información proporcionada y el contexto de la conversación. Si la pregunta es una 
        contrapregunta sobre el producto actual, enfócate en responder específicamente esa duda.
        Si la información requerida no está disponible, sugiere visitar el enlace de 'Más información'.
        """
        
        product_context = (
            f"Información del producto:\n"
            f"Nombre: {product['Nombre del producto']}\n"
            f"Objetivo: {product['Principal objetivo']}\n"
            f"Instrucciones: {product['Instrucciones de Uso']}\n"
            f"Ventajas: {product['Ventajas']}\n"
            f"Presentación: {product['Presentación']}\n"
            f"Más información: {product['Más información']}"
        )
        
        # Incluir contexto de la conversación reciente
        conversation_context = "\n".join([
            f"{'Usuario' if is_user else 'Asistente'}: {msg}"
            for is_user, msg in self.conversation_history[-3:]
        ]) if self.conversation_history else ""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Usar un modelo verificado de OpenAI
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Contexto del producto:\n{product_context}\n\n"
                                              f"Conversación reciente:\n{conversation_context}\n\n"
                                              f"Pregunta actual del usuario: {query}"}
                ],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error en la API: {e}")
            return "Lo siento, hubo un error al procesar tu consulta. Por favor, intenta nuevamente."

    def process_query(self, user_query: str) -> str:
        """
        Procesa la consulta del usuario y retorna una respuesta
        """
        # Agregar la consulta del usuario a la historia
        self.conversation_history.append((True, user_query))
        
        # Primera llamada: encontrar el producto relevante
        product_index = self.find_relevant_product(user_query)
        
        if product_index == -1:
            response = "Lo siento, no pude encontrar un producto específico para tu consulta. ¿Podrías ser más específico sobre lo que estás buscando?"
        else:
            # Actualizar el último producto discutido
            self.last_product_index = product_index
            response = self.get_product_response(product_index, user_query)
        
        # Agregar la respuesta a la historia
        self.conversation_history.append((False, response))
        
        return response
