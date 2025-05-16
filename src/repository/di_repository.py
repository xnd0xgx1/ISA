import logging
from azure.identity import DefaultAzureCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from src.interfaces.di_interface import DocIntInterface
import json
from datetime import datetime
import re
from azure.core.credentials import AzureKeyCredential


class DocIntRepository(DocIntInterface):

   

    def __init__(self, doc_int_endpoint):
        # credential = DefaultAzureCredential()
        credential = AzureKeyCredential("5zUCiMdRV1dAYM2Z21bD5Az47d2K3PEUCbVqtdTQ5UiWyzgMxt9iJQQJ99BBACYeBjFXJ3w3AAALACOGUFu1")
        self.client = DocumentIntelligenceClient(doc_int_endpoint, credential)
        
    def formatear_fecha(self,fecha_str):
        logging.warning(f"Fecha: {fecha_str}")
        if not fecha_str:
            return "01/01/2025"
        formatos = ["%d-%b-%Y", "%d-%m-%Y", "%d/%b/%Y", "%d/%m/%Y", "%d-%B-%Y", "%d/%B/%Y","%Y/%m/%d"]
        fecha = None
        for fmt in formatos:
            try:
                fecha = datetime.strptime(fecha_str, fmt)
                return fecha.strftime("%d/%m/%Y")
            except ValueError:
                pass
        SPANISH_MONTHS = {
            # abreviaturas
            "ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04", "MAY": "05", "JUN": "06",
            "JUL": "07", "AGO": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DIC": "12",
            # nombres completos
            "ENERO": "01", "FEBRERO": "02", "MARZO": "03", "ABRIL": "04", "MAYO": "05", "JUNIO": "06",
            "JULIO": "07", "AGOSTO": "08", "SEPTIEMBRE": "09", "OCTUBRE": "10", "NOVIEMBRE": "11", "DICIEMBRE": "12",
        }
        cad = fecha_str.strip().upper()
        def _repl(match):
            mes_txt = match.group(0)
            return SPANISH_MONTHS.get(mes_txt, mes_txt)
        cad_num = re.sub(r'\b[A-Z]{3,9}\b', _repl, cad)
        formatos2 = ["%d-%m-%Y", "%d/%m/%Y"]
        for fmt in formatos2:
            try:
                fecha = datetime.strptime(cad_num, fmt)
                return fecha.strftime("%d/%m/%Y")
            except ValueError:
                pass

        # 4) Si aun así no podemos, devolvemos el valor por defecto
        return "01/01/2025"
        
        
    def limpiar_contrato(self,contrato_str):
        if not contrato_str:
            return 0
        match = re.search(r'\d{10,}', contrato_str)
        if match:
            return int(match.group())
        return 0
    

    def Process(self, filestream):
        try:
            logging.info(f"[DocIntRepository - process] - initialize")

            FIELD_MAP = {
                "Nacional": {
                    "amparos":       "AMPAROS",
                    "desde":         "VIGENCIA DESDE",
                    "hasta":         "VIGENCIA HASTA",
                    "valor_prima":   "SUMA ASEGURADA",
                    "coberturas":"Coberturas",
                    "contrato":"Contrato",
                    "numeropoliza":"NumeroPoliza",
                    "numeromodificacion":"NumeroModificacion",
                    "aseguradora":"Aseguradora",
                    "nombreproveedor":"NombreProveedor",
                    "nitproveedor":"NitProveedor",
                    "nombreasegurado":"NombreAsegurado",
                    "nitasegurado":"NitAsegurado",
                    "objetocaratula":"ObjetoCaratula"
                },
                "Bolivar": {
                    "amparos":       "COBERTURA",
                    "desde":         "DESDE",
                    "hasta":         "HASTA",
                    "valor_prima":   "VALOR ASEGURADO",
                    "coberturas":"Coberturas",
                     "contrato":"Contrato",
                     "numeropoliza":"NumeroPoliza",
                    "numeromodificacion":"NumeroModificacion",
                    "aseguradora":"Aseguradora",
                    "nombreproveedor":"NombreProveedor",
                    "nitproveedor":"NitProveedor",
                    "nombreasegurado":"NombreAsegurado",
                    "nitasegurado":"NitAsegurado",
                    "objetocaratula":"ObjetoCaratula"
                },
                "Cesce": {
                    "amparos":       "Coberturas",
                    "desde":         "DESDE",
                    "hasta":         "HASTA",
                    "valor_prima":   "Valor",
                    "coberturas":"Coberturas",
                    "contrato":"Contrato",
                    "numeropoliza":"NumeroPoliza",
                    "numeromodificacion":"NumeroModificacion",
                    "aseguradora":"Aseguradora",
                    "nombreproveedor":"NombreProveedor",
                    "nitproveedor":"NitProveedor",
                    "nombreasegurado":"NombreAsegurado",
                    "nitasegurado":"NitAsegurado",
                    "objetocaratula":"ObjetoCaratula"
                },
                "Chubb": {
                    "amparos":       "Coberturas",
                    "desde":         "Vig. Desde (YYYY/MM/DD)",
                    "hasta":         "Vig. Hasta (YYYY/MM/DD)",
                    "valor_prima":   "VLR. Asegurado",
                    "coberturas":"Coberturas",
                    "contrato":"Contrato",
                    "numeropoliza":"NumeroPoliza",
                    "numeromodificacion":"NumeroModificacion",
                    "aseguradora":"Aseguradora",
                    "nombreproveedor":"NombreProveedor",
                    "nitproveedor":"NitProveedor",
                    "nombreasegurado":"NombreAsegurado",
                    "nitasegurado":"NitAsegurado",
                    "objetocaratula":"ObjetoCaratula"
                },
                
                 "Confianza": {
                    "amparos":       "Cobertura",
                    "desde":         "Desde",
                    "hasta":         "Hasta",
                    "valor_prima":   "Valor",
                    "coberturas":"Coberturas",
                    "contrato":"Contrato",
                    "numeropoliza":"NumeroPoliza",
                    "numeromodificacion":"NumeroModificacion",
                    "aseguradora":"Aseguradora",
                    "nombreproveedor":"NombreProveedor",
                    "nitproveedor":"NitProveedor",
                    "nombreasegurado":"NombreAsegurado",
                    "nitasegurado":"NitAsegurado",
                    "objetocaratula":"ObjetoCaratula"
                },
                "Solidaria": {
                    "amparos":       "DESCRIPCION AMPAROS CONTRATO",
                    "desde":         "VIGENCIA DESDE",
                    "hasta":         "VIGENCIA HASTA",
                    "valor_prima":   "SUMA ASEGURADA",
                    "coberturas":"Coberturas",
                    "contrato":"Contrato",
                    "numeropoliza":"NumeroPoliza",
                    "numeromodificacion":"NumeroModificacion",
                    "aseguradora":"Aseguradora",
                    "nombreproveedor":"NombreProveedor",
                    "nitproveedor":"NitProveedor",
                    "nombreasegurado":"NombreAsegurado",
                    "nitasegurado":"NitAsegurado",
                    "objetocaratula":"ObjetoCaratula"
                },
                "Sura2": {
                    "amparos":       "COBERTURA",
                    "desde":         "FECHA INICIAL",
                    "hasta":         "FECHA VENCIMIENTO",
                    "valor_prima":   "VALOR ASEGURADO",
                    "coberturas":"Coberturas",
                    "contrato":"Contrato",
                    "numeropoliza":"NumeroPoliza",
                    "numeromodificacion":"NumeroModificacion",
                    "aseguradora":"Aseguradora",
                    "nombreproveedor":"NombreProveedor",
                    "nitproveedor":"NitProveedor",
                    "nombreasegurado":"NombreAsegurado",
                    "nitasegurado":"NitAsegurado",
                    "objetocaratula":"ObjetoCaratula"
                },
                "Sura": {
                    "amparos":       "Cobertura",
                    "desde":         "FechaInicial",
                    "hasta":         "FechaFinal",
                    "valor_prima":   "Valor",
                    "coberturas":"Coberturas",
                     "contrato":"Contrato/Orden",
                    "numeropoliza":"NumeroPoliza",
                    "numeromodificacion":"NumeroModificacion",
                    "aseguradora":"Aseguradora",
                    "nombreproveedor":"NombreProveedor",
                    "nitproveedor":"NitProveedor",
                    "nombreasegurado":"NombreAsegurado",
                    "nitasegurado":"NitAsegurado",
                    "objetocaratula":"ObjetoCaratula"
                },
            }
            DEFAULT_MAPPING = FIELD_MAP["Sura"]
           
            logging.info("Starting classification model")
            pollercls = self.client.begin_classify_document(classifier_id="ClasificacionV2",body=filestream)
            classification_result = pollercls.result()

            logging.info(f"Classification model result {classification_result.documents[0]['docType']}")
            filestream.seek(0)
            if(classification_result.documents[0]["docType"] == "Confianza"):
                logging.info("Starting extraction model")
                poller = self.client.begin_analyze_document(model_id="CaratulasV8", body=filestream,pages=1)
            else:
                logging.info("Starting extraction model")
                poller = self.client.begin_analyze_document(model_id="CaratulasV8", body=filestream)
            result: AnalyzeResult = poller.result()
            # logging.info(f"[DocIntRepository - process] - result obtained: {result}")
            doctype = "Sura"
            output = {}
            logging.warning("Procesing DI RESULTS")
            for doc in result.documents:
                if doc.fields is None:
                    continue
                doctype = doc["docType"]
                # Determino el mapeo a usar
                mapping = FIELD_MAP.get(doc["docType"], DEFAULT_MAPPING)

                # Primero, copio todos los campos que NO sean Coberturas
                for name, fv in doc.fields.items():
                    if name != "Coberturas":
                        output[name] = fv.content or ""

                # Ahora, proceso el arreglo de Coberturas
                cob_array = doc.fields[mapping["coberturas"]]["valueArray"]  
                logging.warning("Coberturas processing")
                logging.warning(f"Mapping: {mapping}")

                cober_list = [
                    item["valueObject"][mapping["amparos"]].get("valueString","")
                    for item in cob_array
                    if mapping["amparos"] in item["valueObject"]
                ]
                desde_list = [
                    item["valueObject"][mapping["desde"]].get("valueString","")
                    for item in cob_array
                    if mapping["desde"] in item["valueObject"]
                ]
                hasta_list = [
                    item["valueObject"][mapping["hasta"]].get("valueString","")
                    for item in cob_array
                    if mapping["hasta"] in item["valueObject"]
                ]
                valor_list = [
                    item["valueObject"][mapping["valor_prima"]].get("valueString","")
                    for item in cob_array
                    if mapping["valor_prima"] in item["valueObject"]
    ]

                # output["coberturas"]       = cober_list
                # output["fechas_iniciales"] = desde_list
                # output["fechas_finales"]   = hasta_list
                # output["valores_asegurados"]= valor_list

                # 2) Empaquetamos en tuplas fila a fila
                rows = list(zip(cober_list, desde_list, hasta_list, valor_list))

                # 3) Filtramos duplicados preservando el primer encuentro
                seen = set()
                unique_rows = []
                for row in rows:
                    if row not in seen:
                        seen.add(row)
                        unique_rows.append(row)

                # 4) Desempaquetamos de nuevo en listas (o dejamos vacías si no quedó nada)
                if unique_rows:
                    cober_u, desde_u, hasta_u, valor_u = zip(*unique_rows)
                    output["coberturas"]      = list(cober_u)
                    output["fechas_iniciales"]= list(desde_u)
                    output["fechas_finales"]  = list(hasta_u)
                    output["valores_asegurados"]= list(valor_u)
                else:
                    output["coberturas"]       = cober_list
                    output["fechas_iniciales"] = desde_list
                    output["fechas_finales"]   = hasta_list
                    output["valores_asegurados"]= valor_list




            logging.warning("None Clearing")
            # Limpieza de posibles valores None
            for k, v in output.items():
                if isinstance(v, list):
                    output[k] = [elem or "" for elem in v]
                else:
                    output[k] = v or ""
            monedas = []
            nuevos_valores_asegurados = []
            logging.warning("Monedas processing")
            for val in output.get('valores_asegurados',[]):
                moneda = output.get(f'Moneda', "")
                
                if val and "$" in val:
                    partes = val.split("$", 1)
                    moneda = partes[0].strip() if partes[0].strip() != "" else "COP"
                    valor_numerico = partes[1].strip()
                    monedas.append(moneda)
                    nuevos_valores_asegurados.append(valor_numerico)
                else:
                    if val.strip() != "":
                        nuevos_valores_asegurados.append(val.strip())
                        logging.warning(f"Moneda strip {moneda.strip()}")
                        if moneda and moneda.strip() != "":
                            if(moneda.strip() == "COL$"):
                                monedas.append("COP")
                                continue
                            if(moneda.strip() == "$US"):
                                monedas.append("USD")
                                continue
                            if(moneda.strip() == "PESOS"):
                                monedas.append("COP")
                                continue
                            if(moneda.strip() == "DOLARES"):
                                monedas.append("USD")
                                continue
                            if(moneda.strip() == "$"):
                                monedas.append("COP")
                                continue
                            if(moneda.strip() == "US$"):
                                monedas.append("USD")
                                continue
                            if(moneda.strip() == "US $"):
                                monedas.append("USD")
                                continue
                            if(moneda.strip() == "($-Pesos"):
                                monedas.append("COP")
                                continue
                            if(moneda.strip() == "($USA-Dolares"):
                                monedas.append("USD")
                                continue
                            if(moneda.strip() == "EUR$"):
                                monedas.append("EUR")
                                continue
                            else:
                                monedas.append("COP")
                                continue
                        else:
                            monedas.append("COP")
                    else:
                        nuevos_valores_asegurados.append("")
                        monedas.append("")
            



            logging.warning("Coberturas procesing elimination")
            # Se eliminan los campos específicos de coberturas del output general
            for i in range(1, 10):
                sufijo = "" if i == 1 else str(i)
                for campo in [f'Cobertura{sufijo}', f'FechaInicialCobertura{sufijo}', f'FechaFinalCobertura{sufijo}', f'ValorAseguradoMoneda{sufijo}']:
                    if campo in output:
                        output.pop(campo)

            # Se clona la información general en una nueva lista de objetos, uno por cobertura
            resultados = []
            m = FIELD_MAP.get(doctype)
            if not m:
                raise ValueError(f"No existe configuración de campos para el doctype {doctype!r}")
            logging.warning(f"dctype {doctype}")
            logging.warning(f"map {m}")
            
            # Obtener cantidad de coberturas encontradas (se asume que todas las listas tienen la misma longitud)
            cantidad = len(output.get("coberturas",[]))
            logging.warning(f"cantidad {cantidad}")
            logging.warning(f"cantidad { output.get('coberturas',[]) }")
            logging.warning(f"fechainicial {output.get('fechas_iniciales',[])}")
            logging.warning(f"fechafinal {output.get('fechas_iniciales',[])}")


            logging.warning(f"Valores : {nuevos_valores_asegurados}")
            logging.warning(f"Monedas : {monedas}")
            for idx in range(cantidad):
                obj_cobertura = {}
                obj_cobertura["NumeroPóliza"] = output.get(m["numeropoliza"], "")
                obj_cobertura["NumeroModificación"] = output.get(m["numeromodificacion"], "")
                obj_cobertura["Aseguradora"] = output.get(m["aseguradora"], "")
                obj_cobertura["NombreProveedor"] = output.get(m["nombreproveedor"], "")
                obj_cobertura["NitProveedor"] = output.get(m["nitproveedor"], "")
                obj_cobertura["NombreAsegurado"] = output.get(m["nombreasegurado"], "")
                obj_cobertura["NitAsegurado"] = output.get(m["nitasegurado"], "")
                obj_cobertura["ObjetoCaratula"] = output.get(m["objetocaratula"], "")
                logging.warning("SETTING COBERTURAS")

                obj_cobertura["Cobertura"] = output.get("coberturas",[])[idx]
                logging.warning("SETTING fechas")
                obj_cobertura["FechaInicialCobertura"] = self.formatear_fecha(output.get('fechas_iniciales',[])[idx])
                obj_cobertura["FechaFinalCobertura"] = self.formatear_fecha(output.get('fechas_finales',[])[idx])

               
                obj_cobertura["ValorAsegurado"] = nuevos_valores_asegurados[idx]
                obj_cobertura["Moneda"] = monedas[idx]

                obj_cobertura["ContratoOrden"] = self.limpiar_contrato(output.get(m["contrato"], ""))
                resultados.append(obj_cobertura)

            finaljson = json.dumps(resultados)
            logging.info(f"[DocIntRepository - process] - finalize: {finaljson}")
            return finaljson

        except Exception as e:
            logging.error(f"Error al ejecutar openai: {str(e)}")
            raise ValueError(f"[DocIntRepository - process] - Error: {str(e)}")



    def ProcessFase2(self, filestream):
        try:
            logging.info(f"[DocIntRepository - process] - initialize")

            poller = self.client.begin_analyze_document(model_id="prebuilt-read",body=filestream,pages="1-30")
            result: AnalyzeResult = poller.result()
            return result.content

        except Exception as e:
            logging.error(f"Error al ejecutar openai: {str(e)}")
            raise ValueError(f"[DocIntRepository - process] - Error: {str(e)}")