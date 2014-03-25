#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import docker
import netifaces
import os
import re
import socket
import subprocess
import sys
import time
import unittest
import urllib2
import yaml

import galley


def connect(timeout=30):
    """Creates a Docker Client Object to communicate with API."""
    # For boot2docker and docker-osx compatibility.
    if 'DOCKER_HOST' in os.environ.keys():
        docker_host = os.environ['DOCKER_HOST']
        # docker-py does not support 'tcp://' as base_url; however,
        # the docker client does not support 'http://' for DOCKER_HOST.
        # So, we need to convert DOCKER_HOST for compatibility.
        if 'tcp://' in docker_host:
            docker_host = docker_host.replace("tcp://", "http://")
        base_url = docker_host
    else:
        base_url = 'unix://var/run/docker.sock'

    c = docker.Client(base_url=base_url,
                      version='1.7',
                      timeout=timeout)
    return c


def build(path=None, tag=None, quiet=False, fileobj=None, nocache=False,
          rm=False, stream=False, timeout=600, retry=True):
    """Build Docker image from Dockerfile in provided path."""
    print("Building image %s with tag %s." % (path, tag))
    c = connect(timeout)
    image, _ = c.build(path=path, tag=tag, quiet=quiet, fileobj=fileobj,
                       nocache=nocache, rm=rm, stream=stream)
    time.sleep(5)
    if image:
        if check_if_image_exists(image):
            print("Successfully built image %s from %s." % (image, path))
            return image
        elif retry:
            print("Image %s could not be found. Retrying build." % image)
            build(path=path, tag=tag, quiet=quiet, fileobj=fileobj,
                  nocache=nocache, rm=rm, stream=stream, retry=False)
        else:
            print("Failed building image. Image %s could \
                  not be found." % image)
            print("Build Output: \n")
            sys.exit(1)
    elif retry:
        print("Failed building image from %s with tag %s. \
              Retrying build." % (image, path))
        build(path=path, tag=tag, quiet=quiet, fileobj=fileobj,
              nocache=nocache, rm=rm, stream=stream, retry=False)
    else:
        print("Failed building image from %s with tag %s." % (image, tag))
        print("Build Output: \n")
        sys.exit(1)


def check_if_container_exists(container):
    """Checks to see if Docker container exists."""
    #c = connect()
    print("Checking if container %s exists." % container[:12])
    # Docker-py currently does not properly list all containers
    # even though it is documented. When/If it does, the
    # following API call should work instead of the shell out.
    # conts = c.containers(all=True)
    if 'DOCKER_HOST' in os.environ.keys():
        host = os.environ['DOCKER_HOST']
        conts = subprocess.check_output(['docker', '-H', host, 'ps', '-a',
                                        '-notrunc=true'])
    else:
        conts = subprocess.check_output(['docker', 'ps', '-a',
                                        '-notrunc=true'])
    for cont in conts.splitlines():
        if container in cont:
            return True


def check_if_image_exists(image, tag=None):
    c = connect()
    images = c.images()
    if tag:
        print("Checking if image %s:%s exists." % (image, tag))
        for i in images:
            for repoTag in i['RepoTags']:
                if image + ":" + tag in repoTag:
                    print("Found image %s:%s." % (image, tag))
                    return True
    else:
        print("Checking if image %s exists." % image[:12])
        for i in images:
            # Force short hash because some Docker-Py functions
            # return long hash, and some return short hash. :/
            if image[:12] in i['Id']:
                print("Found image %s." % image[:12])
                return True
            for repoTag in i['RepoTags']:
                if image == repoTag:
                    print("Found image %s." % image)
                    return True


def check_if_running(container):
    c = connect()
    conts = c.containers()
    for cont in conts:
        if container in cont['Id']:
            return True


def clean(environment, nodestroy):
  # Clean the house...
  if not nodestroy:
      for index, data in environment['resources'].iteritems():
          kill(data['container'])
          remove_container(data['container'])
      for index, data in environment['images'].iteritems():
          if 'persist' in data.keys():
              if not data['persist']:
                  remove_image(data['image'])
          else:
              remove_image(data['image'])


def cleanup(containers=None, images=None):
    """Remove Images and Containers from System."""
    print("Cleaning Up Environment:")
    if containers:
        print("Removing containers:")
        for cont in containers:
            kill(cont)
            remove_container(cont)
    if images:
        print("Removing images:")
        for image in images:
            remove_image(image)
    print("Cleanup Successful.")


def create(image, command=None, hostname=None, user=None, detach=False,
           stdin_open=False, tty=False, mem_limit=0, ports=None,
           environment=None, dns=None, volumes=None, volumes_from=None,
           network_disabled=False, name=None, entrypoint=None, cpu_shares=None,
           working_dir=None):
    """Create a Docker container from an image."""
    c = connect()
    print("Creating %s container." % image)
    cont = c.create_container(image, command=command, hostname=hostname,
                              user=user, detach=detach,
                              stdin_open=stdin_open, tty=tty,
                              mem_limit=mem_limit, ports=ports,
                              environment=environment, dns=dns,
                              volumes=volumes, volumes_from=volumes_from,
                              name=name)
    print("Successfully created %s container: %s" % (image[:12],
                                                     cont['Id'][:12]))
    return cont['Id']


