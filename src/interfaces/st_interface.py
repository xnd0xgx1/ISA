from abc import ABC, abstractmethod

class STInterface(ABC):
    @abstractmethod
    def Save(self, document_name,content):
        pass
    @abstractmethod
    def Get(self,document_name):
        pass
   
   