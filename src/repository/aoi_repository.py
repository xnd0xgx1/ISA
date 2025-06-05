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

Los subtítulos de las coberturas SIEMPRE deben detectarse incluso si no tienen número o letra explícita. Pueden empezar con una letra (a., b., c., etc.), con guion, mayúsculas, o directamente con frases como “El CONTRATISTA se obliga a…”, “El CONTRATISTA deberá…”, “El CONTRATISTA constituirá…”. Si un bloque describe una obligación de asegurar, garantizar, cubrir, o entregar póliza, se debe considerar una nueva cobertura. NO supongas que todas las coberturas tienen un subtítulo explícito. Si el contenido tiene estructura y descripción distintas, asume que es una cobertura separada. Seguido de la última cobertura, puede haber un título que empiece por "PARÁGRAFO".


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
    "TextoTiempoAdicionalCobertura": "desde la firma del contrato 
hasta la fecha de finalización del plazo contractual más un (1) mes",
    "TiempoAdicionalCobertura": "1 mes",
    "DescripcionValorDoc": "El valor estimado del Contrato es la suma de MIL QUINIENTOS CUARENTA 
Y CINCO MILLONES DOSCIENTOS VEINTISÉIS MIL OCHOCIENTOS 
TREINTA Y SEIS PESOS COLOMBIANOS (COP $1.545.226.836,00), pero 
su valor real será el que resulte de la sumatoria de los productos que se 
obtengan de multiplicar los ítems entregados por su precio unitario de 
conformidad con lo estipulado en el Anexo 1 -Lista de Cantidades y Precios del contrato.
",
    "ValorDoc": "1545226836",
    "Moneda": "COP",
    "PlazoVigenciaDoc": La vigencia para la ejecución del contrato será cinco (5) años, contados a partir de la 
fecha señalada por LA EMPRESA en la orden de iniciación escrita en los mismos.
La vigencia del contrato podrá ser modificada por acuerdo entre las partes mediante 
Cláusula Adicional.",
    "PlazoDoc": "5 años",
    "FechaInicioCobertura": "01/01/2025",
    "FechaFinCobertura": "30/01/2025",
    "OrdenInicio": 1
  }
]

