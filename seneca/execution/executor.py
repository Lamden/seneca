import multiprocessing
import abc

from seneca.parallelism import book_keeper, conflict_resolution
from seneca.execution import module, runtime

from seneca.db.driver import ContractDriver
#from seneca.metering.tracer import Tracer


class Executor:

    def __init__(self, metering=True, concurrency=True, flushall=False, production=False):
        # Colin - Load in the database driver from the global config
        #         Set driver_proxy to none to indicate it exists and
        #         may be filled later
        self.driver_base = ContractDriver()
        self.driver_proxy = None
        if flushall:
            self.driver.flush()

        # Colin - Load in the parameters for the default contracts
        #         NOTE: Not sure this belongs here at all (should
        #               be happening in bootstrap most likely).
        #self.path = join(seneca.__path__[0], 'contracts')
        #self.author = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
        #self.official_contracts = OFFICIAL_CONTRACTS
        #self.setup_official_contracts()

        # Setup whether or not flags have been set
        self.metering = metering
        self.concurrency = concurrency

        # Colin -  Setup the tracer
        # Colin TODO: Find out why Tracer is not instantiating properly. Raghu also said he wants to pull this out.
        #cu_cost_fname = join(seneca.__path__[0], 'constants', 'cu_costs.const')
        #self.tracer = Tracer(cu_cost_fname)
        self.tracer = None

        if production:
            self.sandbox = SingleProcessSandbox()
        else:
            self.sandbox = LocalSandbox()

    @property
    # Colin - I don't understand what this property is for, why
    #         do we need a driver_proxy for CR, we should not be
    #         instantiating drivers all over the place.
    def driver(self):
        if self.concurrency:
            if not self.driver_proxy:
                info = book_keeper.BookKeeper.get_cr_info()
                self.driver_proxy = conflict_resolution.StateProxy(sbb_idx=info['sbb_idx'], contract_idx=info['contract_idx'],
                                               data=info['data'])
            else:
                info = book_keeper.BookKeeper.get_cr_info()
                self.driver_proxy.sbb_idx = info['sbb_idx']
                self.driver_proxy.contract_idx = info['contract_idx']
                self.driver_proxy.data = info['data']
            return self.driver_proxy
        else:
            return self.driver_base


    def execute_bag(self, bag):
        """
        The execute bag method sends a list of transactions to the sandbox to be executed

        :param bag: a list of deserialized transaction objects
        :return: a list of results (result index == bag index)
        """
        return self.sandbox.execute_bag(bag)

    def execute(self, sender, code_str):
        """
        Method that does a naive execute

        :param sender:
        :param code_str:
        :return:
        """
        return self.sandbox.execute(sender, code_str)



class AbstractSandbox:
    __metaclass__ = abc.ABCMeta
    """
    The Sandbox class is used as a execution sandbox for a transaction.

    I/O pattern:

        ------------                                  -----------
        | Executor |  ---> Transaction Bag (all) ---> | Sandbox |
        ------------                                  -----------
                                                           |
        ------------                                       v
        | Executor |  <---      Send Results     <---  Execute all tx
        ------------

        * The client sends the whole transaction bag to the Sandbox for
          processing. This is done to minimize back/forth I/O overhead
          and deadlocks
        * The sandbox executes all of the transactions one by one, resetting
          the syspath after each execution.
        * After all execution is complete, pass the full set of results
          back to the client again to minimize I/O overhead and deadlocks
        * Sandbox blocks on pipe again for new bag of transactions
    """
    @abc.abstractmethod
    def execute_bag(self, bag):
        return

    @abc.abstractmethod
    def execute(self, sender, code_str):
        return

    @staticmethod
    def _execute(sender, code_str):
        runtime.rt.ctx.pop()
        runtime.rt.ctx.append(sender)
        env = {}
        module = exec(code_str, env)
        return module, env


class LocalSandbox(AbstractSandbox):
    def __init__(self):
        pass

    def execute_bag(self, bag):
        pass

    def execute(self, sender, code_str):
        return self._execute(sender, code_str)


class SingleProcessSandbox(AbstractSandbox):
    def __init__(self):
        self._p_out, self._p_in = multiprocessing.Pipe()
        self._p = SandboxProcess((self._p_out, self._p_in), self._execute)
        self._p.start()

    def execute_bag(self, bag):
        pass

    def execute(self, sender, code_str):
        self._p_in.send((sender, code_str))
        return self._p_out.recv()


class SandboxProcess(multiprocessing.Process):
    def __init__(self, pipe, execute_fn):
        super(SandboxProcess, self).__init__()
        self._p_out, self._p_in = pipe
        self.execute = execute_fn

    def run(self):
        while True:
            sender, code_str = self._p_out.recv()
            self._p_in.send(self.execute(sender, code_str))

