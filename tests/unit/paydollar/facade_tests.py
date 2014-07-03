import urlparse

from decimal import Decimal as D
from unittest import TestCase

from mock import patch, Mock
from purl import URL
from oscar.apps.shipping.methods import Free

from asiapay.models import PaydollarTransaction as Transaction
from asiapay.paydollar.facade import get_asiapay_url, fetch_transaction_details


class MockedResponseTests(TestCase):
    token = ''
    response_body = ''

    def setUp(self):
        response = Mock()
        response.content = self.response_body
        response.status_code = 200
        with patch('requests.post') as post:
            post.return_value = response
            self.perform_action()
            self.mocked_post = post

    def perform_action(self):
        pass

    def tearDown(self):
        Transaction.objects.all().delete()


class BaseSetPaydollarCheckoutTests(MockedResponseTests):
    def _get_asiapay_params(self):
        return urlparse.parse_qs(self.mocked_post.call_args[0][1])

    def assertAsiapayParamEqual(self, key, value):
        self.assertEqual(self._get_asiapay_params()[key], [value])

    def assertAsiapayParamDoesNotExist(self, key):
        self.assertFalse(key in self._get_asiapay_params())


class SuccessfulSetPaydollarCheckoutTests(BaseSetPaydollarCheckoutTests):
    token = 'EC-6469953681606921P'
    response_body = 'TOKEN=EC%2d6469953681606921P&TIMESTAMP=2012%2d03%2d26T17%3a19%3a38Z&CORRELATIONID=50a8d895e928f&ACK=Success&VERSION=60%2e0&BUILD=2649250'

    def perform_action(self):
        basket = Mock()
        basket.id = 1
        basket.total_incl_tax = D('200')
        basket.all_lines = Mock(return_value=[])
        basket.offer_discounts = []
        basket.voucher_discounts = []
        basket.shipping_discounts = []
        methods = [Free()]
        url_str = get_asiapay_url(basket, methods)
        self.url = URL.from_string(url_str)

    def test_url_has_correct_keys(self):
        self.assertTrue(self.url.has_query_param('token'))
        self.assertTrue('_paydollar-checkout', self.url.query_param('cmd'))

    def test_corrent_asiapay_params(self):
        for param in [
                'LOCALECODE', 'HDRIMG', 'LANDINGPAGE',
                'REQCONFIRMSHIPPING', 'PAGESTYLE', 'SOLUTIONTYPE',
                'BRANDNAME', 'CUSTOMERSERVICENUMBER'
            ]:
            self.assertAsiapayParamDoesNotExist(param)

        # defaults
        self.assertAsiapayParamEqual('CALLBACKTIMEOUT', '3')
        self.assertAsiapayParamEqual('ALLOWNOTE', '1')


class ExtraAsiapaySuccessfulSetPaydollarCheckoutTests(BaseSetPaydollarCheckoutTests):
    token = 'EC-6469953681606921P'
    response_body = 'TOKEN=EC%2d6469953681606921P&TIMESTAMP=2012%2d03%2d26T17%3a19%3a38Z&CORRELATIONID=50a8d895e928f&ACK=Success&VERSION=60%2e0&BUILD=2649250'

    asiapay_params = {
            'CUSTOMERSERVICENUMBER': '999999999',
            'SOLUTIONTYPE': 'Mark',
            'LANDINGPAGE': 'Login',
            'BRANDNAME': 'My Brand Name',
            'PAGESTYLE': 'eee',
            'HDRIMG': 'http://image.jpg',
            'LOCALECODE': 'GB',
            'REQCONFIRMSHIPPING': True,
            'ALLOWNOTE': False,
            'CALLBACKTIMEOUT': 2
        }

    def perform_action(self):
        basket = Mock()
        basket.id = 1
        basket.total_incl_tax = D('200')
        basket.all_lines = Mock(return_value=[])
        basket.offer_discounts = []
        basket.voucher_discounts = []
        basket.shipping_discounts = []
        methods = [Free()]
        url_str = get_asiapay_url(basket, methods, asiapay_params=self.asiapay_params)
        self.url = URL.from_string(url_str)

    def test_corrent_asiapay_params(self):
        self.assertTrue(self.url.has_query_param('token'))
        self.assertTrue('_paydollar-checkout', self.url.query_param('cmd'))
        for key, value in self.asiapay_params.iteritems():
            if isinstance(value, bool):
                value = int(value)
            self.assertAsiapayParamEqual(key, str(value))


