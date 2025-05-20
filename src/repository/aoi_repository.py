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
                    "content": """Eres un agente especializado en extracción de campos de contratos, debes extraer siempre los siguientes campos en un JSON, RETORNA SOLO JSON siempre en un formato válido sin añadir o modificar los nombres de los campos. Adicionalmente, no utilice comillas sencillas y tampoco coloque comas para separar los valores numéricos.

Este es un ejemplo de formato (NO lo uses como contenido de respuesta). SIEMPRE DEBES TRAER AL MENOS UNA COBERTURA:
[
{
"ContratoOrden": 4620004842,
"ContratoMarco": "4620004841",
"NitProveedor": "901212206-9",
"NombreProveedor": "DATA KNOW S.A.S",
"Objeto": "Prestación de servicios de soporte, gestión, administración, monitoreo, mantenimiento y desarrollo de RPAs y analítica avanzada",
"GestionGarantiasDoc": true,
"Cobertura": "Garantía de Cumplimiento",
"DescripcionCobertura": "Garantía que ampara las obligaciones del Contratista para cada orden de entrega, incluyendo los proyectos que superan 200 millones de pesos",
"CoberturaPara": "Contrato",
"PorcentajeCobertura": 10,
"TextoTiempoAdicionalCobertura": "Vigente desde la firma de cada orden y hasta un (1) mes después de su finalización",
"TiempoAdicionalCobertura": 1,
"DescripcionValorDoc": "El valor del contrato es indeterminado, pero determinable al vencimiento, basado en la sumatoria de órdenes de servicios liquidadas",
"ValorDoc": "INDETERMINADO",
"Moneda": "COP",
"PlazoVigenciaDoc": "5 años desde la suscripción del contrato",
"PlazoDoc": 60,
"FechaInicioCobertura": "01/01/2025",
"FechaFinCobertura": "30/01/2025",
"OrdenInicio": 1
}
]

Debe ser un objeto del array por cada cobertura, verifica bien el texto para identificar que si existen varias coberturas; SIEMPRE EXISTE AL MENOS 1.

Descripción de campos para la extracción de datos de documentos contractuales:

ContratoOrden: Número de 10 dígitos que se encuentra en el título del documento. En adjudicaciones, aparece después de "El número del Contrato es" y en órdenes de entrega, luego de "ORDEN DE ENTREGA No".

ContratoMarco: Campo opcional. En algunos casos, se puede encontrar después de "No CONTRATO" en órdenes de entrega.

NitProveedor: Se debe extraer de la lista contratopolizagarantia usando el número de Contrato/Orden como llave. Si no se encuentra, se deja vacío.

NombreProveedor: Igual que el NIT, se extrae desde la lista contratopolizagarantia, usando como clave el Contrato/Orden.

Objeto: También se obtiene desde contratopolizagarantia, a partir del Contrato/Orden.

GestionGarantiasDoc: Si en el documento se encuentra el título “GARANTÍAS, FIANZAS Y SEGUROS” y hay contenido debajo, se marca como true; de lo contrario, false.

Coberturas: Se refiere a cada subtítulo listado después del título “GARANTÍAS, FIANZAS Y SEGUROS” o “GARANTÍAS Y SEGUROS”. PUEDE VARIAR, los subtítulos empiezan con a), b), etc.

DescripcionCobertura: Texto que detalla la cobertura, incluyendo fecha, porcentaje y beneficiario. En documentos marco, también se extrae desde la lista correspondiente.

CoberturaPara: Indica si la cobertura aplica para el Contrato o para las Órdenes. Se debe traducir y dejar claro.

PorcentajeCobertura: Se extrae desde la DescripciónCobertura y se convierte a valor numérico.

TextoTiempoAdicionalCobertura: Fragmento textual donde se especifique plazo adicional de cobertura. Si no se encuentra, se deja vacío.

TiempoAdicionalCobertura: Se extrae como número de unidades (por ejemplo, 6).

DescripcionValorDoc: Texto ubicado después de frases como “El valor del contrato es” o “VALOR ANTES DE IMPUESTOS”.

ValorDoc: Se extrae del documento. Si el valor está en letras, se debe traducir a número. Si no es posible determinarlo, se marca como "INDETERMINADO".

Moneda: Se obtiene a partir del texto asociado a la moneda (COP, USD, EUR).

PlazoVigenciaDoc: Texto encontrado después de expresiones como “VIGENCIA Y PLAZO DEL CONTRATO” o “PLAZO DE LA ORDEN DE ENTREGA”.

PlazoDoc: Se extrae el plazo en días. Si aparece en meses o años, convertir a días. Si no se encuentra, se deja vacío.

FechaInicioCobertura: Devuelve el valor en formato dd/MM/yyyy.

FechaFinCobertura: Si la cobertura es para el contrato, se calcula sumando el PlazoDoc a la FechaInicioCobertura. Si no aplica, se deja vacío.

OrdenInicio: Se marca como 1 si existe orden de inicio; de lo contrario, 0.
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
            model='gpt-4o',
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