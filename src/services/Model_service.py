from src.interfaces.di_interface import DocIntInterface
from src.interfaces.aoi_interface import AOIInterface
import logging
class ModelService:

    def __init__(self,azure_di:DocIntInterface,azure_oi: AOIInterface):
        self.azure_di = azure_di
        self.azure_oi = azure_oi

    def process(self,filestream):
        result = self.azure_di.Process(filestream=filestream,azure_oi=self.azure_oi)
        return result
    def processfase2(self,filestream):
        content = self.azure_di.ProcessFase2(filestream=filestream)
        logging.warning(f"Result initilializing AOI")
        result = self.azure_oi.Call(content=content)
        return result
    