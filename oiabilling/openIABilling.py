from kivy.app import App
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.properties import *
from kivy.logger import Logger

from jnius import autoclass, PythonJavaClass, java_method, cast
from android import activity
from android.runnable import run_on_ui_thread
from functools import partial

PythonActivity = autoclass('org.kivy.android.PythonActivity')
mactivity = PythonActivity.mActivity

OpenIabHelper = autoclass('org.onepf.oms.OpenIabHelper')
Options = autoclass('org.onepf.oms.OpenIabHelper$Options')
Builder = autoclass('org.onepf.oms.OpenIabHelper$Options$Builder')

DEBUG=True

# since our callbacks from Java don't keep their Python
# from getting GC'd, we have to keep refs
_refs = []

# we remove refs when they are called to allow gc
def _allow_gc(fn):
    def checked(self, *args, **kwargs):
            fn(self, *args, **kwargs)
            _refs.remove(self)
    return checked

def _protect_callback(new_callback):
    '''increment counter and attach to new callback object'''
    _refs.append(new_callback)


# Java callbacks that call back into the provided Python callbacks
class _OnIabSetupFinishedListener(PythonJavaClass):
    __javainterfaces__ = ['org.onepf.oms.appstore.googleUtils.IabHelper$OnIabSetupFinishedListener']
    __javacontext__ = 'app'

    def __init__(self, callback):
        self.callback = callback
        super(_OnIabSetupFinishedListener, self).__init__()

    @java_method('(Lorg/onepf/oms/appstore/googleUtils/IabResult;)V')
    @_allow_gc
    def onIabSetupFinished(self, result):
        self.callback(result)

class _QueryInventoryFinishedListener(PythonJavaClass):
    __javainterfaces__ = ['org.onepf.oms.appstore.googleUtils.IabHelper$QueryInventoryFinishedListener']
    __javacontext__ = 'app'

    def __init__(self, callback):
        self.callback = callback
        super(_QueryInventoryFinishedListener, self).__init__()

    @java_method('(Lorg/onepf/oms/appstore/googleUtils/IabResult;Lorg/onepf/oms/appstore/googleUtils/Inventory;)V')
    @_allow_gc
    def onQueryInventoryFinished(self, result, inventory):
        self.callback(result, inventory)

class _OnPurchaseFinishedListener(PythonJavaClass):
    ''' This one seems to blow up inside the IabHelper OnActivityResult'''
    __javainterfaces__ = ['org.onepf.oms.appstore.googleUtils.IabHelper$OnIabPurchaseFinishedListener']
    __javacontext__ = 'app'

    def __init__(self, callback):
        self.callback = callback
        super(_OnPurchaseFinishedListener, self).__init__()

    @java_method('(Lorg/onepf/oms/appstore/googleUtils/IabResult;Lorg/onepf/oms/appstore/googleUtils/Purchase;)V')
    @_allow_gc
    def onIabPurchaseFinished(self, result, purchase):
        self.callback(result, purchase)

class _OnConsumeFinishedListener(PythonJavaClass):
    __javainterfaces__ = ['org.onepf.oms.appstore.googleUtils.IabHelper$OnConsumeFinishedListener']
    __javacontext__ = 'app'

    def __init__(self, callback):
        self.callback = callback
        super(_OnConsumeFinishedListener, self).__init__()

    @java_method('(Lorg/onepf/oms/appstore/googleUtils/Purchase;Lorg/onepf/oms/appstore/googleUtils/IabResult;)V')
    @_allow_gc
    def onConsumeFinished(self, purchase, result):
        self.callback(purchase, result)

