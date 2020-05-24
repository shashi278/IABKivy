from kivy import platform

__all__ = ('Billing',)

if platform == 'android':
    from .openIABilling import OpenIABilling as Billing
else:
    from .mockbilling import MockBilling as Billing
