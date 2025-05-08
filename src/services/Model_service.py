from src.interfaces.di_interface import DocIntInterface
import logging
from collections import defaultdict
from datetime import datetime

class ModelService:

    def __init__(self,azure_di:DocIntInterface):
        self.azure_di = azure_di

    def process(self,filestream):
        result = self.azure_di.Process(filestream=filestream)
        return result
    