#############################################
class OpenIABilling(EventDispatcher):
    consumed = DictProperty()
    helper = ObjectProperty(None)
    setup_complete = BooleanProperty(False)
    skus = ListProperty(None)
    consumable=ListProperty([])
    r_code=NumericProperty(12347)
    
    def __init__(self, skus,confFile,**kwargs):
        self.skus = skus
        #FIXME:for now, the config is done in the java part
        Config = autoclass(confFile)

        Logger.info("Creating IAB helper."+50*'-')
        builder = Builder()
        builder.setVerifyMode(Options.VERIFY_EVERYTHING)
        #builder.addStoreKeys
        builder.setStoreSearchStrategy(Options.SEARCH_STRATEGY_INSTALLER)
        builder.addStoreKey(OpenIabHelper.NAME_GOOGLE, Config.GOOGLE_PLAY_KEY)
        self.helper = OpenIabHelper(mactivity, builder.build())
        self.helper.enableDebugLogging(DEBUG)
        Logger.info("Creating IAB done.")
        s = _OnIabSetupFinishedListener(self._setup_finished)
        Logger.info("OnIabSetupFinishedListener.")
        _protect_callback(s)
        
        
        self._helper_setup(s)
        
        Logger.info("END __INIT__.")
    
    @run_on_ui_thread
    def _helper_setup(self, s):
        self.helper.startSetup(s)

    def setConsumable(self,sku):
        if sku in self.skus and sku not in self.consumable:
            self.consumable.append(sku)

    def isConsumable(self,sku):
        if sku in self.skus:
            return sku in self.consumable
        return False
           
    def purchase(self, sku):
        Logger.info('Purchasing %s item...'%sku)
        if not self.setup_complete:
            Logger.info('setup not complete')
            #self._setup()
        else:
            Logger.info('doing the purchase')
            if sku not in self.skus:
                raise AttributeError('The sku is not in the skus you initialized with')
            Logger.info('Starting purchase workflow for ' + sku)
            c = cast('android.app.Activity', mactivity)
            p = _OnPurchaseFinishedListener(self._purchase_finished)
            _protect_callback(p)
            self.helper.launchPurchaseFlow(c, sku, self.r_code, p)
        return True

    def consume(self,sku):
        p = self.inventory.getPurchase(sku)
        self._consume(p)
        
    #PRIVATE METHODS
    def _setup_finished(self, result):
        if result.isSuccess():
            Logger.info('Setup complete. Scheduling inventory check!')
            self.setup_complete = True
            a = App.get_running_app()
            a.bind(on_stop=self._dispose)
            activity.bind(on_activity_result=self._on_activity_result) 
            self._get_inventory()
        else:
            Logger.info('There was a problem with setup...')
            
    def _on_activity_result(self, requestCode, responseCode, Intent):
        # Bound in _setup_callback to activity.on_activity_result
        if DEBUG:
            Logger.info('Request Code: ' + str(requestCode))
            Logger.info('Expected Code: ' + str(self.r_code))
        if requestCode == self.r_code:
            #Logger.info('Passing result to IAB helper')
            #FIXME: handleActivityResult cause app crashing when activity resumed while purchase has benn user cancelled...
            # so I just launch _get_inventory to do the job.
            
            #if self.helper.handleActivityResult(requestCode, responseCode, Intent):
            #    Logger.info('Helper completed the request.')
            self._get_inventory()
        return True
            
    def _get_inventory(self, *args):
        Logger.info('Getting Inventory.')
        q = _QueryInventoryFinishedListener(self._got_inventory_callback)
        _protect_callback(q)
        self.helper.queryInventoryAsync(q)

    def _got_inventory_callback(self, result, inventory):
        if result.isSuccess():
            Logger.info('Got Inventory')
            self.inventory = inventory
            for i in self.skus:
                if inventory.hasPurchase(i):
                    currentPurchase = inventory.getPurchase(i)
                    Logger.info("CHECKING %s"%i)
                    Logger.info("SKU details:%s"%inventory.getSkuDetails(i))
                    if self._verifyDeveloperPayload(currentPurchase):
                        self.consumed[i] = True
            Logger.info('In inventory:')
        else:
            Logger.info('Could not check inventory')
            Logger.info(result.toString())
            
    def _verifyDeveloperPayload(self,purchase):
        if purchase:
            return True    
 
    def _purchase_finished(self, result, purchase):
        Logger.info('Result was ' + str(result.isSuccess()) + ' for ' + 
                    purchase.getSku())
        if result.isSuccess():
            self.consumed[purchase.getSku()]=True
            self._consume(purchase)

    def _consume(self, purchase):
        if purchase.getSku() in self.consumable:
            Logger.info('Consuming ' + purchase.getSku())
            c = _OnConsumeFinishedListener(self._consume_finished)
            _protect_callback(c)
            self.helper.consumeAsync(purchase, c)

    def _consume_finished(self, purchase, result):
        try:
            s = str(purchase.getSku())
        except:
            s = 'unknown sku'
        if result.isSuccess():
            self.consumed[s] = False
            Logger.info(s + ' was successfully purchased.  Time to get rich!')
        else:
            Logger.info('There was a problem consuming ' + s)
        
    def _dispose(self, *args):
        ''' Let all callbacks be GC'd and destroy helper'''
        self.helper.dispose()
        global _refs
        _refs = []
