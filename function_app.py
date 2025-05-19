import azure.functions as func
import logging
from src.services.Model_service import ModelService
from src.repository.di_repository import DocIntRepository
from src.repository.aoi_repository import AOIRepository
from src.repository.st_repository import STRepository
import os
from io import BytesIO

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

diendpoint = os.environ["DOC_INT_ENDPOINT"]
oaiendpoint = os.environ["AOI_ENDPOINT"]
stconn = os.environ["ST_ACOUNNT_URL"]
azuredi = DocIntRepository(doc_int_endpoint=diendpoint)
azure_oi = AOIRepository(oaiendpoint)
azure_st = STRepository(stconn) 
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
       

   
         
        contrato = req.params.get("contrato")
        if not contrato:
            return func.HttpResponse(
                "Se deben enviar el contrato", 
                status_code=400
            )



        # Llamar a servicio de procesamiento sobre ambos archivos
        resultado = modelService.processfase2Autocompletado(contrato)

        
        return func.HttpResponse(resultado, status_code=200, mimetype="application/json")
          
    

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
