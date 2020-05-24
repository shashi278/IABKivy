from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.properties import *
from kivy.logger import Logger


class MockBilling(EventDispatcher):
    consumed = DictProperty()
    setup_complete = BooleanProperty(False)
    skus = ListProperty(None)
    consumable=ListProperty(None)

    def __init__(self, skus,confFile, *args, **kwargs):
        super(MockBilling, self).__init__(*args, **kwargs)
        self.skus = skus

    def setConsumable(self,sku):
        if sku in self.skus and sku not in self.consumable:
            self.consumable.append(sku)

    def isConsumable(self,sku):
        if sku in self.skus:
            return sku in self.consumable
        return False
    
    def purchase(self, sku):
        self.consumed[sku]=True

    def consume(self,sku):
        if sku in self.consumable:
            self.consumed[sku]=False
