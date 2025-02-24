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
        """
        Primera llamada a la API con logs detallados
        """
        print("\n--- INICIO BÚSQUEDA DE PRODUCTO ---")
        print(f"Query: {query}")
        
        # Preparar el contexto
        products_list = "\n".join([
            f"{i}. {row['Nombre del producto']} - {row['Principal objetivo']}"
            for i, row in self.df.iterrows()
        ])
        
        print("Productos disponibles:")
        print(products_list)
        
        try:
            print("\n>> Llamando a OpenAI API...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente dental. Debes responder SOLO con el número del producto más relevante (0-13) o -1 si no hay match."},
                    {"role": "user", "content": f"PRODUCTOS:\n{products_list}\n\nCONSULTA: {query}\n\nResponde SOLO con el número:"}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            print(f"Respuesta cruda de OpenAI: '{result}'")
            
            try:
                index = int(result)
                print(f"Índice convertido: {index}")
                if 0 <= index < len(self.df):
                    product = self.df.iloc[index]['Nombre del producto']
                    print(f"Producto encontrado: {product}")
                    return index
                else:
                    print(f"ERROR: Índice {index} fuera de rango [0-{len(self.df)-1}]")
                    return -1
            except ValueError:
                print(f"ERROR: No se pudo convertir '{result}' a número")
                return -1
                
        except Exception as e:
            print(f"ERROR en API OpenAI: {str(e)}")
            return -1
        finally:
            print("--- FIN BÚSQUEDA DE PRODUCTO ---\n")

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
        Procesa la consulta del usuario y retorna una respuesta con logs detallados
        """
        print("\n=== INICIO PROCESAMIENTO DE CONSULTA ===")
        print(f"Consulta recibida: {user_query}")
        
        # Agregar la consulta del usuario a la historia
        self.conversation_history.append((True, user_query))
        print("Historia de conversación actualizada")
        
        # Primera llamada: encontrar el producto relevante
        print("\n>> Buscando producto relevante...")
        product_index = self.find_relevant_product(user_query)
        print(f"Índice de producto retornado: {product_index}")
        
        if product_index == -1:
            print("WARNING: find_relevant_product() retornó -1")
            print("Razón posible: No se encontró match o hubo error en la llamada a la API")
            response = "Lo siento, no pude encontrar un producto específico para tu consulta. ¿Podrías ser más específico sobre lo que estás buscando?"
        else:
            print(f"\n>> Generando respuesta para producto {product_index}...")
            # Actualizar el último producto discutido
            self.last_product_index = product_index
            try:
                product_name = self.df.iloc[product_index]['Nombre del producto']
                print(f"Producto seleccionado: {product_name}")
                response = self.get_product_response(product_index, user_query)
            except Exception as e:
                print(f"ERROR en get_product_response: {str(e)}")
                response = "Hubo un error generando la respuesta. Por favor, intenta nuevamente."
        
        # Agregar la respuesta a la historia
        self.conversation_history.append((False, response))
        print("\n>> Respuesta final generada")
        print("=== FIN PROCESAMIENTO DE CONSULTA ===\n")
        
        return response
