from unittest import TestCase
from seneca.db.driver import CacheDriver


class TestCacheDriver(TestCase):
    def setUp(self):
        self.c = CacheDriver()
        self.c.conn.flushdb()

    def tearDown(self):
        self.c.conn.flushdb()

    def test_get_from_db_if_not_in_modified_keys(self):
        self.c.conn.set('test', 'val1')

        val = self.c.get('test')
        self.assertEqual(val, b'val1')

    def test_get_from_contract_modification_if_already_set(self):
        update = {'test': 'val2'}
        self.c.contract_modifications.append(update)
        self.c.modified_keys.update({'test': 0})

        self.c.conn.set('test', 'val1')

        val = self.c.get('test')

        self.assertEqual(val, 'val2')

    def test_get_from_contract_modification_chains(self):
        update = {'test': 'val2', 'stu': 1234, 'colin': 0}
        self.c.contract_modifications.append(update)
        self.c.modified_keys.update({'test': 0, 'stu': 1234, 'colin': 0})

        update = {'test': 'val3'}
        self.c.contract_modifications.append(update)
        self.c.modified_keys.update({'test': 1})

        update = {'stu': 500000}
        self.c.contract_modifications.append(update)
        self.c.modified_keys.update({'stu': 2})

        update = {'colin': 1000000}
        self.c.contract_modifications.append(update)
        self.c.modified_keys.update({'colin': 3})

        self.assertEqual(self.c.get('test'), 'val3')
        self.assertEqual(self.c.get('stu'), 500000)
        self.assertEqual(self.c.get('colin'), 1000000)

    def test_basic_set_writes_to_contract_modifications_and_modified_keys(self):
        self.c.set('stu', 'farm')
        self.c.set('col', 'bro')
        self.c.set('raghu', 'set')

        self.assertDictEqual(self.c.modified_keys, {'stu': 0, 'col': 0, 'raghu': 0})
        self.assertDictEqual(self.c.contract_modifications[-1], {'stu': 'farm', 'col': 'bro', 'raghu': 'set'})

    def test_new_tx_adds_length_to_contract_modifications(self):
        self.c.new_tx()
        self.assertEqual(len(self.c.contract_modifications), 2)

    def test_new_tx_creates_new_key_space(self):
        self.c.set('stu', 'farm')
        self.c.set('col', 'bro')
        self.c.set('raghu', 'set')

        self.c.new_tx()

        self.c.set('col', 'orb')
        self.c.set('raghu', 'tes')

        self.assertDictEqual(self.c.modified_keys, {'stu': 0, 'col': 1, 'raghu': 1})

    def test_new_tx_creates_new_key_space_and_gets_correct_keys(self):
        self.c.set('stu', 'farm')
        self.c.set('col', 'bro')
        self.c.set('raghu', 'set')

        self.c.new_tx()

        self.c.set('col', 'orb')
        self.c.set('raghu', 'tes')

        self.assertEqual(self.c.get('raghu'), 'tes')
        self.assertEqual(self.c.get('stu'), 'farm')
        self.assertEqual(self.c.get('col'), 'orb')