def get_ip_address():
    """Attempts to get IP address for eth1, falls back to eth0."""
    # For boot2docker and docker-osx compatibility.
    if 'DOCKER_HOST' in os.environ.keys():
        if ('127.0.0.1' or 'localhost') not in os.environ['DOCKER_HOST']:
            host = urllib2.urlparse.urlparse(os.environ['DOCKER_HOST'])[1]
            if ':' in host:
                host = host.split(":")[0]
            return host

    try:
        host = netifaces.ifaddresses('eth1')[netifaces.AF_INET][0]['addr']
    except Exception:
        host = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']

    return host


def kill(container, signal=None):
    c = connect()
    print("Killing container %s." % container[:12])
    c.kill(container, signal)
    if not check_if_running(container):
        print("Successfully killed container %s." % container[:12])
        return True
    else:
        print("Failed to kill container %s." % container[:12])
        return False


def pull(repository, tag='latest', stream=False):
    """Pull a Docker image from the Index."""
    c = connect()
    # TODO(rwalker): Docker-py does not seem to support pulling
    # specific tags even though it is documented. For now
    # we will always default to 'latest'.
    tag = 'latest'
    print("Pulling %s:%s from registry." % (repository, tag))
    c.pull(repository, stream=stream)
    time.sleep(5)
    if check_if_image_exists(repository, tag):
        print("Successfully pulled %s:%s." % (repository, tag))
        return True
    else:
        raise Exception("Failed to pull %s:%s." % (repository, tag))


def remove_container(container):
    """Remove a Docker container from the system."""
    c = connect()
    print("Removing container %s." % container[:12])
    if check_if_container_exists(container):
        c.remove_container(container)
        if not check_if_container_exists(container):
            print("Successfully removed container %s." % container[:12])
        else:
            print("Failed to remove container: %s." % container[:12])
    else:
        print("Container %s not found. Skipping..." % container[:12])


def remove_image(image, tag="latest"):
    """Remove a Docker image from the system."""
    c = connect()
    # Sometimes images may be passed with a tag included.
    if ':' in image:
        tag = image.split(':')[1]
        image = image.split(':')[0]
        print("Removing image %s:%s." % (image, tag))
        if check_if_image_exists(image):
            c.remove_image(image)
        else:
            print("Image %s:%s not found. Skipping..." % (image, tag))
            return False
    else:
        try:
            print("Removing image %s:%s." % (image, tag))
            imagetags = image + ':' + tag
            c.remove_image(imagetags)
        except docker.APIError:
            # Probably an image ID, so it has no tag.
            if check_if_image_exists(image):
                c.remove_image(image)
            else:
                print("Image %s not found. Skipping..." % image)
                return False

    if not check_if_image_exists(image, tag):
        print("Successfully removed image %s:%s." % (image, tag))
    else:
        print("Failed to remove image %s:%s." % (image, tag))


def select_random_port():
    retries = 10
    while retries:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            sock.bind(('', 0))
            port = sock.getsockname()[1]
            sock.close()
            return port
        except Exception:
            if retries == 1:
                raise Exception("Unable to select random port. Aborting.")
            print("Unable to bind to port. Retrying...")
            retries -= 1


def start(container, binds=None, port_bindings=None, lxc_conf=None,
          publish_all_ports=False, links=None):
    """Start a Docker container."""
    c = connect()
    print("Starting container %s." % container[:12])
    c.start(container, binds=binds, port_bindings=port_bindings,
            lxc_conf=lxc_conf, publish_all_ports=publish_all_ports,
            links=links)
    time.sleep(6)
    if check_if_running(container):
        print("Successfully started container %s." % container[:12])
        return True


def stop(container):
    """Stop a running container."""
    c = connect()
    print("Stopping container %s." % container[:12])
    c.stop(container=container)
    if not check_if_running(container):
        print("Successfully stopped container %s." % container[:12])
        return True


def load_yaml(filepath):
    """Convert YAML file to Python object."""
    with open(filepath, 'r') as infile:
        return yaml.load(infile.read())