Descripción de campos a extraer:
- ContratoOrden: //CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO Número de 10 dígitos visible en encabezado, título o texto como "ORDEN DE ENTREGA No" 
- ContratoMarco: //CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO. Opcional. Puede aparecer como “Contrato Marco No” si no se encuentra dejar como string vacio 
- NitProveedor, NombreProveedor, Objeto (Traer el párrafo, puede empezar en "el opbjeto de la presente" o "el objeto del presente"...): Extraer desde la lista //CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO
- GestionGarantiasDoc: //CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO. true si aparece el título de garantías y contenido debajo; false si no
- Cobertura: //CAMPO INDEPENDIENTE DE CADA COBERTURA. El nombre de la cobertura (por ejemplo: "Garantía de Cumplimiento","Seguro de accidentes personales", "Garantía de Calidad y correcto Funcionamiento de los Equipos", "Garantía de pago de salarios", "Prestaciones sociales e indemnizaciones", "Garantía de Responsabilidad Civil Extracontractual", "Seguro de Accidentes Personales", etc.) son todos los subtítulos después de GARANTÍAS, FIANZAS Y SEGUROS, los subtítulos pueden empezar con letras a., b., c., etc.) Pueden existir varias coberturas, siempre al menos una. No unifiques las coberturas, cada una es distinta y debe considerarse así.
- DescripcionCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA. El campo DescripcionCobertura debe contener todo el contenido asociado hasta que inicie otra cobertura (las coberturas inician por "GARANTÍA", "SEGURO" o "BUEN MANEJO"). Nunca debes cortar en medio de los párrafos, DEBES esperar al inicio de la siguiente cobertura. Nunca asumas que se terminó una cobertura si el texto sigue describiendo condiciones de duración, valor, porcentaje o uso de la garantía. Dentro de las coberturas pueden existir múltiples saltos de línea pero no te dejes confundir, la siguiente cobertura empezará por "GARANTÍA", "SEGURO" o "BUEN MANEJO", puede ser en mayúscula o minúscula. TRAE LITERALMENTE TEXTUALMENTE TODA LA COBERTURA.
- CoberturaPara://CAMPO INDEPENDIENTE PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO. Debes analizar el contenido del campo DescripcionCobertura. Si el texto menciona explícitamente que la cobertura aplica a una “orden de servicio”, “orden de entrega”, “orden de iniciación”, “orden de compra” u otra orden, este campo debe ser "orden". Si menciona que aplica al “contrato” o si no dice nada sobre órdenes, este campo debe ser "contrato". Si hay mención tanto a contrato como a órdenes, prioriza "orden". NO dejes este campo vacío nunca.
- PorcentajeCobertura: //CAMPO INDEPENDIENTE DE CADA COBERTURA. Extraído como número en la cobertura. Si no encuentras un valor en porcentaje, deja este campo vacío. Usa DescripcionCobertura para realizar esta extracción. Ejemplo: "10% de la suma asegurada", "20% del valor del contrato", "30% del valor de la póliza", etc. Si no hay porcentaje explícito, deja este campo vacío.
- TextoTiempoAdicionalCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA, Puede estar redactado como “estar vigente por...”, “deberá tener vigencia de...”, “la garantía deberá estar vigente hasta...”, “estará vigente desde... hasta...” o alguna variante. Detecta también expresiones como “por tres (3) años, contados desde la fecha de aceptación”. No es necesario que se diga explícitamente “tiempo adicional”; si hay una duración clara aplicable a la cobertura, debes extraerla como texto y además extraerla como unidad (ejemplo: “3 años”) en el campo TiempoAdicionalCobertura.
- TiempoAdicionalCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA, valor con unidades si hay un plazo adicional, ejemplo del valor: 2 años, 10 meses, 1 día, etc... Si no existe un valor traducible a un valor de tiempo (dígito unidad de tiempo) dejas este campo vacío. Adicional, trae siempre este valor en español.
- DescripcionValorDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO Texto ubicado despues de VALOR TRAE TODO EL CONTEXTO, SIEMPRE TIENE EL VALOR DESCRIPCIÓN
- ValorDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO Ubicado despues del titulo VALOR (si encuentra el valor en numero; si esta en letras traducirlo y poner el valor en numero; si no colocar INDETERMINADO)
- Moneda://CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO Si lo encuentras en letras traducirlo, si esta en valor se encuentra antes. SOLO TRAE ESTOS CASOS COP, USD, EUR.
- PlazoVigenciaDoc:///CAMPO GLOBAL PARA TODAS LAS COBERTURAS. Transcribe literalmente el primer párrafo ubicado bajo el título “VIGENCIA Y PLAZO” o similar, que hable de la vigencia y duración general del CONTRATO. No incluyas información relacionada a órdenes de entrega individuales. El párrafo puede tener múltiples oraciones y debe terminar cuando cambie de tema o haya punto aparte que hable de plazos específicos de órdenes de entrega. No tomes información de frases que mencionen "la primera orden", "orden de entrega" o "cronograma". Este campo es exclusivamente para la duración global del contrato.
- PlazoDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS. Extrae la duración del contrato en unidades de tiempo (por ejemplo: “3 años”) a partir del campo PlazoVigenciaDoc. Ignora frases relacionadas con plazos de órdenes de entrega o garantías. Si no se menciona un plazo en años o meses explícitamente en ese párrafo, VERIFICA QUE NO EXISTA explicitamente la terminación del contrato, si es así, unicamente coloca la fecha de terminación del contrato en formato dd/MM/yyyy
- FechaInicioCobertura://CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO El campo lo vas a encontrar en formato dd/MM/yyyy SIEMPRE esta como la marca de tiempo (fecha) de completado (del documento). Al final de todo el documento encontrarás una tabla con título "Resumen de eventos del sobre", normalmente en la última fila encontrarás un registro llamado "Completado", deberás traer la fecha correspondiente a este registro. ejemplo: Completado Seguridad comprobada 17/01/2025 12:16:47 la fecha seria 17/01/2025 NUNCA LO DEJES VACÍO.
- FechaFinCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA, La fecha calculada del inicio de la cobertura (FechaInicioCobertura) más el PlazoDoc más el tiempo adicional (TiempoAdicionalCobertura), recuerda que FechaInicioCobertura viene en un formato dd/MM/yyyy. SIEMPRE TIENE FECHAINICIO, Y PLAZODOC, EN CASO DE QUE PLAZODOC, YA CONTENGA LA FECHA TERMINACIÓN DEL CONTRATO, UNICAMENTE AÑADE EL TIEMPOADICIONAL DE LA COBERTURA.
- OrdenInicio://CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO 1 si se menciona “orden de inicio”; 0 si no.

