from abc import ABC, abstractmethod

class AOIInterface(ABC):
    @abstractmethod
    def Call(self, content,TipoDocumento):
        pass
    @abstractmethod
    def ExtractObjeto(self, content):
        pass
    @abstractmethod
    def CallId(self, content):
        pass
    
    @abstractmethod
    def clean_json_string(self, s):
        pass
   
   
   
   