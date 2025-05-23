from abc import ABC, abstractmethod

class STInterface(ABC):
    @abstractmethod
    def Get(self,document_name):
        pass
    @abstractmethod
    def Save(self, document_path, content):
        pass