EN NINGÚN TEXTO O DESCRIPCIÓN CORTES EL PÁRRAFO! (DescripcionCobertura, TextoTiempoAdicionalCobertura,DescripcionValorDoc, PlazoVigenciaDoc)
⚠️ IMPORTANTE: Transcribe literalmente todo el texto asociado a cada cobertura, sin resumen, sin abreviar y sin cortar oraciones ni listas. No omitas elementos aunque parezcan repetitivos o similares. Tu trabajo es de extracción textual, no de interpretación ni síntesis.
Tu salida debe ser un array de objetos con un objeto por cada cobertura encontrada. No omitas ninguna. Si hay 4, devuelves 4 objetos. Si solo hay 1, devuelves uno.
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
    "PlazoDoc": "1 año",
    "FechaInicioCobertura": "01/01/2025",
    "FechaFinCobertura": "30/01/2025",
    "OrdenInicio": 1
  }
]

Descripción de campos a extraer:
- ContratoOrden://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Número de 10 dígitos visible en encabezado, título o texto como "ORDEN DE ENTREGA No".
- ContratoMarco://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Numero de 10 digitos ubicado despues de "No CONTRATO".
- NitProveedor, NombreProveedor, Objeto://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Extraer desde la lista.
- GestionGarantiasDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS true si aparece el título de garantías y contenido debajo; false si no.
- Cobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA El nombre de la cobertura (por ejemplo: "Garantía de Cumplimiento", son todos los subtitulos despues de GARANTÍAS, FIANZAS Y SEGUROS, los subtitulos empiezan con letras a), b), etc.. (Pueden existir varias, siempre al menos una, ejemplos de coberturas: Garantía de Cumplimiento,Garantía de Calidad y Correcto Funcionamiento de los Equipo,Garantía de pago de salarios, prestaciones sociales e indemnizaciones,Garantía de Responsabilidad Civil Extracontractual,Seguro de Accidentes PersonalesGarantía de Calidad y Correcto Funcionamiento de los Equipos,).
- DescripcionCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA Todo el contenido textual asociado a esa cobertura antes de que inicie la siguiente (hasta antes del proximo subtitulo o titulo) NO CORTES EL PARRAFO
- CoberturaPara://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Orden
- PorcentajeCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA Extraído como número (ej. "10").
- TextoTiempoAdicionalCobertura y TiempoAdicionalCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA Texto y valor con unidades si hay un plazo adicional, ejemplo del valor: 2 años, 10 meses, 1 día, etc...
- DescripcionValorDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS texto ubicado despues de El valor del Contrato es 
- ValorDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Valor ubicado despues de VALOR ANTES DE IMPUESTOS (traerlo numerico) ; si no colocar INDETERMINADO
- Moneda://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Texto ubicado despues de "MONEDA" (COP USD EUR)
- PlazoVigenciaDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Texto despues de PLAZO DE LA ORDEN DE ENTREGA:
- PlazoDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS De Plazo/VigenciaDoc traer dato de plazo sea en días, meses ó años; si no dejar vacio, ejemplo si el texto menciona 3 años, traer 3 años,  VERIFICA QUE NO EXISTA explicitamente la terminación del contrato, si es así, unicamente coloca la fecha de terminación del contrato en formato dd/MM/yyyy
- FechaInicioCobertura://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Formato dd/MM/yyyy teniendo el inicio de la cobertura o en su defecto el del contrato (debe venir al final como la marca de tiempo completado, ejemplo: en Completado\nSeguridad comprobada\n17/01/2025).
- FechaFinCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA, La fecha calculada del inicio de la cobertura (FechaInicioCobertura) más el PlazoDoc más el tiempo adicional (TiempoAdicionalCobertura), recuerda que FechaInicioCobertura viene en un formato dd/MM/yyyy. SIEMPRE TIENE FECHAINICIO, Y PLAZODOC, EN CASO DE QUE PLAZODOC, YA CONTENGA LA FECHA TERMINACIÓN DEL CONTRATO, UNICAMENTE AÑADE EL TIEMPOADICIONAL DE LA COBERTURA.
- OrdenInicio://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Si en el campo Plazo/VigenciaDoc se indica que tiene orden de inicio colocar SI, de lo contrario NO 

