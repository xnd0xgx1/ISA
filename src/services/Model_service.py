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
    def processfase2(self,filestream):
        content = self.azure_di.ProcessFase2(filestream=filestream)
        logging.warning(f"Result initilializing AOI")
        result = self.azure_oi.Call(content=content)
        return result
    def processfase2Autocompletado(self,contrato):
        file1 = self.azure_st.Get(f"{contrato}/file1.pdf")
        file2 = self.azure_st.Get(f"{contrato}/file2.pdf")
        content = self.azure_di.ProcessFase2(filestream=file1)
        content2 = self.azure_di.ProcessFase2(filestream=file2)
        contenidoFinal = f"Contenido1: {content}, Contenido2: {content2}"
        result = self.azure_oi.Call(content=contenidoFinal)
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