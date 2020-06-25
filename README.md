# Simple Artefact Registry

The Simple Artefact Registry is a simple web-based registry that allows up and download of artefacts and includes
optional authorization checks.

To run the Simple Artefact Registry Server use

```
   python -m simple_artefact_registry [OPTIONS]
```

The following options are available:

* ``-c`` ``--config``: The configuration file to load. Defaults to "sar.yaml"
* ``-p`` ``--port``: The port to listen on. Defaults to 8080

The configuration file format is documented (here)[https://github.com/mmh352/simple-artefact-registry/blob/default/src/simple_artefact_registry/__init__.py]
