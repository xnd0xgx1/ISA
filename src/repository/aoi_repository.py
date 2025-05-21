import logging
from src.interfaces.aoi_interface import AOIInterface
from openai import AzureOpenAI
import json
# from azure.core.credentials import AzureKeyCredential
import re

class AOIRepository(AOIInterface):

   

    def __init__(self, endpoint):
        self.client = AzureOpenAI(
            api_key="9ZdC0OfiFYbjNGejuHcADRYqhpll2gUPd3OwradiqvsgNGSFkNNuJQQJ99BBACYeBjFXJ3w3AAABACOGmKlW",  
            api_version="2024-10-21",
            azure_endpoint = endpoint
            )
        
    def Call(self,content):
        logging.error(f"Content on AOI")
        response = self.client.chat.completions.create(
            model='gpt-4',
            messages=[
                {
                    "role": "system",
                    "content": """Eres un agente especializado en extracción de campos de contratos. Tu tarea es devolver SIEMPRE un arreglo de objetos JSON (uno por cada cobertura) con los siguientes campos. NO añadas comentarios ni ningún texto fuera del JSON. NO uses comillas simples. NO pongas comas en los valores numéricos.

⚠️ ATENCIÓN IMPORTANTE: SIEMPRE debes detectar TODAS las coberturas que existan en el documento. Los subtítulos de las coberturas aparecen generalmente bajo títulos como:
- “GARANTÍAS, FIANZAS Y SEGUROS”
- “GARANTÍAS Y SEGUROS”

Los subtítulos de las coberturas pueden empezar con letras (a), b), c)...), guiones o incluso ser párrafos separados. DEBES detectar cada cobertura como un bloque de contenido que incluya descripción, porcentaje, duración, y beneficiario si está disponible. 

⚠️ Si el texto tiene más de una cobertura, DEVUELVE cada una como un objeto separado dentro del array. NO omitas ninguna.

Formato de salida esperado (ejemplo, no copiar literalmente):
[
  {
    "ContratoOrden": 4620004040,
    "ContratoMarco": "4620004841",
    "NitProveedor": "901212206-9",
    "NombreProveedor": "DATA KNOW S.A.S",
    "Objeto": "Prestación de servicios de soporte...",
    "GestionGarantiasDoc": true,
    "Cobertura": "Garantía de Cumplimiento",
    "DescripcionCobertura": "...",
    "CoberturaPara": "Contrato",
    "PorcentajeCobertura": 10,
    "TextoTiempoAdicionalCobertura": "...",
    "TiempoAdicionalCobertura": 1,
    "DescripcionValorDoc": "...",
    "ValorDoc": "INDETERMINADO",
    "Moneda": "COP",
    "PlazoVigenciaDoc": "...",
    "PlazoDoc": 60,
    "FechaInicioCobertura": "01/01/2025",
    "FechaFinCobertura": "30/01/2025",
    "OrdenInicio": 1
  }
]

Descripción de campos a extraer:
- ContratoOrden: Número de 10 dígitos visible en encabezado, título o texto como "ORDEN DE ENTREGA No".
- ContratoMarco: Opcional. Puede aparecer como “Contrato Marco No”.
- NitProveedor, NombreProveedor, Objeto: Extraer desde la lista `contratopolizagarantia` usando el número de ContratoOrden.
- GestionGarantiasDoc: true si aparece el título de garantías y contenido debajo; false si no.
- Cobertura: El nombre de la cobertura (por ejemplo: "Garantía de Cumplimiento").
- DescripcionCobertura: Todo el contenido textual asociado a esa cobertura.
- CoberturaPara: "Contrato" o "Orden", según el contexto del documento.
- PorcentajeCobertura: Extraído como número (ej. "10").
- TextoTiempoAdicionalCobertura y TiempoAdicionalCobertura: Texto y valor numérico si hay un plazo adicional.
- DescripcionValorDoc, ValorDoc, Moneda: Extraer del texto donde se hable del valor del contrato.
- PlazoVigenciaDoc, PlazoDoc: Texto y duración del contrato en días.
- FechaInicioCobertura: Formato dd/MM/yyyy.
- FechaFinCobertura: Calcular si es posible; si no, dejar vacío.
- OrdenInicio: 1 si se menciona “orden de inicio”; 0 si no.

Tu salida debe ser un array con un objeto por cada cobertura encontrada en el documento. No omitas ninguna. Si hay 4, devuelves 4 objetos. Si solo hay 1, devuelves uno.

                    """,
                },
                {
                    "role": "user",
                    "content": "Extrae los campos de este contenido fuente: " + content,
                }
            ]
        )
        try:
            responseoai = response.choices[0].message.content.replace("json\n","")
            # logging.warning(f"Respuesta del openai: {responseoai}")
            match = re.search(r'(\[.*\])', responseoai, re.S)
            if not match:
                return '[]'
            json_str = match.group(1)

            data = json.loads(json_str)
            return json.dumps(data)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
            return '[]'
        except Exception as e:
            logging.error(f"Error processing response: {e}")
            return '[]'
    def ExtractObjeto(self,content):
        logging.info(f"Content on AOI {content}")
        response = self.client.chat.completions.create(
            model='o3-mini',
            messages=[
                {
                    "role": "system",
                    "content": """Necesito que me traigas UNICAMENTE el objeto de la garantia, que normalmente empieza despues de CUYO OBJETO, NO AGREGUES TEXTO NI CAMBIES EL CONTENIDO., Ejemplo:
                    CUYO OBJETO ES EL OBJETO DEL CONTRATO ES LA PRESTACIÓN DE LOS SERVICIOS PARA LA
EJECUCIÓN DEL MANTENIMIENTO DE LÍNEAS DE TRANSMISIÓN DE ENERGÍA Y FIBRA ÓPTICA Y DEMÁS SERVICIOS Y SUMINISTROS INHERENTES A ESTOS, BAJO LA
MODALIDAD DE OUTSOURCING, EN EL TERRITORIO COLOMBIANO.
                    """,
                },
                {
                    "role": "user",
                    "content": "Extrae el objeto de este contenido fuente: " + content,
                }
            ]
        )
        logging.warning(f"Respuesta del OPENAI: {response.choices[0].message.content}")
        return  response.choices[0].message.content