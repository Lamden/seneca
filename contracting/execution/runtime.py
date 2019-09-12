from collections import deque
import sys
from .. import config
import contracting
import os
from .metering.tracer import Tracer


class DequeSet:
    def __init__(self, maxlen=config.RECURSION_LIMIT):
        self.d = deque(maxlen=maxlen)

    def push(self, item):
        if len(self.d) == 0 or self.last() != item:
            self.d.append(item)

    def pop(self):
        return self.d.pop()

    def last(self):
        return self.d[-1]

    def clear(self):
        self.d.clear()

    def last_parent(self):
        try:
            return self.d[-2]
        except IndexError:
            return self.d[-1]


class Context:
    def __init__(self, base_state):
        self._state = []
        self._base_state = base_state

    def _context_changed(self, contract):
        if self._get_state()['this'] == contract:
            return False
        return True

    def _get_state(self):
        if len(self._state) == 0:
            return self._base_state
        return self._state[-1]

    def _add_state(self, state: dict):
        if self._context_changed(state['this']):
            self._state.append(state)

    def _pop_state(self):
        if len(self._state) > 0:
            self._state.pop(-1)

    def _reset(self):
        self._state = []

    @property
    def this(self):
        print('getting this')
        return self._get_state()['this']

    @property
    def caller(self):
        print(self._base_state)
        return self._get_state()['caller']

    @property
    def signer(self):
        print('getting signer')
        return self._get_state()['signer']

    @property
    def owner(self):
        print('getting this')
        return self._get_state()['owner']

print('resetting context')
_context = Context({
        'this': None,
        'caller': None,
        'owner': None,
        'signer': None
    })

class Runtime:
    cu_path = contracting.__path__[0]
    cu_path = os.path.join(cu_path, 'execution', 'metering', 'cu_costs.const')

    os.environ['CU_COST_FNAME'] = cu_path

    #ctx = deque(maxlen=config.RECURSION_LIMIT)
    #ctx.append('__main__')

    loaded_modules = []

    env = {}
    stamps = 0

    tracer = Tracer()

    signer = None

    context = _context

    @classmethod
    def set_up(cls, stmps, meter):
        if meter:
            cls.stamps = stmps
            cls.tracer.set_stamp(stmps)
            cls.tracer.start()

        cls.context._reset()

    @classmethod
    def clean_up(cls):
        cls.tracer.stop()
        cls.tracer.reset()
        cls.stamps = 0

        cls.signer = None

        for mod in cls.loaded_modules:
            if sys.modules.get(mod) is not None:
                del sys.modules[mod]

        cls.loaded_modules = []
        cls.env = {}


rt = Runtime()
