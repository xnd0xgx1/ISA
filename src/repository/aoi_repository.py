import logging
from src.interfaces.aoi_interface import AOIInterface
from openai import AzureOpenAI
import json
# from azure.core.credentials import AzureKeyCredential
import re

class AOIRepository(AOIInterface):

    promptContratoMinuta = """
Eres un agente especializado en extracción de campos de contratos. Tu tarea es devolver SIEMPRE un arreglo de objetos JSON (uno por cada cobertura) con los siguientes campos. NO añadas comentarios ni ningún texto fuera del JSON. NO uses comillas simples. NO pongas comas en los valores numéricos.

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
    "NitProveedor": "",
    "NombreProveedor": "",
    "Objeto": "",
    "GestionGarantiasDoc": true,
    "Cobertura": "Garantía de Cumplimiento",
    "DescripcionCobertura": "...",
    "CoberturaPara": "Contrato",
    "PorcentajeCobertura": 10,
    "TextoTiempoAdicionalCobertura": "...",
    "TiempoAdicionalCobertura": "1 dia",
    "DescripcionValorDoc": "...",
    "ValorDoc": "INDETERMINADO",
    "Moneda": "COP",
    "PlazoVigenciaDoc": "El plazo de la vigencia de documento",
    "PlazoDoc": "60 meses",
    "FechaInicioCobertura": "01/01/2025",
    "FechaFinCobertura": "30/01/2025",
    "OrdenInicio": 1
  }
]

Descripción de campos a extraer:
- ContratoOrden: Número de 10 dígitos visible en encabezado, título o texto como "ORDEN DE ENTREGA No".
- ContratoMarco: Opcional. Puede aparecer como “Contrato Marco No” si no se encuentra dejar como string vacio.
- NitProveedor, NombreProveedor, Objeto: Extraer desde la lista.
- GestionGarantiasDoc: true si aparece el título de garantías y contenido debajo; false si no.
- Cobertura: El nombre de la cobertura (por ejemplo: "Garantía de Cumplimiento", son todos los subtitulos despues de GARANTÍAS, FIANZAS Y SEGUROS, los subtitulos empiezan con letras a), b), etc.. (Pueden existir varias, siempre al menos una, ejemplos de coberturas: Garantía de Cumplimiento,Garantía de Calidad y Correcto Funcionamiento de los Equipo,Garantía de pago de salarios, prestaciones sociales e indemnizaciones,Garantía de Responsabilidad Civil Extracontractual,Seguro de Accidentes Personales,Garantía de Calidad y Correcto Funcionamiento de los Equipos,).
- DescripcionCobertura: Todo el contenido textual asociado a esa cobertura antes de que inicie la siguiente (hasta antes del proximo subtitulo o titulo) NO CORTES EL PARRAFO
- CoberturaPara: "Contrato" o "Orden", según el contexto del documento.
- PorcentajeCobertura: Extraído como número (ej. "10").
- TextoTiempoAdicionalCobertura: Texto si hay un plazo adicional
- TiempoAdicionalCobertura: valor con unidades si hay un plazo adicional, ejemplo del valor: 2 años, 10 meses, 1 día, etc...
- DescripcionValorDoc:Texto ubicado despues de VALOR TRAE TODO EL CONTEXTO
- ValorDoc: Ubicado despues del titulo VALOR (si encuentra el valor en numero; si esta en letras traducirlo y poner el valor en numero; si no colocar INDETERMINADO)
-  Moneda: Si lo encuentras en letras traducirlo, si esta en valor se encuentra antes. casos COP, USD, EUR.
- PlazoVigenciaDoc: Texto ubicado en PLAZO  Texto ubicado despues de VIGENCIA Y PLAZO DEL CONTRATO / PLAZO, traer todo el texto asociado
- PlazoDoc: Transcirbe la duración del contrato en días teniendo en cuenta el PlazoVigenciaDoc teniendo la unidad de tiempo en el texto
- FechaInicioCobertura: Formato dd/MM/yyyy SIEMPRE esta como la marca de tiempo (fecha) de completado (del documento), ejemplo: en Completado\nSeguridad comprobada\n17/01/2025 la fecha seria 17/01/2025 NUNCA LO DEJES VACIO.
- FechaFinCobertura: La fecha calculada del inicio de la cobertura más el plazoDoc.
- OrdenInicio: 1 si se menciona “orden de inicio”; 0 si no.

Tu salida debe ser un array con un objeto por cada cobertura encontrada en el documento. No omitas ninguna. Si hay 4, devuelves 4 objetos. Si solo hay 1, devuelves uno.
               """
    
    promptOrdenminuta = """
Eres un agente especializado en extracción de campos de ordenes. Tu tarea es devolver SIEMPRE un arreglo de objetos JSON (uno por cada cobertura) con los siguientes campos. NO añadas comentarios ni ningún texto fuera del JSON. NO uses comillas simples. NO pongas comas en los valores numéricos.

Los subtítulos de las coberturas pueden empezar con letras (a), b), c)...), guiones o incluso ser párrafos separados. DEBES detectar cada cobertura como un bloque de contenido que incluya descripción, porcentaje, duración, y beneficiario si está disponible. 

⚠️ Si el texto tiene más de una cobertura, DEVUELVE cada una como un objeto separado dentro del array. NO omitas ninguna.

Formato de salida esperado (ejemplo, no copiar literalmente):
[
  {
    "ContratoOrden": 4620004040,
    "ContratoMarco": "4620004841",
    "NitProveedor": "",
    "NombreProveedor": "",
    "Objeto": "",
    "GestionGarantiasDoc": true,
    "Cobertura": "Garantía de Cumplimiento",
    "DescripcionCobertura": "...",
    "CoberturaPara": "ORDEN",
    "PorcentajeCobertura": 10,
    "TextoTiempoAdicionalCobertura": "...",
    "TiempoAdicionalCobertura": "1 mes",
    "DescripcionValorDoc": "...",
    "ValorDoc": "INDETERMINADO",
    "Moneda": "COP",
    "PlazoVigenciaDoc": "...",
    "PlazoDoc": "",
    "FechaInicioCobertura": "01/01/2025",
    "FechaFinCobertura": "30/01/2025",
    "OrdenInicio": 1
  }
]

Descripción de campos a extraer:
- ContratoOrden: Número de 10 dígitos visible en encabezado, título o texto como "ORDEN DE ENTREGA No".
- ContratoMarco: Numero de 10 digitos ubicado despues de "No CONTRATO".
- NitProveedor, NombreProveedor, Objeto: Extraer desde la lista.
- GestionGarantiasDoc: true si aparece el título de garantías y contenido debajo; false si no.
- Cobertura: El nombre de la cobertura (por ejemplo: "Garantía de Cumplimiento", son todos los subtitulos despues de GARANTÍAS, FIANZAS Y SEGUROS, los subtitulos empiezan con letras a), b), etc.. (Pueden existir varias, siempre al menos una, ejemplos de coberturas: Garantía de Cumplimiento,Garantía de Calidad y Correcto Funcionamiento de los Equipo,Garantía de pago de salarios, prestaciones sociales e indemnizaciones,Garantía de Responsabilidad Civil Extracontractual,Seguro de Accidentes PersonalesGarantía de Calidad y Correcto Funcionamiento de los Equipos,).
- DescripcionCobertura: Todo el contenido textual asociado a esa cobertura antes de que inicie la siguiente (hasta antes del proximo subtitulo o titulo) NO CORTES EL PARRAFO
- CoberturaPara:Orden
- PorcentajeCobertura: Extraído como número (ej. "10").
- TextoTiempoAdicionalCobertura y TiempoAdicionalCobertura: Texto y valor con unidades si hay un plazo adicional, ejemplo del valor: 2 años, 10 meses, 1 día, etc...
- DescripcionValorDoc: ""
- ValorDoc: Valor ubicado despues de VALOR ANTES DE IMPUESTOS (traerlo numerico)
- Moneda: Texto ubicado despues de "MONEDA" (COP USD EUR)
- PlazoVigenciaDoc: Texto despues de PLAZO DE LA ORDEN DE ENTREGA:
- PlazoDoc: De Plazo/VigenciaDoc traer dato de plazo sea en dias, meses ó años; si no dejar vacio
- FechaInicioCobertura: Formato dd/MM/yyyy teniendo el inicio de la cobertura o en su defecto el del contrato (debe venir al final como la marca de tiempo completado, ejemplo: en Completado\nSeguridad comprobada\n17/01/2025).
- FechaFinCobertura:el fin de la cobertura asociada (calcularlo segun la vigencia e inicio del contrato en formato fecha), si no, dejar vacío.
- OrdenInicio: Si en el campo Plazo/VigenciaDoc se indica que tiene orden de inicio colocar SI, de lo contrario NO 

Tu salida debe ser un array con un objeto por cada cobertura encontrada en el documento. No omitas ninguna. Si hay 4, devuelves 4 objetos. Si solo hay 1, devuelves uno.
               """
    promptSap = """
Eres un agente especializado en extracción de campos de contratos. Tu tarea es devolver SIEMPRE un arreglo de objetos JSON con los siguientes campos. NO añadas comentarios ni ningún texto fuera del JSON. NO uses comillas simples. NO pongas comas en los valores numéricos.



Formato de salida esperado (ejemplo, no copiar literalmente):
[
  {
    "ContratoOrden": 4620004040,
    "ContratoMarco": "4620004841",
    "GestionGarantiasDoc": true,
    "CoberturaPara": "Orden",
  
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
- ContratoOrden: Numero despues de: ORDEN DE ENTREGA/ORDEN DE SERVICIOS 
- ContratoMarco: Si en el titulo principal encuentra el contrato (inicia con 46/15 y es de 10 digitos).
- GestionGarantiasDoc: true si aparece el título de garantías y contenido debajo; false si no.
- CoberturaPara: Orden
- DescripcionValorDoc:Texto en Titulo VALOR
- ValorDoc:Ubicado despues del titulo VALOR (si encuentra el valor en numero; si esta en letras traducirlo y poner el valor en numero; si no colocar INDETERMINADO)
- Moneda: Si lo encuentra en letras traducirlo, si esta en valor se encuentra antes. casos COP, USD, EUR
- PlazoVigenciaDoc: Texto despues del titulo VIGENCIA Y PLAZO (Traer todo el parrafo)
- PlazoDoc: De Plazo/VigenciaDoc traer dato de plazo sea en dias, meses ó años; si no dejar vacio
- FechaInicioCobertura: Fecha ubicada en "Resumen de eventos sobre / Completado" como marca de tiempo
- FechaFinCobertura:el fin de la cobertura asociada (calcularlo segun la vigencia e inicio del contrato en formato fecha), si no, dejar vacío.
- OrdenInicio: Si en el campo Plazo/VigenciaDoc se indica que tiene orden de inicio colocar SI, de lo contrario NO 

Tu salida debe ser un array con un objeto. No omitas ninguna.
               """
    promptAutocontenido = """Eres un agente especializado en extracción de campos de contratos. Tu tarea es devolver SIEMPRE un arreglo de objetos JSON (uno por cada cobertura) con los siguientes campos. NO añadas comentarios ni ningún texto fuera del JSON. NO uses comillas simples. NO pongas comas en los valores numéricos.

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
    "TiempoAdicionalCobertura": 1 mes,
    "DescripcionValorDoc": "...",
    "ValorDoc": "INDETERMINADO",
    "Moneda": "COP",
    "PlazoVigenciaDoc": "...",
    "PlazoDoc": 60 meses,
    "FechaInicioCobertura": "01/01/2025",
    "FechaFinCobertura": "30/01/2025",
    "OrdenInicio": 1
  }
]

Descripción de campos a extraer:
- ContratoOrden: Número de 10 dígitos visible en encabezado, título o texto como "ORDEN DE ENTREGA No".
- ContratoMarco: Opcional. Puede aparecer como “Contrato Marco No” si no se encuentra dejar como string vacio.
- NitProveedor, NombreProveedor, Objeto: Extraer desde la lista.
- GestionGarantiasDoc: true si aparece el título de garantías y contenido debajo; false si no.
- Cobertura: El nombre de la cobertura (por ejemplo: "Garantía de Cumplimiento", son todos los subtitulos despues de GARANTÍAS, FIANZAS Y SEGUROS, los subtitulos empiezan con letras a), b), etc.. (Pueden existir varias, siempre al menos una, ejemplos de coberturas: Garantía de Cumplimiento,Garantía de Calidad y Correcto Funcionamiento de los Equipo,Garantía de pago de salarios, prestaciones sociales e indemnizaciones,Garantía de Responsabilidad Civil Extracontractual,Seguro de Accidentes PersonalesGarantía de Calidad y Correcto Funcionamiento de los Equipos,).
- DescripcionCobertura: Texto donde se indique fecha, porcentaje de la cobertura y para quien, trae el contenido textual asociado a esa cobertura antes de que inicie la siguiente (hasta antes del proximo subtitulo o titulo) NO CORTES EL PARRAFO
- CoberturaPara: "Contrato".
- PorcentajeCobertura: Extraído como número (ej. "10").
- TextoTiempoAdicionalCobertura:Texto si hay un plazo adicional
- TiempoAdicionalCobertura: valor con unidades si hay un plazo adicional, ejemplo del valor: 2 años, 10 meses, 1 día, etc...
- DescripcionValorDoc: Texto ubicado despues de El valor del Contrato es
- ValorDoc: Traducir y traer de DescripcionValorDoc, si encuentra el valor en numero; si esta en letras traducirlo y poner el valor en numero; si no colocar INDETERMINADO)
- Moneda: Si lo encuentra en letras traducirlo, si esta en valor se encuentra antes. casos COP, USD, EUR
- PlazoVigenciaDoc: Texto ubicado en PLAZO  "El plazo para la ejecución", traer todo el texto
- PlazoDoc: Transcirbe la duración del contrato en días teniendo en cuenta el PlazoVigenciaDoc teniendo la unidad de tiempo en el texto
- FechaInicioCobertura: Formato dd/MM/yyyy teniendo despues del titulo Enviado:.
- FechaFinCobertura: el fin de la cobertura calcularlo segun el inicio del contrato mas el plazoDoc.
- OrdenInicio: 1 si se menciona “orden de inicio”; 0 si no.

Tu salida debe ser un array con un objeto por cada cobertura encontrada en el documento. No omitas ninguna. Si hay 4, devuelves 4 objetos. Si solo hay 1, devuelves uno.
                    """

    def __init__(self, endpoint):
        self.client = AzureOpenAI(
            api_key="9ZdC0OfiFYbjNGejuHcADRYqhpll2gUPd3OwradiqvsgNGSFkNNuJQQJ99BBACYeBjFXJ3w3AAABACOGmKlW",  
            api_version="2024-12-01-preview",
            azure_endpoint = endpoint
            )
    def clean_json_string(self,s: str) -> str:
        """
        Extrae el fragmento entre el primer '{' y el último '}', o entre el primer '['
        y el último ']' si no hay objetos, y devuelve esa subcadena.
        """
        # Primero, elimina posibles prefijos como "json\n" o ```json
        for prefix in ("json\n", "```json", "```"):
            if s.startswith(prefix):
                s = s[len(prefix):]
        s = s.strip()

        # Decide si es un objeto o un array
        if s.startswith("{") and "}" in s:
            start = s.find("{")
            end = s.rfind("}") + 1
        elif s.startswith("[") and "]" in s:
            start = s.find("[")
            end = s.rfind("]") + 1
        else:
            # Busquemos igual un objeto dentro de la cadena
            start = s.find("{")
            end = s.rfind("}") + 1
            if start == -1 or end == 0:
                # No parece contener JSON; devolvemos entero y dejaremos que json.loads falle
                return s

        candidate = s[start:end]

        # Eliminamos posibles marcas de bloque de código restantes
        return candidate.strip().strip("```").strip()
        
    def Call(self,content,TipoDocumento):
        logging.error(f"Content on AOI")
        prompt = ""
        if TipoDocumento == "ContratoMinuta":
            prompt = self.promptContratoMinuta
        elif TipoDocumento == "OrdenEntrega":
            prompt = self.promptOrdenminuta
        elif TipoDocumento == "SAP":
            prompt = self.promptSap
        elif TipoDocumento == "AutoContenido":
            prompt = self.promptAutocontenido
        else:
            prompt = self.promptContratoMinuta
        logging.error(f"Tipo de prompt: {TipoDocumento}")
        response = self.client.chat.completions.create(
            model='o3-mini',
            messages=[
                {
                    "role": "system",
                    "content": prompt,
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
                return []
            json_str = match.group(1)

            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
            return []
        except Exception as e:
            logging.error(f"Error processing response: {e}")
            return []
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
    
    def CallId(self,content):
        try:
            logging.info(f"Content on AOI")
            response = self.client.chat.completions.create(
                model='o3-mini',
                messages=[
                    {
                        "role": "system",
                        "content": """Necesito que analices la primera pagina de los documentos y logres identificar el tipo, existen solo 3: ContratoMinuta,OrdenEntrega y SAP,
                        Las diferencias son:
                        ContratoMinuta: Unicamente viene el contrato en el archivo, no viene nada relacionado a orden
                        OrdenEntrega: Viene el numero de orden siempre
                        SAP: Trae un codigo SAP
                        NOTA: A VECES EN MINUTA ORDEN VIENE EL TERMINO SAP, ESTO NO SIGNIFICA QUE SEA DEL TIPO SAP, SOLO SI TRAE EL CODIGO SAP
                        Me debes retornar Unicamente el JSON, sin nada más, verifica que el resultado final sea un JSON válido:
                        {"TipoDocumento": '<TipoDocumento>', "Contrato":<NumerodeContrato>}
                        """,
                    },
                    {
                        "role": "user",
                        "content": "Extrae el objeto de este contenido fuente: " + content,
                    }
                ]
            )
            logging.warning(f"Respuesta del OPENAI: {response.choices[0].message.content}")
            responseoai = response.choices[0].message.content.replace("json\n","")
            logging.warning(f"Respuesta del openai: {responseoai}")
            cleaned = self.clean_json_string(responseoai)
            logging.info(f"Cleaned: {cleaned}")
            try:
                
                parsed = json.loads(cleaned)
                return parsed
            except json.JSONDecodeError as e:
                logging.warning(f"Error parsing json: {e}")
                return json.loads("{}")
        except Exception as e:
            return "ContratoMinuta"
    def Revisar(self,content):
        try:
            logging.info(f"Content on AOI {content}")
            response = self.client.chat.completions.create(
                model='o3-mini',
                messages=[
                    {   
                        "role": "system",
                        "content": """Necesito que analices los json 1 y 2 con ello me arrojes un resultado si CUMPLE o NO CUMPLE, es una comparación de una garantia recibida vs requerida
                        
                        Cumple: Si todas las coberturas requeridas están presentes en Recibidas. 
                        No Cumple: Si alguna cobertura requerida no está presente en Recibidas o difiere en algún valor en las columnas mencionadas en columnas claves: Número de Contrato/Orden, Nombre del Proveedor, NIT del proveedor, Cobertura, ValorDoc, Moneda, FechaInicioCobertura y FechaFinCobertura. 
                        TEN PRESENTE QUE LAS COBERTURAS PUEDEN VARIAR UN POCO NO DEBEN DE SER EXACTAMENTE IGUALES, igual que los nombres de campos
                        Si la cobertura varia poco ejemplo: garantia de cumplimiento y cumplimiento, estas deben ser validas
                        Me debes retornar Unicamente el JSON, sin nada más, verifica que el resultado final sea un JSON válido:
                        {"Cumple": true, "Motivo":<Motivo del porque cumple o no cumple>}
                        """,
                    },
                    {
                        "role": "user",
                        "content": f"Valida los siguientes json: {json.dumps(content)}",
                    }
                ]
            )
            logging.warning(f"Respuesta del OPENAI: {response.choices[0].message.content}")
            responseoai = response.choices[0].message.content.replace("json\n","")
            logging.warning(f"Respuesta del openai: {responseoai}")
            cleaned = self.clean_json_string(responseoai)
            logging.info(f"Cleaned: {cleaned}")
            parsed = json.loads(cleaned)
            return parsed
         
        except Exception as e:
            logging.warning(f"ERROR: {e}")
            return "{}"