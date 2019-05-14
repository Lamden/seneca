from unittest import TestCase
from contracting.webserver import app


class TestTimedelta(TestCase):
    def test_ping_api(self):
        _, response = app.test_client.get('/')
        self.assertEqual(response.status, 418)

    def test_get_all_contracts(self):
        _, response = app.test_client.get('/contracts')
        contracts = response.json.get('contracts')
        self.assertListEqual(['submission'], contracts)

    def test_get_submission_code(self):
        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        _, response = app.test_client.get('/contracts/submission')

        code = response.json.get('code')

        self.assertEqual(contract, code)

    def test_get_submission_methods(self):
        _, response = app.test_client.get('/contracts/submission/methods')

        method = 'submit_contract'
        kwargs = ['name', 'code']

        methods = response.json.get('methods')

        self.assertEqual(len(methods), 1)

        test_method = methods[0]

        self.assertEqual(method, test_method.get('name'))

        self.assertListEqual(kwargs, test_method.get('arguments'))