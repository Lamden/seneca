from seneca.engine.interface import SenecaInterface
import types


def default_driver():
    return SenecaInterface(concurrent_mode=False,
                           development_mode=True,
                           port=6379,
                           password='')



class SenecaFunction:
    def __init__(self, name, module_path, kwargs, author, default_sender, driver):
        self.name = name
        self.module_path = module_path
        self.kwargs = kwargs
        self.defaults = {
            'author': author,
            'sender': default_sender
        }
        self.driver = driver

    def __call__(self, *args, **kwargs):

        def default(d, k):
            return d if kwargs.get(k) is None else kwargs.get(k)

        stamps = default(None, 'stamps')
        author = default(self.defaults.get('author'), 'author')
        sender = default(self.defaults.get('sender'), 'sender')

        r = self.driver.execute_function(
            module_path=self.module_path,
            stamps= stamps,
            author= author,
            sender= sender,
            **kwargs
        )

        return r


class ContractWrapper:
    def __init__(self, contract_name=None, driver=default_driver(), default_sender=None):
        self.driver = driver
        self.author = driver.get_contract_meta(contract_name)['author']
        self.default_sender = default_sender
        contract_code = driver.get_code_obj(contract_name)
        codes = [cd for cd in contract_code.co_consts if type(cd) == types.CodeType]
        for _c in codes:
            name = _c.co_name
            module_path = 'seneca.contracts.{}.{}'.format(contract_name, _c.co_name)
            kwargs = _c.co_varnames
            setattr(self, name, SenecaFunction(name=name,
                                               module_path=module_path,
                                               kwargs=kwargs,
                                               author=self.author,
                                               default_sender=self.default_sender,
                                               driver=self.driver)
                    )