EN NINGUN TEXTO O DESCRIPCIÓN CORTES EL PARRAFO! (DescripcionCobertura,TextoTiempoAdicionalCobertura,DescripcionValorDoc,PlazoVigenciaDoc)
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
    "ValorDoc": "1233,11",
    "Moneda": "COP",
    "PlazoVigenciaDoc": "...",
    "PlazoDoc": "1 mes",
    "FechaInicioCobertura": "01/01/2025",
    "FechaFinCobertura": "30/01/2025",
    "OrdenInicio": 1
  }
]

Descripción de campos a extraer:
- ContratoOrden: Numero después de: ORDEN DE ENTREGA/ORDEN DE SERVICIOS 
- ContratoMarco: Si en el titulo principal encuentra el contrato (inicia con 46/15 y es de 10 dígitos).
- GestionGarantiasDoc: true si aparece el título de garantías y contenido debajo; false si no.
- CoberturaPara: Orden
- DescripcionValorDoc: Este campo debe devolverse vacío
- ValorDoc: Ubicado después del titulo VALOR (si encuentra el valor en numero; si esta en letras traducirlo y poner el valor en numero; si no colocar INDETERMINADO)
- Moneda: Si lo encuentra en letras traducirlo, si esta en valor se encuentra antes. casos COP, USD, EUR
- PlazoVigenciaDoc: Texto después del titulo VIGENCIA Y PLAZO (Traer todo el párrafo)
- PlazoDoc: Del campo PlazoVigenciaDoc traer dato de plazo sea en días, meses o años; si no dejar vacío, ejemplo si el texto menciona 3 años, traer 3 años,  VERIFICA QUE NO EXISTA explicitamente la terminación del contrato, si es así, unicamente coloca la fecha de terminación del contrato en formato dd/MM/yyyy
- FechaInicioCobertura://CAMPO GLOBAL PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO El campo lo vas a encontrar en formato dd/MM/yyyy SIEMPRE esta como la marca de tiempo (fecha) de completado (del documento). Al final de todo el documento encontrarás una tabla con título "Resumen de eventos del sobre", normalmente en la última fila encontrarás un registro llamado "Completado", deberás traer la fecha correspondiente a este registro. ejemplo: Completado Seguridad comprobada 17/01/2025 12:16:47 la fecha seria 17/01/2025 NUNCA LO DEJES VACÍO.
- FechaFinCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA, La fecha calculada del inicio de la cobertura (FechaInicioCobertura) más el plazoDoc más el tiempo tiempo adicional (TiempoAdicionalCobertura), recuerda que FechaInicioCobertura viene en un formato dd/MM/yyyy.
- OrdenInicio: Si en el campo Plazo/VigenciaDoc se indica que tiene orden de inicio colocar SI, de lo contrario NO 

