from abc import ABC, abstractmethod

class AOIInterface(ABC):
    @abstractmethod
    def Call(self, content):
        pass
   
   