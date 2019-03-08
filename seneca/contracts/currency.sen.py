from seneca.libs.storage.datatypes import Hash, Resource

# Declare Data Types
xrate = Resource()
seed_amount = Resource()
balances = Hash('balances', default_value=0)
allowed = Hash('allowed', default_value=0)

@seed
def seed_wallets():
    # Initialization
    xrate = 1.0
    seed_amount = 1000000
    balances['LamdenReserves'] = 0

    # Deposit to all network founders
    founder_wallets = [
        '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502',
        'a103715914a7aae8dd8fddba945ab63a169dfe6e37f79b4a58bcf85bfd681694',
        '20da05fdba92449732b3871cc542a058075446fedb41430ee882e99f9091cc4d',
        'ed19061921c593a9d16875ca660b57aa5e45c811c8cf7af0cfcbd23faa52cbcd',
        'cb9bfd4b57b243248796e9eb90bc4f0053d78f06ce68573e0fdca422f54bb0d2',
        'c1f845ad8967b93092d59e4ef56aef3eba49c33079119b9c856a5354e9ccdf84'
    ]

    for w in founder_wallets:
        balances[w] = seed_amount


def assert_stamps(stamps):
    # NOTE: This is run first before executing any lines from the core code block. No stamps will be
    #       subtracted if this assertion fails.
    assert balances[rt['origin']] >= stamps, "Not enough funds to submit stamps"


def submit_stamps(stamps):
    # NOTE: Assertion is made before executing the core code block. The exact amount of used stamps is
    #       passed in from the executor as a separate exec() command. This will ensure that even if
    #       the core code block fails, stamps will be subtracted
    stamps *= xrate
    balances[rt['origin']] -= stamps
    balances['LamdenReserves'] += stamps

@export
def transfer(to, amount):
    assert balances[rt['sender']] > 0, '{} <> Sender {} has amount {} but tried to transfer {}. Not enough funds'.format(balances.key, rt['sender'], balances[rt['sender']], amount)
    print("xfering from {} to {} with amount {}".format(rt['sender'], to, amount))
    balances[rt['sender']] -= amount
    balances[to] += amount

@export
def approve(spender, amount):
    allowed[rt['sender']][spender] = amount

@export
def transfer_from(approver, spender, amount):
    assert allowed[approver][spender] >= amount
    assert balances[approver] >= amount
    allowed[approver][spender] -= amount
    balances[approver] -= amount
    balances[spender] += amount

@export
def mint(to, amount):
    # print("minting {} to wallet {}".format(amount, to))
    assert rt['sender'] == rt['author'], 'Only the original contract author can mint!'

    balances[to] += amount