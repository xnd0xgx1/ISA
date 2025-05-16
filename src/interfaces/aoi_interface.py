from abc import ABC, abstractmethod

class AOIInterface(ABC):
    @abstractmethod
    def Call(self, content):
        pass
    @abstractmethod
    def ExtractObjeto(self, content):
        pass
   
   
   