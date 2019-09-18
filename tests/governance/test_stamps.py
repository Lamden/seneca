from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td

def stamps():
    import election_house

    S = Hash()

    ELECTION_INTERVAL = datetime.DAYS * 3
    VOTING_PERIOD = datetime.DAYS * 1

    @construct
    def seed(initial_rate):
        S['rate'] = initial_rate
        reset()

    @export
    def current_value():
        return S['rate']

    @export
    def vote(vk, obj):
        # Check to make sure that there is an election
        if S['in_election']:
            assert_vote_is_valid(vk, obj)
            S['votes', vk] = obj

            if now - S['election_start_time'] >= VOTING_PERIOD:
                # Tally votes and set the new value
                result = median(S['votes'].all())
                S['rate'] = result

                reset()
        else:
            # If there isn't, it might be time for a new one, so start it if so.
            # You can then submit your vote as well.
            if now - S['last_election_end_time'] > ELECTION_INTERVAL:
                # Start the election and set the proper variables
                S['election_start_time'] = now
                S['in_election'] = True

                assert_vote_is_valid(vk, obj)
                S['votes', vk] = obj
            else:
                raise Exception('Outside of governance parameters.')

    def assert_vote_is_valid(vk, obj):
        current_rate = S['rate']
        assert type(obj) == int, 'Vote is not an int'
        assert current_rate / 2 <= obj <= current_rate * 2, 'Proposed rate is not within proper boundaries.'

        masternode_policy = election_house.current_value_for_policy(policy='masternodes')

        assert vk in masternode_policy['masternodes'], 'VK is not a masternode!'
        assert S['vote', vk] is None, 'VK already voted!'

    def median(vs):
        sorted_votes = sorted(vs)
        index = (len(sorted_votes) - 1) // 2

        if len(sorted_votes) % 2:
            return sorted_votes[index]
        else:
            return (sorted_votes[index] + sorted_votes[index + 1]) / 2

    def reset():
        S['last_election_end_time'] = now
        S['in_election'] = False
        S.clear('votes')


class TestStamps(TestCase):
    def setUp(self):
        self.client = ContractingClient()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='election_house')
        self.election_house = self.client.get_contract('election_house')

        with open('./contracts/masternodes.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='masternodes', owner='election_house', constructor_args={
            'initial_masternodes': [
                'stu', 'raghu', 'alex'
            ],
            'initial_open_seats': 0
        })

        self.election_house.register_policy(policy='masternodes', contract='masternodes')

        self.masternodes = self.client.get_contract('masternodes')

    def tearDown(self):
        self.client.flush()

    def test_init(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        self.assertEqual(stamps_contract.current_value(), 10000)

    def test_vote_is_not_int_fails(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        with self.assertRaises(AssertionError):
            stamps_contract.run_private_function(
                f='assert_vote_is_valid',
                vk='sys',
                obj='a'
            )

    def test_vote_is_less_than_half_current_rate_fails(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        with self.assertRaises(AssertionError):
            stamps_contract.run_private_function(
                f='assert_vote_is_valid',
                vk='sys',
                obj=4000
            )

    def test_vote_is_greater_than_double_current_rate_fails(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        with self.assertRaises(AssertionError):
            stamps_contract.run_private_function(
                f='assert_vote_is_valid',
                vk='sys',
                obj=40000
            )

    def test_vk_is_not_masternode_fails(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        with self.assertRaises(AssertionError):
            stamps_contract.run_private_function(
                f='assert_vote_is_valid',
                vk='sys',
                obj=12000
            )

    def test_vote_works_if_vk_in_range_etc(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        stamps_contract.run_private_function(
            f='assert_vote_is_valid',
            vk='stu',
            obj=12000
        )

    def test_vk_has_already_voted_fails(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        stamps_contract.quick_write('S', 'votes', args=['stu'], value=123)

        with self.assertRaises(AssertionError):
            stamps_contract.run_private_function(
                f='assert_vote_is_valid',
                vk='stu',
                obj=12000
            )

    def test_median_performs_properly_on_even_lists(self):
        a = [12, 62, 16, 24, 85, 41, 84, 13, 1999, 47, 27, 43]
        expected = 42

        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        got = stamps_contract.run_private_function(
            f='median',
            vs=a,
        )

        self.assertEqual(expected, got)

    def test_median_performs_properly_on_odd_lists(self):
        a = [92, 73, 187, 2067, 10, 204, 307, 24, 478, 23, 11]
        expected = 92

        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        got = stamps_contract.run_private_function(
            f='median',
            vs=a,
        )

        self.assertEqual(expected, got)

    def test_reset_works(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        stamps_contract.quick_write('S', 'votes', value=123, args=['id1'])
        stamps_contract.quick_write('S', 'votes', value=124, args=['id2'])
        stamps_contract.quick_write('S', 'votes', value=125, args=['id3'])
        stamps_contract.quick_write('S', 'votes', value=126, args=['id4'])
        stamps_contract.quick_write('S', 'votes', value=127, args=['id5'])
        stamps_contract.quick_write('S', 'votes', value=128, args=['id6'])
        stamps_contract.quick_write('S', 'votes', value=129, args=['id7'])
        stamps_contract.quick_write('S', 'votes', value=130, args=['id8'])
        stamps_contract.quick_write('S', 'votes', value=131, args=['id9'])

        stamps_contract.quick_write('S', 'in_election', value=True)
        stamps_contract.quick_write('S', 'last_election_end_time', value='something')

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}
        stamps_contract.run_private_function('reset', environment=env)

        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id1']), None)
        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id2']), None)
        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id3']), None)
        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id4']), None)
        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id5']), None)
        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id6']), None)
        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id7']), None)
        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id8']), None)
        self.assertEqual(stamps_contract.quick_read('S', 'votes', ['id9']), None)

        self.assertEqual(stamps_contract.quick_read('S', 'in_election'), False)
        self.assertEqual(stamps_contract.quick_read('S', 'last_election_end_time'), env['now'])
