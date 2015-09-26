#!/usr/bin/env python3
from CommandBuilder import CommandBuilder
from ConfigManager import ConfigManager
from DockerMachine import DockerMachine
from Utils import printe
import Utils
import argparse
import os
import re
import json


class DockerContainer(object):

	def __init__(self, name, machine):
		self.name = name
		self.machine = DockerMachine(machine)

	def base_command(self):
		return CommandBuilder('docker')

	def create(self, image, *command_args, capabilities=[], run=True, detach=True, device=False, environment={}, expose=[], links=[], net=False, ports=[], restart=False, volumes=[]):
		command = self.base_command()
		if run:
			command.append('run')
			if detach:
				command.append('--detach')
		else:
			command.append('create')
		command.append('--name', self.name)
		for cap in capabilities:
			command.append('--cap-add', cap)
		if device:
			command.append('--device', device)
		for env_var in environment:
			value = environment[env_var]
			if value is True:
				value = 'true'
			elif value is False:
				value = 'false'
			elif isinstance(value, dict) or isinstance(value, list):
				value = json.dumps(value)
			command.append('--env', '%s=%s' % (env_var, str(value)))
		for exp_port in expose:
			command.append('--expose', exp_port)
		for link in links:
			if not re.match(r'.+:.+', link):
				printe('Error: In %s, the link "%s" does not contain both a container name and an alias. Example = name:alias' % (self.name, link), terminate=True)
			command.append('--link', link)
		if net:
			command.append('--net', net)
		if ports:
			ip = self.machine.ip()
			for port in ports:
				if not re.match(r'.+:.+', port):
					printe('Error: In %s, the port "%s" does not contain both internal and external port.' % (self.name, port), terminate=True)
				if ip and port.startswith(':'):
					port = ip + port
				command.append('-p', port)
		if restart:
			command.append('--restart', 'always')
		for volume in volumes:
			command.append('--volume', volume)
		command.append(image)

		pattern = re.compile(r"{{([\w\-_]+)}}")
		for arg in command_args:
			for match in pattern.finditer(arg):
				name = match.group(1)
				if name == 'machine':
					ip = self.machine.ip()
				else:
					try:
						printe('Looking for machine with name %s' % name)
						ip = DockerMachine(name).ip()
					except:
						printe('Looking for neighboring container with name %s' % name)
						ip = DockerContainer(name, self.machine.name).ip()
				arg = arg.replace(match.group(0), ip)
			command.append(arg)
		return command.run()

	def is_running(self):
		running = self.base_command().append('inspect', '-f', '{{.State.Running}}', self.name).run()
		return running == 'true'

	def shell(self, shell='sh'):
		return self.base_command().append('exec', '-it', self.name, shell).run(replaceForeground=True)

	def ip(self):
		return self.base_command().append('inspect', '--format', '{{.NetworkSettings.IPAddress}}', self.name).run()

	def remove(self, stop_if_running=False):
		if self.is_running() and stop_if_running:
			self.stop()
		return self.base_command().append('rm', self.name).run()

	def stop(self):
		return self.base_command().append('stop', self.name).run()

	def kill(self):
		return self.base_command().append('kill', self.name).run()

	def start(self):
		return self.base_command().append('start', self.name).run()

	processes_column_layouts = {
		0: ['Names'],
		1: ['Names'],
		2: ['Names', 'Status'],
		3: ['Names', 'Image', 'Status'],
		4: ['Names', 'Image', 'Command', 'Status'],
		5: ['Names', 'Image', 'Command', 'Status'],
		6: ['Names', 'Image', 'Command', 'Status', 'CreatedAt'],
		7: ['Names', 'Image', 'Command', 'Status', 'CreatedAt'],
		8: ['Names', 'Image', 'Command', 'Status', 'CreatedAt', 'Ports'],
	}

	def processes(self):
		def make_table(names):
			columns = []
			for name in names:
				columns += ['{{.%s}}' % name]
			return 'table %s' % '\t'.join(columns)

		terminal_size = Utils.terminal_size()
		if terminal_size:
			min_col_width = 20
			table_column_space = int(terminal_size[1] / min_col_width)
			layout = ['Names', 'ID', 'Image', 'Command', 'Status', 'CreatedAt', 'Ports']
			table = make_table(DockerContainer.processes_column_layouts.get(table_column_space, layout))
		else:
			table = make_table('Names', 'Image', 'Status')
		return self.base_command().append('ps', '--all', '--format', table).run()

	def images(self):
		return self.base_command().append('images').run()

	def logs(self, tail=100):
		if self.name:
			return self.base_command().append('logs', '--follow', '--tail', str(int(tail)), self.name).run(replaceForeground=True)
		else:
			return CommandBuilder('bash', '-c', """
				set -m
				trap 'kill $(jobs -p)' 2
				count=0
				for c in $(docker ps --format "{{.Names}}"); do
					color="$(echo "$c" | md5 | cut -c1-4)"
					color=$((31 + ((16#${color}) % 7) ))
					docker logs -f $c | sed "s/^/\033[1;${color}m$c | \033[0;00m/" &
					count+=1
				done
				wait
			""").run(replaceForeground=True)


