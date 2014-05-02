Galley
======

End-to-end test orchestration with Docker.

Getting Started Guide
=====================

Requirements:

-  Python 2.7.5
-  Docker >= 0.10.0

Installation
------------

1. Install Galley:

   ::

       pip install -r requirements
       python setup.py install

2. Run Galley:

   ::

       $ galley -h
       usage: galley [-h] [--no-destroy] [config] [pattern]

       End-to-end testing orchestration with Docker.

       positional arguments:
         config        Path to galley YAML file that defines Docker resources.
         pattern       Test file pattern.

       optional arguments:
         -h, --help    show this help message and exit
         --no-destroy  Do not destroy images and containers.

.galley.yml
-----------

You define the environment you want Galley to create in the
``.galley.yml`` file. Place this file in your application's root
directory. ``.galley.yml`` consists of three sections: ``images``,
``resources``, and ``testparams``.

images
~~~~~~

::

    images:
      0:
        name: "redis"
        source: "dockerfile/redis"
        tag: "latest"
        action: "pull"
        persist: True
      1:
        name: "mongodb"
        source: "dockerfile/mongodb"
        tag: "latest"
        action: "pull"
        persist: True
      2:
        name: "baconpancakes"
        source: "/path/to/baconpancakes"
        action: "build"
        persist: False

In the ``images`` section, you describe what images you want Galley to
create and how you would like to create them.

-  ``name``: A name for the image in Galley. This can be used by
   ``resources`` to describe what image to use when creating them. For
   ``build`` actions, this is also the name tagged to the image built.
-  ``source``: For images with an ``pull`` action, this is the
   ``repo/image`` of the image to be pulled. For ``build`` actions, this
   is the path to the directory containing the ``Dockerfile`` to build.
   If ``.galley.yml`` is in the same directory as your ``Dockerfile``,
   this can be ``"."``.
-  ``tag``: The image tag to pull.
-  ``action``: Available actions are ``pull`` and ``build``:

   -  ``pull`` uses the ``docker pull`` command to pull the image
      described in ``source`` from the Docker Index.
   -  ``build`` uses the ``docker build`` command to build an image from
      the ``Dockerfile`` located in the directory described in
      ``source``.

-  ``persist`` (optional): When Galley finishes testing, it destroys all
   images it created. To keep images from one Galley run to the next,
   set ``persist`` to ``True``. This is helpful if you have upstream
   images you will use every time since they will not have to be
   downloaded on each run.

testparams
~~~~~~~~~~

::

    testparams:
      pancakes: "{{environ['GALLEY_PANCAKES']}}"
      bacon: "{{environ['GALLEY_BACON']}}"

``testparams`` are key-value attributes that can be referenced by your
tests.

resources
~~~~~~~~~

::

    resources:
      0:
        name: "redis"
        image: "{{redis}}"
        host_port: "{{random_port}}"
        cont_port: 6379
      1:
        name: "mongodb"
        image: "{{mongodb}}"
        host_port: "{{random_port}}"
        cont_port: 27017
      2:
        name: "baconpancakes"
        image: "{{baconpancakes}}"
        host_port: "{{random_port}}"
        cont_port: 8080
        command: "--role api"
        host_volume: "./docker/config"
        cont_volume: "config"
        environment:
          BACONPANCAKES_ADDRESS: "0.0.0.0:8080"
          BACONPANCAKES_USERNAME: "{{environ['GALLEY_BACONPANCAKES_USERNAME']}}"
          BACONPANCAKES_PASSWORD: "{{environ['GALLEY_BACONPANCAKES_PASSWORD']}}"
          BACONPANCAKES_BROKER_URL: "redis://{{host['ip']}}:{{resources[0]['host_port']}}"
          BACONPANCAKES_CELERY_BACKEND: "redis://{{host['ip']}}:{{resources[0]['host_port']}}"
          BACONPANCAKES_CONNECTION_STRING: "mongodb://{{host['ip']}}:{{resources[1]['host_port']}}"

In the ``resources`` section, you describe what containers you would
like Galley to create and run from the images in the ``images`` section.

-  ``name``: The name of the resource. Currently this is not used by
   anything, but in the furture should be used as the name of the
   container and as a key when referenced by other resources.
-  ``image``: The ``id`` of the image to use to create the container. By
   using ``{{image_name}}``, Galley will replace this with the actual
   image ``id`` when the image is created.