EN NINGUN TEXTO O DESCRIPCIÓN CORTES EL PARRAFO! (DescripcionValorDoc,PlazoVigenciaDoc)
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
    "TextoTiempoAdicionalCobertura": "Su vigencia será de 2 años, después de la finalización del plazo contractual ",
    "TiempoAdicionalCobertura": "1 mes",
    "DescripcionValorDoc": "3. El valor del contrato es la suma de CUARENTA Y TRES MILLONES DE PESOS COLOMBIANOS
(COP 43’000.000) El anterior valor no incluye el Impuesto sobre las Ventas (IVA). El valor acordado no es reajustable.
",
    "ValorDoc": "43000000",
    "Moneda": "COP",
    "PlazoVigenciaDoc": "El plazo de ejecución es de cuatro (4) meses contados a partir de la fecha de emisión de la Orden de Iniciación. El plazo de ejecución
podrá ser modificado mediante Acta suscrita por las dos (2) partes.",
    "PlazoDoc": "60 meses",
    "FechaInicioCobertura": "01/01/2025",
    "FechaFinCobertura": "30/01/2025",
    "OrdenInicio": 1
  }
]

Descripción de campos a extraer:
- ContratoOrden://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Número de 10 dígitos visible en encabezado, título o texto como "ORDEN DE ENTREGA No".
- ContratoMarco://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Opcional. Puede aparecer como “Contrato Marco No” si no se encuentra dejar como string vacio.
- NitProveedor, NombreProveedor, Objeto://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Extraer desde la lista.
- GestionGarantiasDoc: true si aparece el título de garantías y contenido debajo; false si no.
- Cobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA El nombre de la cobertura (por ejemplo: "Garantía de Cumplimiento", son todos los subtitulos despues de GARANTÍAS, FIANZAS Y SEGUROS, los subtitulos empiezan con letras a), b), etc.. (Pueden existir varias, siempre al menos una, ejemplos de coberturas: Garantía de Cumplimiento,Garantía de Calidad y Correcto Funcionamiento de los Equipo,Garantía de pago de salarios, prestaciones sociales e indemnizaciones,Garantía de Responsabilidad Civil Extracontractual,Seguro de Accidentes PersonalesGarantía de Calidad y Correcto Funcionamiento de los Equipos,).
- DescripcionCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA Texto donde se indique fecha, porcentaje de la cobertura y para quien, trae el contenido textual asociado a esa cobertura antes de que inicie la siguiente (hasta antes del proximo subtitulo o titulo) NO CORTES EL PARRAFO
- CoberturaPara://CAMPO INDEPENDIENTE PARA TODAS LAS COBERTURAS VIENE DEL CONTRATO. Debes analizar el contenido del campo DescripcionCobertura. Si el texto menciona explícitamente que la cobertura aplica a una “orden de servicio”, “orden de entrega”, “orden de iniciación”, “orden de compra” u otra orden, este campo debe ser "orden". Si menciona que aplica al “contrato” o si no dice nada sobre órdenes, este campo debe ser "contrato". Si hay mención tanto a contrato como a órdenes, prioriza "orden". NO dejes este campo vacío nunca.
- PorcentajeCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA Extraído como número (ej. "10").
- TextoTiempoAdicionalCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA ES el Texto si hay un plazo adicional, si hay plazo adicional TRAE TODO EL CONTENIDO DEL PLAZO ADICIONAL
- TiempoAdicionalCobertura://CAMPO INDEPENDIENTE DE CADA COBERTURA valor con unidades si hay un plazo adicional, ejemplo del valor: 2 años, 10 meses, 1 día, etc...
- DescripcionValorDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Texto ubicado despues de VALOR, TRAE TODO EL CONTEXTO NO CORTES EL PARRAFO, SIEMPRE TIENE EL VALOR DESCRIPCIÓN, puede venir como el valor de esta orden es, el valor del documento, el valor es, etc... o similares
- ValorDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Traducir y traer de DescripcionValorDoc, si encuentra el valor en numero; si esta en letras traducirlo y poner el valor en numero; si no colocar INDETERMINADO)
- Moneda://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Si lo encuentra en letras traducirlo, si esta en valor se encuentra antes. casos COP, USD, EUR
- PlazoVigenciaDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Texto ubicado despues de PLAZO  "El plazo para la ejecución", traer todo el texto asociado en ese parrafo, NO CORTES EL PARRAFO
- PlazoDoc://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Transcribe la duración del contrato en días teniendo en cuenta el PlazoVigenciaDoc teniendo la unidad de tiempo en el texto, ejemplo si el texto menciona 3 años, traer 3 años. Traer el dato de la fecha cuando se dice "para constitución de garantías" si no dejar vacío.
- FechaInicioCobertura://CAMPO GLOBAL PARA TODAS LAS COBERTURAS Formato dd/MM/yyyy teniendo despues del titulo Enviado: SIEMPRE TRAE EL CAMPO!!.
- FechaFinCobertura://INDEPENDIENTE DE CADA COBERTURA, La fecha calculada del inicio de la cobertura (FechaInicioCobertura) más el plazoDoc más el tiempo tiempo adicional (TiempoAdicionalCobertura), recuerda que FechaInicioCobertura viene en un formato dd/MM/yyyy. SIEMPRE TIENE FECHAINICIO, Y PLAZODOC.
- OrdenInicio://CAMPO GLOBAL PARA TODAS LAS COBERTURAS 1 si se menciona “orden de inicio”; 0 si no.