action_mappings = {
	'create': DockerContainer.create,
	'desc': ConfigManager.describe,
	'describe': ConfigManager.describe,
	'sh': DockerContainer.shell,
	'shell': DockerContainer.shell,
	'images': DockerContainer.images,
	'ip': DockerContainer.ip,
	'kill': DockerContainer.kill,
	'kinds': ConfigManager.listContainers,
	'logs': DockerContainer.logs,
	'ps': DockerContainer.processes,
	'processes': DockerContainer.processes,
	'remove': DockerContainer.remove,
	'rm': DockerContainer.remove,
	'run': DockerContainer.create,
	'running': DockerContainer.is_running,
	'stop': DockerContainer.stop,
	'start': DockerContainer.start
}

actions_without_name = ['images', 'kinds', 'ps', 'processes', 'logs']


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--config-dir', dest='config_directory', default='~/.lazy-docker', help='The config directory to be used for creating containers.')
	parser.add_argument('-f', '--force', dest='force', action='store_true', help='Force the current command, if supported.')
	parser.add_argument('--debug', dest='debug', action='store_const', const=True, help='Print out the commands instead of executing them.')
	parser.add_argument('-m', '--machine', default=os.environ.get('DOCKER_MACHINE_NAME'), help='The machine in which this container is located.')
	parser.add_argument('--no-debug', dest='debug', action='store_const', const=False, help='Disable debug mode.')
	parser.add_argument('action', choices=action_mappings, help='The action to perform: %s' % ', '.join(action_mappings))
	parser.add_argument('name', nargs='?', help='The name of the container to be used.')
	parser.add_argument('kind:flavor', nargs='?', help='Of form "kind:flavor". Kinds available are determined by the kinds in the config directory. Use the actions "kinds" to look up all available options.')
	args = parser.parse_args()

	if args.debug is True:
		os.environ['UTILS_DEBUG'] = 'true'
	elif args.debug is False:
		os.environ['UTILS_DEBUG'] = 'false'

	if args.action == 'create' or args.action == 'run' and not vars(args)['kind:flavor']:
		printe('No kind provided for action "create".')
		printe(parser.format_usage(), terminate=2)

	if args.action not in actions_without_name and not args.name:
		if args.action in ('desc', 'describe'):
			printe('Container kind:flavor required for action "%s". Use action "kinds" to list available options.' % args.action, terminate=2)
		printe('Container name required for action "%s".' % args.action, terminate=2)

	config_manager = ConfigManager(args.config_directory, filter='container')
	if args.action in ('run', 'create', 'describe', 'desc'):
		if args.action == 'create' or args.action == 'run':
			kind_and_flavor = vars(args)['kind:flavor']
		else:
			kind_and_flavor = args.name
		(kind, _, flavor) = kind_and_flavor.partition(':')
		if args.action == 'create' or args.action == 'run':
			config = config_manager.getContainerConfig(kind, flavor)
			DockerContainer(args.name, args.machine).create(
				config['image'],
				*config['command'],
				run=args.action == 'run',
				links=config['links'],
				ports=config['ports'],
				expose=config['expose'],
				volumes=config['volumes'],
				device=config['device'],
				capabilities=config['capabilities'],
				environment=config['environment'],
				restart=config['restart'],
				net=config['net']
			)
		else:
			print(config_manager.describeContainer(kind, flavor))
	elif args.action == 'kinds':
		printe("Here's a list of available kinds to create containers from:", flush=True)
		print('\n'.join(config_manager.listContainers()), flush=True)
		printe('To create one, use the "create" action, supply a name, and put kind:flavor on the end.')
	elif args.action == 'logs':
		if not args.name:
			DockerContainer(False, args.name).logs()
		else:
			DockerContainer(args.name, args.machine).logs()
	elif args.action in actions_without_name:
		if not args.machine:
			print(action_mappings[args.action](DockerContainer(False, args.name)))
		else:
			print(action_mappings[args.action](DockerContainer(args.name, args.machine)))
	elif args.action == 'rm' or args.action == 'remove':
		print(DockerContainer(args.name, args.machine).remove(stop_if_running=args.force))
	else:
		print(action_mappings[args.action](DockerContainer(args.name, args.machine)))
