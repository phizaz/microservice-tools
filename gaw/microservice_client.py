from __future__ import print_function, absolute_import
from gaw.jsonsocketserver import JsonSocketClient

class MicroserviceClient:

    def __init__(self, ip, port, connection_lifetime = 30, verbose=False,
                 request_maker=None,
                 _state=0, _service_name=None, _method_name=None):
        self.ip = ip
        self.port = port
        self.connection_lifetime = connection_lifetime
        self.verbose = verbose

        if request_maker is None:
            self.request_maker = JsonSocketClient(client_lifetime=connection_lifetime, verbose=verbose)
        else:
            self.request_maker = request_maker

        self._state = _state
        self._service_name = _service_name
        self._method_name = _method_name

    def __getattr__(self, item):
        if self._state == 0:
            state = 1
            service_name = item

            return MicroserviceClient(
                ip=self.ip, port=self.port,
                connection_lifetime=self.connection_lifetime,
                verbose=self.verbose,
                request_maker=self.request_maker,
                _state=state,
                _service_name=service_name,
                _method_name=self._method_name
            )
        elif self._state == 1:
            method_name = item

            return self.get_procedure_caller(
                service_name=self._service_name,
                method_name=method_name,
                ip=self.ip,
                port=self.port,
                request_maker=self.request_maker,
                verbose=self.verbose
            )
        else:
            raise ValueError('state not recognized')

    def get_procedure_caller(self, service_name, method_name,
                             ip, port, request_maker, verbose):
        assert isinstance(request_maker, JsonSocketClient), 'request maker should be a jsonsocketclient'
        path = '{}/{}'.format(service_name, method_name)

        def rpc(*args, **kwargs):
            if verbose:
                print('microservice client: procedure call path', path, 'args:', args, 'kwargs:', kwargs)

            return request_maker.request(ip=ip, port=port, path=path,
                                         payload=dict(
                                             args=args,
                                             kwargs=kwargs
                                         ))
        return rpc
