from src.interfaces.di_interface import DocIntInterface
from src.interfaces.aoi_interface import AOIInterface
from src.interfaces.st_interface import STInterface
import logging
import json
class ModelService:

    def __init__(self,azure_di:DocIntInterface,azure_oi: AOIInterface,azure_st: STInterface):
        self.azure_di = azure_di
        self.azure_oi = azure_oi
        self.azure_st = azure_st

    def process(self,filestream):
        result = self.azure_di.Process(filestream=filestream,azure_oi=self.azure_oi)
        return result
    
    def identificarDoc(self,filestream,DocumentoCompras):
        content = self.azure_di.GetFirstPage(filestream=filestream)
        result = self.azure_oi.CallId(content=content)
        filestream.seek(0) 
        saveresult = self.azure_st.Save(f"{DocumentoCompras}/{result['TipoDocumento']}.pdf",filestream)
        logging.warning(saveresult)
        return result
    
    def processfase2(self,DocumentoCompras,TipoDocumento,body_list):
        logging.warning("Inciando proceamiento!")
        file1 = self.azure_st.Get(f"{DocumentoCompras}/{TipoDocumento}.pdf")
        content = self.azure_di.ProcessFase2(filestream=file1)
        logging.warning(f"Result initilializing AOI")
        result_list = self.azure_oi.Call(content=content,TipoDocumento=TipoDocumento)
        logging.warning(f"Resulado OAI: {result_list}")
        if TipoDocumento != "ContratoMinuta":
            merged_list = []
            if TipoDocumento != "SAP":
                # Si solo hay un resultado, usarlo para todos los items del body
                if len(result_list) <= len(body_list):
                    single_result = result_list[0] or {}
                    for original in body_list:
                        merged = original.copy()
                        merged["ContratoOrden"] = single_result["ContratoOrden"]
                        merged["ContratoMarco"] = single_result["ContratoMarco"]
                        merged["GestionGarantiasDoc"] = single_result["GestionGarantiasDoc"]
                        merged["CoberturaPara"] = "Orden"
                        merged["DescripcionValorDoc"] = ""
                        merged["ValorDoc"] = single_result["ValorDoc"]
                        merged["Moneda"] = single_result["Moneda"]
                        merged["PlazoVigenciaDoc"] = single_result["PlazoVigenciaDoc"]
                        merged["PlazoDoc"] = single_result["PlazoDoc"]
                        merged["FechaInicioCobertura"] = single_result["FechaInicioCobertura"]
                        merged["FechaFinCobertura"] = single_result["FechaFinCobertura"]
                        merged["OrdenInicio"] = single_result["OrdenInicio"]
                        merged_list.append(merged)
                        logging.warning(f"MergedList: {merged_list}")
                    result_list_orden = self.azure_oi.Call(content=f"{merged_list}",TipoDocumento="FECHAFIN")
                    return result_list_orden
                else:
                    single_result = body_list[0] or {}
                    for original in result_list:
                        merged = original.copy()
                        merged["NitProveedor"] = single_result["NitProveedor"]
                        merged["NombreProveedor"] = single_result["NombreProveedor"]
                        merged["Objeto"] = single_result["Objeto"]
                        merged["CoberturaPara"] = "Orden"
                        merged_list.append(merged)
                        logging.warning(f"MergedList: {merged_list}")
                    result_list_orden = self.azure_oi.Call(content=f"{merged_list}",TipoDocumento="FECHAFIN")
                    return result_list_orden
            else:
                single_result = result_list[0] or {}
                for original in body_list:
                    merged = original.copy()
                    merged["ContratoOrden"] = single_result["ContratoOrden"]
                    merged["ContratoMarco"] = single_result["ContratoMarco"]
                    merged["GestionGarantiasDoc"] = single_result["GestionGarantiasDoc"]
                    merged["CoberturaPara"] = "Orden"
                    merged["DescripcionValorDoc"] = ""
                    merged["ValorDoc"] = single_result["ValorDoc"]
                    merged["Moneda"] = single_result["Moneda"]
                    merged["PlazoVigenciaDoc"] = single_result["PlazoVigenciaDoc"]
                    merged["PlazoDoc"] = single_result["PlazoDoc"]
                    merged["FechaInicioCobertura"] = single_result["FechaInicioCobertura"]
                    merged["FechaFinCobertura"] = single_result["FechaFinCobertura"]
                    merged["OrdenInicio"] = single_result["OrdenInicio"]

                    merged_list.append(merged)
                logging.warning(f"MergedList: {merged_list}")
                result_list_sap = self.azure_oi.Call(content=f"{merged_list}",TipoDocumento="FECHAFIN")
                return result_list_sap
        else:
            return result_list
    def processfase2Autocompletado(self,contrato):
        file1 = self.azure_st.Get(f"{contrato}/file1.pdf")
        file2 = self.azure_st.Get(f"{contrato}/file2.pdf")
        content = self.azure_di.ProcessFase2(filestream=file1)
        content2 = self.azure_di.ProcessFase2(filestream=file2)
        contenidoFinal = f"Contenido1: {content}, Contenido2: {content2}"
        result = self.azure_oi.Call(content=contenidoFinal,TipoDocumento="AutoContenido")
        return json.dumps(result)

    def procesar_doble_json(self, json):
        result = self.azure_oi.Revisar(content=json)
        return result