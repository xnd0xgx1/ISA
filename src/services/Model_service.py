from src.interfaces.di_interface import DocIntInterface
from src.interfaces.aoi_interface import AOIInterface
from src.interfaces.st_interface import STInterface
import logging
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
        merged_list = []
        base_body = body_list[0] if body_list else {}
        fields_to_copy = ['NitProveedor', 'NombreProveedor']

        # Si solo hay un resultado, usarlo para todos los items del body
        if len(result_list) == 1:
            single_result = result_list[0] or {}
            for original in body_list:
                merged = original.copy()
                for key, val in single_result.items():
                    if val is not None and val != "":
                        merged[key] = val
                for field in fields_to_copy:
                    val = base_body.get(field)
                    if val is not None and val != "":
                        merged[field] = val
                merged_list.append(merged)
        else:
            single_result = body_list[0] or {}
            for original in result_list:
                merged = original.copy()
                for key, val in single_result.items():
                    if val is not None and val != "":
                        merged[key] = val
                for field in fields_to_copy:
                    val = base_body.get(field)
                    if val is not None and val != "":
                        merged[field] = val
                merged_list.append(merged)
    

        return merged_list
    def processfase2Autocompletado(self,contrato):
        file1 = self.azure_st.Get(f"{contrato}/file1.pdf")
        file2 = self.azure_st.Get(f"{contrato}/file2.pdf")
        content = self.azure_di.ProcessFase2(filestream=file1)
        content2 = self.azure_di.ProcessFase2(filestream=file2)
        contenidoFinal = f"Contenido1: {content}, Contenido2: {content2}"
        result = self.azure_oi.Call(content=contenidoFinal,TipoDocumento="AutoContenido")
        return result

    def procesar_doble_json(self, json1, json2):
        claves = [
            "ContratoOrden",
            "NombreProveedor",
            "NitProveedor",
            "Cobertura",
            "ValorDoc",
            "Moneda",
            "PorcentajeCobertura",
            "FechaInicioCobertura",
            "FechaFinCobertura"
        ]

        resultado = []
        
        for json in json1:
            cumple = False
            for recibida in json2:
                if all(
                    str(json.get(clave, "")).strip() == str(recibida.get(clave, "")).strip()
                    for clave in claves
                ):
                    cumple = True
                    break

            estado = "Cumple" if cumple else "No Cumple"
            resultado.append({
                **json,
                "Estado": estado
            })

        return resultado