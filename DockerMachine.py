#!/usr/bin/env python3

import argparse
import os
from Utils import printe
from CommandBuilder import CommandBuilder
from ConfigManager import ConfigManager

"""
The MIT License (MIT)

Copyright (c) 2015 John Starich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""


class DockerMachine(object):

    def __init__(self, name=False, url=False):
        if not name and url:
            name = CommandBuilder('bash', '-c', 'docker-machine ls | tail -n +2 | grep "%s" | sed "s/\s.*//"' % url).run()
        self.local = not name
        if self.local:
            name = '127.0.0.1'
        self.name = name

    def create(self, driver, **config):
        command = CommandBuilder('docker-machine', 'create')
        command.append('--driver', driver)
        if config.get('swarm_token') is not None:
            command.append('--swarm')
            command.append('--swarm-discovery', 'token://%s' % config.get('swarm_token'))
        if config.get('swarm_master') is not None:
            command.append('--swarm-master')
        if config.get('registry_mirror') is not None:
            ip = DockerMachine(config.get('registry_mirror')).ip()
            if not ip:
                printe('IP for the registry machine could not be determined. Does that machine have an IP?', terminate=True)
            command.append('--engine-registry-mirror', 'http://%s:5000' % ip)
        if config.get('experimental') is not None:
            command.append('--engine-install-url', 'https://experimental.docker.com')
        if config.get('neighbor_machine') is not None and not config.get('multihost_networking') is not None:
            printe('Neighbor machine was provided but multihost networking was not enabled explicitly. Multihost networking must be enabled if neighboring machine is to be used.', terminate=2)
        if config.get('multihost_networking') is not None:
            command.append('--engine-opt', 'default-network=overlay:multihost')
            command.append('--engine-label', 'com.docker.network.driver.overlay.bind_interface=eth0')
            if config.get('neighbor_machine') is not None:
                command.append('--engine-label', 'com.docker.network.driver.overlay.neighbor_ip=%s' % DockerMachine(config.get('neighbor_machine')).ip())
        if config.get('consul') is not None:
            if isinstance(config.get('consul'), str):
                consul_name = config.get('consul')
            else:
                consul_name = 'consul'
            command.append('--engine-opt', 'kv-store=consul:%s:8500' % DockerMachine(consul_name).ip())

        command.append(self.name)
        return command.run()

    def ip(self):
        return CommandBuilder('docker-machine', 'ip', self.name).run()

    def env(self):
        command = CommandBuilder('docker-machine', 'env')
        if self.local:
            command.append('-u')
        else:
            command.append(self.name)
        return command.run()

    def config(self):
        if self.local:
            return False
        return CommandBuilder('docker-machine', 'config', self.name).run().split()

    def remove(self):
        if self.local:
            printe("Machine name not provided: Cannot remove a local Docker instance.")
        return CommandBuilder('docker-machine', 'rm', self.name).run()

    def ssh(self):
        if self.local:
            printe("Machine name not provided: Won't try to ssh to local.")
        return CommandBuilder('docker-machine', 'ssh', self.name).run(replaceForeground=True)

    def start(self):
        if self.local:
            printe("Machine name not provided: Won't try to start local.")
        return CommandBuilder('docker-machine', 'start', self.name).run()

    def stop(self):
        if self.local:
            printe("Machine name not provided: Won't try to stop local.")
        return CommandBuilder('docker-machine', 'stop', self.name).run()

    def list():
        return CommandBuilder('docker-machine', 'ls').run(replaceForeground=True)

action_mappings = {
    'config': DockerMachine.config,
    'create': DockerMachine.create,
    'env': DockerMachine.env,
    'environment': DockerMachine.env,
    'ip': DockerMachine.ip,
    'kinds': ConfigManager.listMachines,
    'list': DockerMachine.list,
    'ls': DockerMachine.list,
    'rm': DockerMachine.remove,
    'remove': DockerMachine.remove,
    'ssh': DockerMachine.ssh,
    'start': DockerMachine.start,
    'stop': DockerMachine.stop
}

actions_without_name = ['list', 'ls', 'kinds']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', dest='debug', action='store_const', const=True, help='Print out the commands instead of executing them.')
    parser.add_argument('--no-debug', dest='debug', action='store_const', const=False, help='Disable debug mode.')
    parser.add_argument('--config-dir', dest='config_directory', default='~/.lazy-docker', help='The config directory to be used for creating containers.')
    parser.add_argument('-d', '--driver', dest='driver', default='kvm', help='The driver used to provision a docker-machine.')
    parser.add_argument('-c', '--consul-machine', dest='consul_machine', help='The machine on which a consul server is running.')
    parser.add_argument('-e', '--experimental', dest='experimental', action='store_true', help='Whether or not to use the experimental docker engine.')
    parser.add_argument('-m', '--experimental-multihost-networking', dest='multihost_networking', action='store_true', help='Whether or not to use the experimental docker engine.')
    parser.add_argument('-n', '--experimental-neighbor-machine', dest='neighbor_machine', help='Whether or not to use the experimental docker engine.')
    parser.add_argument('-r', '--registry-mirror', dest='registry_mirror', default='pi-registry', help='The registry mirror used to cache Docker Hub requests.')
    parser.add_argument('-R', '--no-registry-mirror', dest='registry_mirror', action='store_const', const=None, help='Disable the registry mirror.')
    parser.add_argument('-s', '--swarm-token', dest='swarm_token', help='The swarm token for this machine.')
    parser.add_argument('--swarm-master', dest='swarm_master', action='store_true', default=False, help='Whether or not this machine will be a swarm master.')
    parser.add_argument('action', choices=action_mappings, help='The action to perform: %s' % ', '.join(action_mappings))
    parser.add_argument('name', nargs='?', help='The name of the machine to use.')
    args = parser.parse_args()
    if args.debug is True:
        os.environ['UTILS_DEBUG'] = 'true'
    elif args.debug is False:
        os.environ['UTILS_DEBUG'] = 'false'

    config_manager = ConfigManager(args.config_directory, filter='machine')
    if args.action not in actions_without_name and not args.name:
        printe('Action "%s" requires a name.' % args.action)
        printe(parser.format_usage(), terminate=2)

    if args.action == 'kinds':
        printe("Here's a list of available kinds to create machines from:", flush=True)
        print('\n'.join(config_manager.listMachines()), flush=True)
        printe('To create one, use the "create" action, supply a name, and put kind:flavor on the end.')
    elif args.action in actions_without_name:
        action_mappings[args.action]()
    elif args.action == 'create':
        machine_config = dict(vars(args))
        if 'consul_machine' in machine_config:
            machine_config['consul'] = machine_config['consul_machine']
            del machine_config['consul_machine']
        if 'driver' in machine_config:
            del machine_config['driver']
        DockerMachine(args.name).create(
            args.driver,
            **machine_config
        )
    else:
        result = action_mappings[args.action](DockerMachine(args.name))
        if isinstance(result, list):
            result = ' '.join(result)
        print(result)
