"""
Responsible for briding between Oscar and the AsiaPay gateway
"""
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .models import PaydollarTransaction as Transaction
from .gateway import (
    set_txn, get_txn, do_txn, SALE, AUTHORIZATION, ORDER,
    do_capture, DO_PAYDOLLAR_CHECKOUT, do_void
)


def _get_payment_action():
    # AsiaPay supports 3 actions: 'Sale', 'Authorization', 'Order'
    action = getattr(settings, 'ASIAPAY_PAYMENT_ACTION', SALE)
    if action not in (SALE, AUTHORIZATION, ORDER):
        raise ImproperlyConfigured(
            "'%s' is not a valid payment action" % action)
    return action


def get_asiapay_url(basket, shipping_methods, user=None, shipping_address=None,
                    shipping_method=None, host=None, scheme=None):
    """
    Return the URL for a AsiaPay Paydollar transaction.

    This involves registering the txn with AsiaPay to get a one-time
    URL.  If a shipping method and shipping address are passed, then these are
    given to AsiaPay directly - this is used within when using AsiaPay as a
    payment method.
    """
    currency = getattr(settings, 'ASIAPAY_CURRENCY', 'GBP')
    if host is None:
        host = Site.objects.get_current().domain
    if scheme is None:
        use_https = getattr(settings, 'ASIAPAY_CALLBACK_HTTPS', True)
        scheme = 'https' if use_https else 'http'
    success_url = '%s://%s%s' % (
        scheme, host, reverse('asiapay-success-response', kwargs={
            'basket_id': basket.id}))
    fail_url = '%s://%s%s' % (
        scheme, host, reverse('asiapay-fail-response', kwargs={
            'basket_id': basket.id}))

    # URL for updating shipping methods - we only use this if we have a set of
    # shipping methods to choose between.
    update_url = None
    if shipping_methods:
        update_url = '%s://%s%s' % (
            scheme, host,
            reverse('asiapay-shipping-options',
                    kwargs={'basket_id': basket.id}))

    # Determine whether a shipping address is required
    no_shipping = False
    if not basket.is_shipping_required():
        no_shipping = True

    # Pass a default billing address is there is one.  This means AsiaPay can
    # pre-fill the registration form.
    address = None
    if user:
        addresses = user.addresses.all().order_by('-is_default_for_billing')
        if len(addresses):
            address = addresses[0]

    return set_txn(basket=basket,
                   shipping_methods=shipping_methods,
                   currency=currency,
                   success_url=success_url,
                   fail_url=fail_url,
                   update_url=update_url,
                   action=_get_payment_action(),
                   shipping_method=shipping_method,
                   shipping_address=shipping_address,
                   user=user,
                   user_address=address,
                   no_shipping=no_shipping)


def fetch_transaction_details(token):
    """
    Fetch the completed details about the AsiaPay transaction.
    """
    return get_txn(token)


def confirm_transaction(payer_id, token, amount, currency):
    """
    Confirm the payment action.
    """
    return do_txn(payer_id, token, amount, currency,
                  action=_get_payment_action())


def capture_authorization(token, note=None):
    """
    Capture a previous authorization.
    """
    txn = Transaction.objects.get(token=token,
                                  method=DO_PAYDOLLAR_CHECKOUT)
    return do_capture(txn.value('TRANSACTIONID'),
                      txn.amount, txn.currency, note=note)


def void_authorization(token, note=None):
    """
    Void a previous authorization.
    """
    txn = Transaction.objects.get(token=token,
                                  method=DO_PAYDOLLAR_CHECKOUT)
    return do_void(txn.value('TRANSACTIONID'), note=note)
