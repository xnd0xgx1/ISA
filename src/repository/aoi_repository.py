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
        logging.info(f"Content on AOI {content}")
        response = self.client.chat.completions.create(
            model='gpt-4',
            messages=[
                {
                    "role": "system",
                    "content": """Eres un agente especializado en extracción de campos de contratos, debes extraer siempre los siguientes campos en un json, RETORNA SOLO JSON siempre en un formato válido sin añadir o modificar los nombres de los campos, Este es un ejemplo de formato (NO lo uses como contenido de respuesta): 
                        [{
                                "ContratoOrden": "",
                                "ContratoMarco": "",
                                "NitProveedor": "",
                                "NombreProveedor": "",
                                "Objeto": "",
                                "GestionGarantiasDoc": false,
                                "Cobertura": "",
                                "DescripcionCobertura": "",
                                "CoberturaPara": "",
                                "PorcentajeCobertura": 0,
                                "TextoTiempoAdicionalCobertura": "",
                                "TiempoAdicionalCobertura": 0,
                                "DescripcionValorDoc": "",
                                "ValorDoc": 0,
                                "Moneda": "",
                                "PlazoVigenciaDoc": "",
                                "PlazoDoc": 0,
                                "FechaInicioCobertura": "",
                                "FechaFinCobertura": "",
                                "OrdenInicio": 0
                                }]

                                debe ser un Objeto por cada cobertura, verifica bien el texto para identificar que si existan varias coberturas, 
                                Descripción de campos para la extracción de datos de documentos contractuales:
                                
                                ContratoOrden: Número de 10 dígitos que se encuentra en el título del documento. En adjudicaciones, aparece después de "El número del Contrato es" y en órdenes de entrega, luego de "ORDEN DE ENTREGA No".

                                ContratoMarco: Campo opcional. En algunos casos, se puede encontrar después de "No CONTRATO" en órdenes de entrega.

                                NitProveedor: Se debe extraer de la lista contratopolizagarantia usando el número de Contrato/Orden como llave. Si no se encuentra, se deja vacío.

                                NombreProveedor: Igual que el NIT, se extrae desde la lista contratopolizagarantia, usando como clave el Contrato/Orden.

                                Objeto: También se obtiene desde contratopolizagarantia, a partir del Contrato/Orden.

                                GestionGarantiasDoc: Si en el documento se encuentra el título “GARANTÍAS, FIANZAS Y SEGUROS” y hay contenido debajo, se marca como “SI”; de lo contrario, se coloca “NO”.

                                Cobertura: Se refiere a cada subtítulo listado después del título “GARANTÍAS, FIANZAS Y SEGUROS” o “GARANTÍAS Y SEGUROS”. Si es un contrato marco, se deben crear múltiples filas para cada cobertura listada.

                                DescripcionCobertura: Texto que detalla la cobertura, incluyendo fecha, porcentaje y beneficiario. En documentos marco, también se extrae desde la lista correspondiente.

                                CoberturaPara: Indica si la cobertura aplica para el Contrato o para las Órdenes. Se debe traducir y dejar claro.

                                PorcentajeCobertura: Se extrae desde la Descripción Cobertura y se convierte a valor numérico.

                                TextoTiempoAdicionalCobertura: Fragmento textual donde se especifique plazo adicional de cobertura. Si no se encuentra, se deja vacío.

                                TiempoAdicionalCobertura: Se traduce y extrae como está en el documento (ej. "6 meses adicionales").

                                DescripcionValorDoc: Texto ubicado después de frases como “El valor del contrato es” o “VALOR ANTES DE IMPUESTOS”.

                                ValorDoc: Se extrae del documento. Si el valor está en letras, se debe traducir a número. Si no es posible determinarlo, se marca como “INDETERMINADO”.

                                Moneda: Se obtiene a partir del texto asociado a la moneda (COP, USD, EUR), y puede estar antes o después del valor.

                                PlazoVigenciaDoc: Texto encontrado después de expresiones como “VIGENCIA Y PLAZO DEL CONTRATO” o “PLAZO DE LA ORDEN DE ENTREGA”. Especifica duración y vigencia del contrato u orden.

                                PlazoDoc: De este campo se extrae el plazo en días, meses o años, y la fecha que se menciona para la constitución de garantías. Si no se encuentra, se deja vacío.

                                FechaInicioCobertura: En contratos, se refiere a la fecha ubicada en secciones como “Resumen de eventos / Completado”. Para órdenes, también puede aparecer explícitamente (devuelve el valor en formato de fecha).

                                FechaFinCobertura: Si la cobertura es para el contrato, se calcula sumando el Plazo Doc a la Fecha Inicio Cobertura. Si no aplica, se deja vacío  (devuelve el valor en formato de fecha).

                                OrdenInicio: Se marca como “SI” si en el documento se menciona que hay una orden de inicio (por ejemplo: “ORDEN DE ENTREGA / ORDEN DE SERVICIOS”); en caso contrario, “NO”.



                    """,
                },
                {
                    "role": "user",
                    "content": "Extrae los campos de este contenido fuente: " + content,
                }
            ]
        )
        responseoai = response.choices[0].message.content.replace("json\n","")
        logging.warning(f"Respuesta del openai: {responseoai}")
        match = re.search(r'(\[.*\])', responseoai, re.S)
        if not match:
            return '[]'
        json_str = match.group(1)

        data = json.loads(json_str)
        return json.dumps(data)
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