-  ``host_port``: The port on the host to map to ``cont_port``. By using
   ``{{random_port}}`` a random available ephemeral port on the host
   will be selected.
-  ``cont_port``: The port in the container to map to ``host_port``.
-  ``command``: The command to use when running the container.
-  ``host_volume``: A directory on the host to mount into your container
   as ``cont_volume``. Note: volumes are currently not supported by any
   of the Docker options in OS X. This option only works in Linux.
-  ``cont_volume``: The directory in the container where ``host_volume``
   will be mounted.
-  ``environment``: Environment variables to inject into container when
   run.

``.galley.yml`` Templating:
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``{{resources[..]}}``:

   -  In the resources section, you can build a relationship from one
      resource to another by referencing another resources data. For
      example, since we are telling Galley to choose a
      ``{{random_port}}`` for our MongoDB and Redis instances, our
      ``baconpancakes`` app won't know how to talk to them. So, in the
      environment section we tell ``baconpancakes`` to find the Celery
      backend with the ``host_port`` from ``resource 0`` by using
      ``{{resources[0]['host_port']}}`` in the connection string. This
      tells Galley to go find the value of ``host_port`` for
      ``resource 0`` and fill it in.
   -  Currently, Galley is not smart enough to resolve dependencies on
      its own; therefore, a resource can only reference values from
      resources that appear before it in the ``.galley.yml`` file. In
      the future, this will likely be resolved by explicitly describing
      dependencies.
   -  Only available in the ``resources`` section.

-  ``{{host[..]}}``:

   -  Host-level information can be referenced through the ``host``
      dictionary. The main usage of this is to provide the host's IP
      address in order to allow separate resources to communicate with
      each other.
   -  Currently, the only host-level attribute available in ``host`` is
      ``ip``.
   -  Only available in the ``resources`` section.

-  ``{{environ[..]}}``:

   -  Replaced with referenced host environment variable.

Sample ``.galley.yml`` file:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    images:
      0:
        name: "redis"
        source: "dockerfile/redis"
        tag: "latest"
        action: "pull"
        persist: True
      1:
        name: "mongodb"
        source: "dockerfile/mongodb"
        tag: "latest"
        action: "pull"
        persist: True
      2:
        name: "baconpancakes"
        source: "/path/to/baconpancakes"
        action: "build"
        persist: False
    resources:
      0:
        name: "redis"
        image: "{{redis}}"
        host_port: "{{random_port}}"
        cont_port: 6379
      1:
        name: "mongodb"
        image: "{{mongodb}}"
        host_port: "{{random_port}}"
        cont_port: 27017
      2:
        name: "baconpancakes"
        image: "{{baconpancakes}}"
        host_port: "{{random_port}}"
        cont_port: 8080
        command: "--role api"
        host_volume: "./docker/config"
        cont_volume: "config"
        environment:
          BACONPANCAKES_ADDRESS: "0.0.0.0:8080"
          BACONPANCAKES_USERNAME: "{{environ['GALLEY_BACONPANCAKES_USERNAME']}}"
          BACONPANCAKES_PASSWORD: "{{environ['GALLEY_BACONPANCAKES_PASSWORD']}}"
          BACONPANCAKES_BROKER_URL: "redis://{{host['ip']}}:{{resources[0]['host_port']}}"
          BACONPANCAKES_CELERY_BACKEND: "redis://{{host['ip']}}:{{resources[0]['host_port']}}"
          BACONPANCAKES_CONNECTION_STRING: "mongodb://{{host['ip']}}:{{resources[1]['host_port']}}"
    testparams:
      pancakes: "{{environ['GALLEY_PANCAKES']}}"
      bacon: "{{environ['GALLEY_BACON']}}"

Galleytests
-----------

After Galley completes creating your environment, it looks recursively
for any ``galleytest_*.py`` files in your current directory.

Writing tests for Galley to use is easy! Galley uses `Python
unittests <http://docs.python.org/2/library/unittest.html>`__ to test
your environment. Therefore, writing a test for Galley is just as easy
and allows you to use any of ``unittest``'s `assert
methods <http://docs.python.org/2/library/unittest.html#assert-methods>`__.
All you need to do is make sure to import ``GalleyTestCase`` from
``galley.test`` and pass ``GalleyTestCase`` into your test class:

