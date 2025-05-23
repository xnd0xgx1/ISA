from abc import ABC, abstractmethod
from src.interfaces.aoi_interface import AOIInterface

class DocIntInterface(ABC):
    @abstractmethod
    def Process(self, filestream,azure_oi: AOIInterface):
        pass
    @abstractmethod
    def ProcessFase2(self, filestream):
        pass
    @abstractmethod
    def GetFirstPage(self, filestream):
        pass
    @abstractmethod
    def formatear_fecha(self,fecha_str):
        pass
    @abstractmethod
    def limpiar_contrato(self,contrato_str):
        pass
    

   