def build_environment(config):
    """Build and return test environment."""

    images = config['images']
    resources = config['resources']
    if 'testparams' in config.keys():
        testparams = config['testparams']
    else:
        testparams = {}
    environ = os.environ

    # TODO(rwalker): Add more host attributes as needed.
    host = {
        'ip': get_ip_address()
    }

    # TODO(rwalker): There has to be a better way to do this without
    #                going full Jinja.

    # Populate environment variables in config
    for index, data in images.iteritems():
        for key, value in data.iteritems():
            if type(value) is dict:
                for k, v in value.iteritems():
                    for match in re.findall('{{environ.*?}}', str(v)):
                        sub = eval(re.sub('{{|}}', '', match), locals(), {})
                        v = v.replace(match, str(sub))
                        images[index][key][k] = v
            else:
                for match in re.findall('{{environ.*?}}', str(value)):
                    sub = eval(re.sub('{{|}}', '', match), locals(), {})
                    value = value.replace(match, str(sub))
                    images[index][key] = value

    for index, data in resources.iteritems():
        for key, value in data.iteritems():
            if type(value) is dict:
                for k, v in value.iteritems():
                    for match in re.findall('{{environ.*?}}', str(v)):
                        sub = eval(re.sub('{{|}}', '', match), locals(), {})
                        v = v.replace(match, str(sub))
                        resources[index][key][k] = v
            else:
                for match in re.findall('{{environ.*?}}', str(value)):
                    sub = eval(re.sub('{{|}}', '', match), locals(), {})
                    value = value.replace(match, str(sub))
                    resources[index][key] = value

    for key, value in testparams.iteritems():
        for match in re.findall('{{environ.*?}}', str(value)):
            sub = eval(re.sub('{{|}}', '', match), locals(), {})
            value = value.replace(match, str(sub))
            testparams[key] = value

    # Build images and write back values
    for index, data in images.iteritems():
        if data['action'] == 'pull':
            pull(data['source'])
            images[index]['image'] = data['source']
        if data['action'] == 'build':
            image = build(path=data['source'], tag=data['name'], rm=True)
            images[index]['image'] = image

    for index, data in resources.iteritems():
        if data['host_port'] == "{{random_port}}":
            data['host_port'] = select_random_port()
    # Find image references in resources and replace with
    # image names/IDs
    for index, data in resources.iteritems():
        for key, image in images.iteritems():
            if re.sub('{{|}}', '', data['image']) == image['name']:
                resources[index]['image'] = image['image']
        # Find resource attr references and replace with value
        if 'environment' in data.keys():
            for key, value in data['environment'].iteritems():
                for match in re.findall('{{resources.*?}}', value):
                    v = eval(re.sub('{{|}}', '', match), locals(), {})
                    value = value.replace(match, str(v))
                    resources[index]['environment'][key] = value
                for match in re.findall('{{host.*?}}', value):
                    v = eval(re.sub('{{|}}', '', match), locals(), {})
                    value = value.replace(match, str(v))
                    resources[index]['environment'][key] = value
    # Create containers
    for index, data in resources.iteritems():
        if 'cont_port' in data.keys():
            ports = data['cont_port']
        else:
            ports = None
        if 'command' in data.keys():
            command = data['command']
        else:
            command = None
        if 'cont_volume' in data.keys():
            volumes = data['cont_volume']
        else:
            volumes = None
        if 'environment' in data.keys():
            environment = data['environment']
        else:
            environment = None
        container = create(data['image'], command=command, ports=[ports],
                           volumes=[volumes], environment=environment)
        resources[index]['container'] = container
    # Start containers
    for index, data in resources.iteritems():
        port_bindings = None
        binds = None
        if 'cont_port' in data.keys():
            if 'host_port' in data.keys():
                port_bindings = {data['cont_port']: data['host_port']}
        if 'host_volume' in data.keys():
            if 'cont_volume' in data.keys():
                binds = {data['host_volume']: data['cont_volume']}
        start(data['container'], port_bindings=port_bindings, binds=binds)
        time.sleep(10)  # Allow container to warm-up before starting next one

    environment = config
    environment['host'] = host
    environment['images'] = images
    environment['resources'] = resources
    environment['testparams'] = testparams

    return environment


def run_tests(config, test_file_pattern, nodestroy):
    start_time = time.time()

    environment = build_environment(config)

    galley.set_environment(environment)
    print("Waiting for containers to start...")
    time.sleep(5)

    # Discover and run all galley unittest files.
    tloader = unittest.TestLoader()
    galleytests = tloader.discover(
        os.getcwd(),
        pattern=test_file_pattern
    )
    runner = unittest.runner.TextTestRunner()
    print("Running tests:\n")
    results = runner.run(galleytests)
    test_count = results.testsRun
    test_errors = len(results.errors)
    test_failures = len(results.failures)

    if not results.wasSuccessful():
        print("\n   Tests Run: %d" % test_count)
        print("Tests Failed: %d" % test_failures)
        print(" Test Errors: %d" % test_errors)
        clean(environment, nodestroy)
        total_time = time.time() - start_time
        print("\nTotal Elapsed Time: %.2f seconds." % total_time)
        sys.exit(1)
    else:
        print("\n   Tests Run: %d" % test_count)
        print("Tests Failed: %d" % test_failures)
        print(" Test Errors: %d\n" % test_errors)
        clean(environment, nodestroy)
        total_time = time.time() - start_time
        print("\nTotal Elapsed Time: %.2f seconds." % total_time)
        sys.exit(0)
