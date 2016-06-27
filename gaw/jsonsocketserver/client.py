from __future__ import print_function, absolute_import
from gaw.jsonsocketserver.datatype import RequestDataType, ResponseDataType
from gaw.postoffice import PostofficeClient
from threading import Thread
import uuid
import datetime
import time
import eventlet

class JsonSocketClient:

    def __init__(self, client_lifetime=30, verbose=False):
        self.client_lifetime = client_lifetime
        self.verbose = verbose

        self._client_pool = dict()
        self._is_busy = dict()
        self._last_act_at = dict()

        self._cleaner = Thread(target=self._cleaner)
        self._cleaner.daemon = True
        self._cleaner.start()

    def request(self, ip, port, path, payload):
        # may retry many times
        while True:
            client = self._get_client(ip, port)
            assert isinstance(client, PostofficeClient)

            if self.verbose:
                print('jsonsocketclient: requesting ip', ip, 'port', port, 'path', path, 'payload', payload)

            request = RequestDataType(id=uuid.uuid1().int,
                                      path=path,
                                      payload=payload)

            try:
                raw_response = client.send(request.dict())
            except Exception as err:
                print('jsonsocketclient: connection error retrying ...')
                # delete the old client
                self._delete(self._key(ip, port))
                eventlet.sleep(1)
                # retry
                continue

            if self.verbose:
                print('jsonsocketclient: response ', raw_response)

            response = ResponseDataType.parse(raw_response)

            if response.resp_to != request.id:
                raise ValueError('request error: wrong response id')

            if not response.success:
                exception = response.payload
                type = exception['type']
                name = exception['name']
                message = exception['message']
                trace = exception['trace']
                raise Exception('\ntype: {}\nname: {}\nmessage: {}\ntrace: {}'.format(type, name, message, trace))

            return response.payload

    # private
    def _key(self, ip, port):
        return '{}:{}'.format(ip, port)

    def _init_client(self, ip, port):
        while True:
            try:
                return PostofficeClient(ip, port, verbose=self.verbose)
            except Exception:
                print('jsonsocketclient: host is down retrying ...')
                eventlet.sleep(5)

    def _get_client(self, ip, port):
        key = self._key(ip, port)

        if key not in self._client_pool:
            self._client_pool[key] = self._init_client(ip, port)

        self._last_act_at[key] = datetime.datetime.now()
        self._is_busy[key] = True

        return self._client_pool[key]

    def _return_client(self, ip, port):
        key = self._key(ip, port)
        self._last_act_at[key] = datetime.datetime.now()
        self._is_busy[key] = False

    def _delete(self, key):
        del self._client_pool[key]
        del self._last_act_at[key]
        del self._is_busy[key]

        if self.verbose:
            print('jsonsocketclient: cleared', key)

    def _cleaner(self):
        while True:
            time.sleep(10) # cleaning interval
            now = datetime.datetime.now()

            for key in list(self._client_pool.keys()):
                if self._is_busy[key]:
                    continue

                last_act = self._last_act_at[key]

                if now - last_act > datetime.timedelta(seconds=self.client_lifetime):
                    self._delete(key)