::

    import requests

    from galley.test import GalleyTestCase


    class TestWebGetRequest(GalleyTestCase):

        def test_web_status(self):
            env = self.environment
            web_ip = env['host']['ip']
            web_port = env['resources'][2]['host_port']
            url = "http://%s:%d" % (web_ip, web_port)
            response = requests.get(url)

            self.assertEqual(200, response.status_code)
            self.assertIn('<title>MakinBaconPancakes</title>', response.text)

In this test we want to check to make sure our web application started
properly and that the some expected content was found on the page. Since
we imported ``GalleyTestCase`` and passed it into our test class, we can
also reference our entire environment in our test by calling
``self.envionment``. Here, we used this to find the IP address of the
Docker host and the port our web application was mapped to. As you can
see, the ``self.assertEqual()`` and ``self.assertIn()`` functions come
straight from ``unittests``.

Galley tests can be more complicated as well:

::

    import requests
    import time

    from galley.test import GalleyTestCase


    class TestPancakes(GalleyTestCase):

        def test_pancakes(self):
            env = self.environment
            api_ip = env['host']['ip']
            api_port = env['resources'][2]['host_port']
            pancakes = env['testparams']['pancakes']
            bacon = env['testparams']['bacon']
            url = "http://%s:%d/api/%s/%s" % (api_ip, api_port, pancakes, bacon)
            response = requests.post(url)
            baconpancakes = response.json()
            status = response.status_code
            pancake_id = baconpancakes['id']

            self.assertEqual(201, status)
            self.assertEqual('REQUESTED', baconpancakes['status'])

            url = url + '/' + pancake_id
            for attempt in range(20):
                r = requests.get(url)
                pancake = r.json()
                try:
                    self.assertEqual('MADE', baconpancakes['status'])
                except Exception:
                    time.sleep(5)

            self.assertEqual('MADE', baconpancakes['status'])
            self.assertIn('bacon', baconpancakes.keys())

TEST!
-----

::

    $ galley
    Pulling dockerfile/redis:latest from registry.
    Checking if image dockerfile/redis:latest exists.
    Found image dockerfile/redis:latest.
    Successfully pulled dockerfile/redis:latest.
    Pulling dockerfile/mongodb:latest from registry.
    Checking if image dockerfile/mongodb:latest exists.
    Found image dockerfile/mongodb:latest.
    Successfully pulled dockerfile/mongodb:latest.
    Building image . with tag baconpancakes.
    Checking if image c023ce32fc62 exists.
    Found image c023ce32fc62.
    Successfully built image c023ce32fc62 from ..
    Creating dockerfile/redis container.
    Successfully created dockerfile/redis container: 380c81fe0775
    Creating dockerfile/mongodb container.
    Successfully created dockerfile/mongodb container: 706e35d5e28f
    Creating c023ce32fc62 container.
    Successfully created c023ce32fc62 container: e0cc0d1cebc2
    Creating c023ce32fc62 container.
    Successfully created c023ce32fc62 container: 1f4d584d8dc0
    Starting container 380c81fe0775.
    Successfully started container 380c81fe0775.
    Starting container 706e35d5e28f.
    Successfully started container 706e35d5e28f.
    Starting container e0cc0d1cebc2.
    Successfully started container e0cc0d1cebc2.
    Starting container 1f4d584d8dc0.
    Successfully started container 1f4d584d8dc0.
    Waiting for containers to start...
    ...
    ----------------------------------------------------------------------
    Ran 3 tests in 30.617s

    OK

    Total Elapsed Time: 362.87 seconds.

Special Install Instructions for OS X:
--------------------------------------

Requirements:

-  Python 2.7.5
-  `Vagrant <vagrantup.com>`__
-  `VirtualBox <https://www.virtualbox.org/wiki/Downloads>`__
-  `docker-osx <https://github.com/noplay/docker-osx>`__

1. Setup VirtualBox and Vagrant.

2. Install docker-osx:

   ::

       curl https://raw.github.com/noplay/docker-osx/0.8.0/docker-osx > /usr/local/bin/docker-osx
       chmod +x /usr/local/bin/docker-osx

3. Start docker-osx:

   ::

       docker-osx start

4. Once the script is done, you should see a line like this:

   ::

       To use docker:
       export DOCKER_HOST=tcp://172.16.42.43:4243
       and then use the docker command from os-x directly.

   Copy and paste the ``export DOCKER_HOST=tcp://172.16.42.43:4243``
   line and run this to set the ``DOCKER_HOST`` environment variable.
   Galley will need this to communicate with Docker.

5. Verify Docker is working:

   ::

       docker version

6. Proceed to the regular installation instructions.


