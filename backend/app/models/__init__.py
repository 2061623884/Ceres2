"""Explicit registration of the current canonical schema."""
from app.models.identity import Owner
from app.models.catalog import CatalogProduct
from app.models.store import Offer, Store
from app.models import guide
from app.mercury.models import MercuryCase, SimulatedOrder
from app.models.cart import Cart, CartItem
from app.models.checkout import CheckoutPreview, CheckoutReceipt
from app.human.models import HumanTicket, HumanHandoffState
from app.mercury.aftersales_models import AfterSalesProposal, AfterSalesApplication, AfterSalesReceipt
from app.models.purchase import PurchaseConfirmation, PurchaseLedger
from app.models.memory import ShoppingMemory
from app.models.comparison import ComparisonDisplay
