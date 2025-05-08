import azure.functions as func
import logging
from src.services.Model_service import ModelService
from src.repository.di_repository import DocIntRepository
import os
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

diendpoint = os.environ["DOC_INT_ENDPOINT"]
azuredi = DocIntRepository(doc_int_endpoint=diendpoint)
modelService = ModelService(azure_di=azuredi)

@app.route(route="ProcessDocument", methods=["POST"])
def ProcessDocument(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        content_type = req.headers.get('Content-Type', '')
        if content_type == 'application/pdf':
            logging.info("[ProcessDocument] - recibiendo PDF como cuerpo binario")
            file_bytes = req.get_body()  # obtener el contenido binario del PDF
            from io import BytesIO
            file_stream = BytesIO(file_bytes)

            # Procesar el archivo
            result = modelService.process(file_stream)

            return func.HttpResponse(result, status_code=200, mimetype="application/json")
        else:
            return func.HttpResponse("Tipo de contenido no soportado", status_code=400)

    except Exception as e:
        logging.error(f"Error procesando el documento: {str(e)}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)

