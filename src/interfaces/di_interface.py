from abc import ABC, abstractmethod

class DocIntInterface(ABC):
    @abstractmethod
    def Process(self, filestream):
        pass
    @abstractmethod
    def ProcessFase2(self, filestream):
        pass
    @abstractmethod
    def formatear_fecha(self,fecha_str):
        pass
    @abstractmethod
    def limpiar_contrato(self,contrato_str):
        pass
    

   