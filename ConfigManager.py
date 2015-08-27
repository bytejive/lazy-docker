import os
import json
from Utils import printe

required_fields = [
	'name',
	'description',
	'type',
	'kind',
	'flavor'
]

required_machine_fields = [
]

# Optional machine config fields with their default values.
optional_machine_fields = {
	'experimental': False,
	'consul_machine': False,
	'multihost_networking': False
}

required_container_fields = [
	'image'
]

# Optional container config fields with their default values.
optional_container_fields = {
	'command': [],
	'environment': {},
	'expose': [],
	'links': [],
	'ports': [],
	'restart': False,
	'volumes': [],
	'net': False
}


class ConfigManager(object):

	def __init__(self, config_directory, filter=None):
		configs = os.listdir(config_directory)
		self.configs = {}
		for config in configs:
			if not config.endswith('.json'):
				continue
			with open('%s/%s' % (config_directory, config)) as file:
				configJson = json.load(file)
			if filter and configJson['type'] != filter:
				continue
			for field in required_fields:
				if field not in configJson:
					printe('Config %s is missing its %s.' % (config, field), terminate=3)
			if configJson['type'] == 'container':
				all_fields = list(required_fields)
				all_fields += required_container_fields
				all_fields += optional_container_fields
				for field in configJson:
					if field not in all_fields:
						printe('Container config %s has unknown field "%s".' % (config, field), terminate=3)
				for field in required_container_fields:
					if field not in configJson:
						printe('Container config %s is missing its %s.' % (config, field), terminate=3)
				for field in optional_container_fields:
					if field not in configJson:
						configJson[field] = optional_container_fields[field]
			elif configJson['type'] == 'machine':
				all_fields = list(required_fields)
				all_fields += required_machine_fields
				all_fields += optional_machine_fields
				for field in configJson:
					if field not in all_fields:
						printe('Container config %s has unknown field "%s".' % (config, field), terminate=3)
				for field in required_machine_fields:
					if field not in configJson:
						printe('Machine config %s is missing its %s.' % (config, field), terminate=3)
				for field in optional_machine_fields:
					if field not in configJson:
						configJson[field] = optional_machine_fields[field]
			else:
				printe('Unknown type "%s". Available types are: container, machine' % configJson['type'], terminate=3)
			config_type = configJson['type']
			kind = configJson['kind']
			flavor = configJson['flavor']
			if config_type not in self.configs:
				self.configs[config_type] = {}
			if kind not in self.configs[config_type]:
				self.configs[config_type][kind] = {}
			elif flavor in self.configs[config_type][kind]:
				printe(
					"Duplicate kind:flavor configs found: %s %s. Please change or remove one of these configs to have a different kind:flavor combination." % (
						self.configs[config_type][kind][flavor].file_name,
						config
					),
					terminate=True
				)
			del configJson['type']
			del configJson['kind']
			del configJson['flavor']
			configJson['file_name'] = config
			self.configs[config_type][kind][flavor] = configJson

	def getContainerConfig(self, kind, flavor):
		return self.get('container', kind, flavor)

	def getMachineConfig(self, kind, flavor):
		return self.get('machine', kind, flavor)

	def get(self, config_type, kind, flavor):
		if kind not in self.configs[config_type]:
			printe('Unknown %s kind: "%s"' % (config_type, kind), terminate=2)
		if flavor not in self.configs[config_type][kind]:
			printe('Unknown %s flavor for %s: "%s"' % (config_type, kind, flavor), terminate=2)
		return self.configs[config_type][kind][flavor]

	def describeContainer(self, kind, flavor):
		return self.describe('container', kind, flavor)

	def describeMachine(self, kind, flavor):
		return self.describe('machine', kind, flavor)

	def describe(self, config_type, kind, flavor):
		config = self.get(kind, flavor)
		return '"%s":\t%s' % (config[config_type]['name'], config[config_type]['description'])

	def listContainers(self):
		return self.list('container')

	def listMachines(self):
		return self.list('machine')

	def list(self, config_type):
		list = []
		for kind in self.configs[config_type]:
			for flavor in self.configs[config_type][kind]:
				list += ['%s:%s' % (kind, flavor)]
		return list
