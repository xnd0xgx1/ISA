import azure.functions as func
import logging
from src.services.Model_service import ModelService
from src.repository.di_repository import DocIntRepository
from src.repository.aoi_repository import AOIRepository
import os
from io import BytesIO

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

diendpoint = os.environ["DOC_INT_ENDPOINT"]
oaiendpoint = os.environ["AOI_ENDPOINT"]
azuredi = DocIntRepository(doc_int_endpoint=diendpoint)
azure_oi = AOIRepository(oaiendpoint)
modelService = ModelService(azure_di=azuredi,azure_oi=azure_oi)

@app.route(route="ProcessDocument", methods=["POST"])
def ProcessDocument(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        content_type = req.headers.get('Content-Type', '')
        if content_type == 'application/pdf':
            logging.info("[ProcessDocument] - recibiendo PDF como cuerpo binario")
            file_bytes = req.get_body()  # obtener el contenido binario del PDF
            file_stream = BytesIO(file_bytes)

            # Procesar el archivo
            result = modelService.process(file_stream)

            return func.HttpResponse(result, status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse("Tipo de contenido no soportado", status_code=400)

    except Exception as e:
        logging.error(f"Error procesando el documento: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)


@app.route(route="ProcessDocumentCaso2", methods=["POST"])
def ProcessDocumentCaso2(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        content_type = req.headers.get('Content-Type', '')

        # Soportar envíos multipart/form-data con dos archivos
        if content_type.startswith('multipart/form-data'):
            logging.info("[ProcessDocumentCaso2] - recibiendo múltiples archivos via form-data")

            # req.files es un dict de FieldStorage
            file1_field = req.files.get('file1')
            file2_field = req.files.get('file2')

            if not file1_field or not file2_field:
                return func.HttpResponse(
                    "Se deben enviar los campos 'file1' y 'file2'", 
                    status_code=400
                )

            # # Leer contenido de cada archivo
            file1_bytes = file1_field.stream.read()
            file2_bytes = file2_field.stream.read()

            # Convertir a BytesIO para procesar
            file1_stream = BytesIO(file1_bytes)
            file2_stream = BytesIO(file2_bytes)

            # Llamar a servicio de procesamiento sobre ambos archivos
            resultado = modelService.processfase2Autocompletado(file1_stream,file2_stream)

            
            return func.HttpResponse(resultado, status_code=200, mimetype="application/json")
          
        else:
            return func.HttpResponse(
                "Tipo de contenido no soportado", 
                status_code=400
            )

    except Exception as e:
        logging.error(f"Error procesando el/los documento(s): {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)



@app.route(route="ProcessDocumentFase2", methods=["POST"])
def ProcessDocumentFase2(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        content_type = req.headers.get('Content-Type', '')
        if content_type == 'application/pdf':
            logging.info("[ProcessDocument] - recibiendo PDF como cuerpo binario")
            file_bytes = req.get_body()  # obtener el contenido binario del PDF
            file_stream = BytesIO(file_bytes)

            # Procesar el archivo
            result = modelService.processfase2(file_stream)

            return func.HttpResponse(result, status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse("Tipo de contenido no soportado", status_code=400)

    except Exception as e:
        logging.error(f"Error procesando el documento: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