Tu salida debe ser un array con un objeto por cada cobertura encontrada en el documento. No omitas ninguna. Si hay 4, devuelves 4 objetos. Si solo hay 1, devuelves uno.
                    """
    
    promptpostsap = """
Eres un agente especializado en extracción de campos de contratos. Tu tarea es devolver SIEMPRE un arreglo de objetos JSON con los siguientes campos. NO añadas comentarios ni ningún texto fuera del JSON. NO uses comillas simples. NO pongas comas en los valores numéricos UNICAMENTE NECESITO QUE MODIFIQUES LA FechaFinCobertura ningun otro campo, 
FechaFinCobertura es un CAMPO INDEPENDIENTE DE CADA COBERTURA (Por objeto del array), La fecha calculada del inicio de la cobertura (FechaInicioCobertura) más el PlazoDoc más el tiempo adicional (TiempoAdicionalCobertura), recuerda que FechaInicioCobertura viene en un formato dd/MM/yyyy. SIEMPRE TIENE FECHAINICIO, Y PLAZODOC, EN CASO DE QUE PLAZODOC, YA CONTENGA LA FECHA TERMINACIÓN DEL CONTRATO, UNICAMENTE AÑADE EL TIEMPOADICIONAL DE LA COBERTURA.
Tu salida debe ser un array con un objeto. No omitas ninguna.
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
        elif TipoDocumento == "FECHAFIN":
            prompt = self.promptpostsap
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
                        
                        Cumple: Si todas las coberturas requeridas están presentes en Recibidas. Te  en cuenta que es probable que el NitProveedor varien un poco dado que a veces se envían con guiones o el dígito de verificación, pero el nombre del proveedor debe ser el mismo.
                        No Cumple: Si alguna cobertura requerida no está presente en Recibidas o difiere en algún valor en las columnas mencionadas en columnas claves: Número de Contrato/Orden, Nombre del Proveedor, NIT del proveedor, Cobertura, ValorDoc, Moneda, FechaInicioCobertura y FechaFinCobertura. 
                        TEN PRESENTE QUE LAS COBERTURAS PUEDEN VARIAR UN POCO NO DEBEN DE SER EXACTAMENTE IGUALES, igual que los nombres de campos
                        Si la cobertura varia poco ejemplo: garantia de cumplimiento y cumplimiento, estas deben ser validas.
                        También ten en cuenta que si no se envían garantías requeridas, se debe considerar que no cumple.
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