class SuccessfulGetPaydollarCheckoutTests(MockedResponseTests):
    token = 'EC-9LW34435GU332960W'
    response_body = 'TOKEN=EC%2d6WY34243AN3588740&CHECKOUTSTATUS=PaymentActionCompleted&TIMESTAMP=2012%2d04%2d19T10%3a07%3a46Z&CORRELATIONID=7e9c5efbda3c0&ACK=Success&VERSION=88%2e0&BUILD=2808426&EMAIL=david%2e_1332854868_per%40gmail%2ecom&PAYERID=7ZTRBDFYYA47W&PAYERSTATUS=verified&FIRSTNAME=David&LASTNAME=Winterbottom&COUNTRYCODE=GB&SHIPTONAME=David%20Winterbottom&SHIPTOSTREET=1%20Main%20Terrace&SHIPTOCITY=Wolverhampton&SHIPTOSTATE=West%20Midlands&SHIPTOZIP=W12%204LQ&SHIPTOCOUNTRYCODE=GB&SHIPTOCOUNTRYNAME=United%20Kingdom&ADDRESSSTATUS=Confirmed&CURRENCYCODE=GBP&AMT=33%2e98&SHIPPINGAMT=0%2e00&HANDLINGAMT=0%2e00&TAXAMT=0%2e00&INSURANCEAMT=0%2e00&SHIPDISCAMT=0%2e00&PAYMENTREQUEST_0_CURRENCYCODE=GBP&PAYMENTREQUEST_0_AMT=33%2e98&PAYMENTREQUEST_0_SHIPPINGAMT=0%2e00&PAYMENTREQUEST_0_HANDLINGAMT=0%2e00&PAYMENTREQUEST_0_TAXAMT=0%2e00&PAYMENTREQUEST_0_INSURANCEAMT=0%2e00&PAYMENTREQUEST_0_SHIPDISCAMT=0%2e00&PAYMENTREQUEST_0_TRANSACTIONID=51963679RW630412N&PAYMENTREQUEST_0_INSURANCEOPTIONOFFERED=false&PAYMENTREQUEST_0_SHIPTONAME=David%20Winterbottom&PAYMENTREQUEST_0_SHIPTOSTREET=1%20Main%20Terrace&PAYMENTREQUEST_0_SHIPTOCITY=Wolverhampton&PAYMENTREQUEST_0_SHIPTOSTATE=West%20Midlands&PAYMENTREQUEST_0_SHIPTOZIP=W12%204LQ&PAYMENTREQUEST_0_SHIPTOCOUNTRYCODE=GB&PAYMENTREQUEST_0_SHIPTOCOUNTRYNAME=United%20Kingdom&PAYMENTREQUESTINFO_0_TRANSACTIONID=51963679RW630412N&PAYMENTREQUESTINFO_0_ERRORCODE=0'

    def perform_action(self):
        self.txn = fetch_transaction_details(self.token)

    def test_token_is_extracted(self):
        self.assertEqual(self.token, self.txn.token)

    def test_is_successful(self):
        self.assertTrue(self.txn.is_successful)

    def test_ack(self):
        self.assertEqual('Success', self.txn.ack)

    def test_amount_is_saved(self):
        self.assertEqual(D('33.98'), self.txn.amount)

    def test_currency_is_saved(self):
        self.assertEqual('GBP', self.txn.currency)

    def test_correlation_id_is_saved(self):
        self.assertEqual('7e9c5efbda3c0', self.txn.correlation_id)

    def test_context(self):
        ctx = self.txn.context
        values = [
            ('ACK', ['Success']),
            ('LASTNAME', ['Winterbottom']),
        ]
        for k, v in values:
            self.assertEqual(v, ctx[k])
