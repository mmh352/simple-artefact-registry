"""
##########################################################
:mod:`simple_artefact_registry` - Simple Artefact Registry
##########################################################

The Simple Artefact Registry is a very simple Tornado web application that allows reading and storing of artefact
files. The available artefacts are configured using a YAML file with the following structure:

.. code-block:: yaml

   server:
     host: host/ip
     port: XXXX
   artefacts:
     dir_name:
       file_name:

The ``artefacts``` key contains an artefact tree structure that mirrors the structure in the file-system.
Only leaf entries are available as artefacts. The ``dir_name`` (or multiple nested) and the ``file_name`` are
concatenated to create both the file-path and the URL for access.

All keys in the ``artefacts`` key (including the ``artefacts`` key) can take the following three settings keys:

* ``_base_directory`` - The base base directory for resolving the file paths. Generally set directly on the
  ``artefacts`` key.
* ``_read_token`` - The bearer Authorization token to use for authorising GET requests. This is optional
* ``_write_token`` - The bearer Authorization token to use for authorising PUT requests. This is optional, but it is
  recommended that this be set otherwise any PUT request to that artefact will be allowed.

All three settings are inherited from parent keys, but can be overriden by child keys.
"""

from copy import deepcopy
from os import makedirs
from os.path import exists, dirname
from tornado import web, ioloop, gen, iostream


class ArtefactHandler(web.RequestHandler):
    """The :class:`~simple_artefact_registry.ArtefactHandler` handles the requests to a single
    artefact. It uses "bearer" authorization to check requests for read/write access. It uses
    GET to retrieve an artefact and PUT to store/update an artefact.

    :param path: The path at which to find the artefact
    :param settings: Settings configuring access to the
    """

    def initialize(self, path, settings):
        """Initialise the request handler, setting the ``path`` and ``settings``.

        :param path: The path at which to find the artefact
        :type path: ``string``
        :param settings: Settings configuring access to the
        :type settings: ``dict``
        """
        self._path = path
        self._settings = settings

    async def get(self):
        """Fetch a single artefact. Returns 401 if a "read_token" is set in the settings and no matching bearer
        Authorization header has been found. Returns 404 if no artefact has been stored/updated for the URL.
        """
        if 'read_token' in self._settings:
            if self.request.headers and 'Authorization' in self.request.headers:
                auth = self.request.headers['Authorization']
                if not auth.startswith('bearer ') or auth[7:] != self._settings['read_token']:
                    raise web.HTTPError(401)
            else:
                raise web.HTTPError(401)
        if not exists(f'{self._settings["base_directory"]}{self._path}'):
            raise web.HTTPError(404)
        with open(f'{self._settings["base_directory"]}{self._path}', 'rb') as in_f:
            while True:
                chunk = in_f.read(1024)
                if not chunk:
                    break
                try:
                    self.write(chunk)
                    await self.flush()
                except iostream.StreamClosedError:
                    break
                finally:
                    del chunk
                    await gen.sleep(0.000000001)

    async def put(self):
        """Store/Update a single artefact. Returns 401 if a "write_token" is set in the settings and no matching
        bearer Authorization header has been found."""
        if 'write_token' in self._settings:
            if self.request.headers and 'Authorization' in self.request.headers:
                auth = self.request.headers['Authorization']
                if not auth.startswith('bearer ') or auth[7:] != self._settings['write_token']:
                    raise web.HTTPError(401)
            else:
                raise web.HTTPError(401)
        if not exists(dirname(f'{self._settings["base_directory"]}{self._path}')):
            makedirs(dirname(f'{self._settings["base_directory"]}{self._path}'))
        with open(f'{self._settings["base_directory"]}{self._path}', 'wb') as out_f:
            out_f.write(self.request.body)
        self.set_status(204)

    def write_error(self, status_code, **kwargs):
        """Overwrite the :func:`~tornado.web.RequestHandler.write_error` to include setting the "WWW-Authenticate"
        header."""
        self.set_header('WWW-Authenticate', 'bearer realm="Simple Artefact Registry"')
        self.finish(f'{status_code}')


def build_urls(config, base_url='', base_settings=None):
    """Recursively builds the URL list for the given set of artefacts.

    :param config: The artefact configuration
    :type config: ``dict``
    :param base_url: The base URL under which to add any new artefacts
    :type base_url: ``string``
    :param base_settings: Any configuration settings set on parent artefacts
    :type base_settings: ``dict``
    :return: A list of URL, :class:`~simple_artefact_registry.ArtefactHandler`, settings tuples
    :rtype: ``[(url, ArtefactHandler, settings)]``
    """
    urls = []
    artefacts = [(key, value) for key, value in config.items() if not key.startswith('_')]
    if base_settings:
        settings = deepcopy(base_settings)
        settings.update(dict([(key[1:], value) for key, value in config.items() if key.startswith('_')]))
    else:
        settings = dict([(key[1:], value) for key, value in config.items() if key.startswith('_')])
    for key, value in artefacts:
        if [k for k in value.keys() if not k.startswith('_')]:
            urls.extend(build_urls(value, base_url=f'{base_url}/{key}', base_settings=settings))
        else:
            urls.append((f'{base_url}/{key}', ArtefactHandler, {'path': f'{base_url}/{key}', 'settings': settings}))
    return urls


def build_app(config):
    """Build the Tornado web app using the given config.

    :param config: The configuration to use
    :type config: ``dict``
    :return: The Tornado web application
    :rtype: :class:`~tornado.web.Application`
    """
    return web.Application(build_urls(config['artefacts']))


def run_server(config):
    """Run the Simple Artefact Registry server.

    :param config: The configuration to use
    :type config: ``dict``
    """
    if 'server' not in config:
        config['server'] = {'port': 8080, 'host': '0.0.0.0'}
    else:
        if 'port' not in config['server']:
            config['server']['port'] = 8080
        if 'host' not in config['server']:
            config['server']['host'] = '0.0.0.0'
    app = build_app(config)
    app.listen(config['server']['port'], config['server']['host'])
    ioloop.IOLoop.current().start()
