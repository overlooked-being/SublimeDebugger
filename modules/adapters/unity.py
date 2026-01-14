from __future__ import annotations
import os
from re import sub
import stat

import sublime

from .. import dap
from .. import core
from . import util
from .util import request

def is_valid_asset(asset: str):
	return asset.endswith('.zip') or asset.endswith('.tar.gz')

class Unity(dap.Adapter):
	type = ['unity']
	docs = 'https://github.com/overlooked-being/unity-dap/blob/master/README.md'

	installer = util.GitInstaller(
		type='unity',
		repo='overlooked-being/unity-dap',
		is_valid_asset=is_valid_asset
	)

	async def start(self, log: core.Logger, configuration: dap.ConfigurationExpanded):
		mono = await util.get_and_warn_require_mono(self.type, console)

		unity_editor_log_paths = {
			'linux': '~/.config/unity3d/Editor.log',
			'osx' : '~/Library/Logs/Unity/Editor.log',
			'windows': '%LOCALAPPDATA%\\Unity\\Editor\\Editor.log'
		}
		unity_editor_log_path = os.path.expandvars(os.path.expanduser(unity_editor_log_paths[sublime.platform()]))

		if not configuration.get('address') or not configuration.get('port'):
			port = None

			try:
				with open(unity_editor_log_path, 'r') as unity_editor_log_file:
					for line_number, line in enumerate(unity_editor_log_file):
						if line.startswith('Using monoOptions'):
							full_address = line[line.index('address=') + len('address='):]
							port = int(full_address[full_address.index(':') + 1:])
							break

			except IOError as e:
				log.error(e)
				raise core.Error('Failed to attach to Unity Editor')

			if not port:
				raise core.Error('Failed to attach to Unity Editor')

			configuration['address'] = '127.0.0.1'
			configuration['port'] = port

		install_path = self.installer.install_path()
		command = [mono, f'{install_path}/Release/unity-debug-adapter.exe']
		return dap.StdioTransport(command, stderr=log.error)

	@property
	def configuration_snippets(self) -> list[dict[str, Any]]:
		return [
			{
				'label': 'Unity: Attach to Unity Editor',
				'body': {
					'name': 'Unity: Attach to Unity Editor',
					'type': 'unity',
					'request': 'launch'
				},
			},
			{
				'label': 'Unity: Attach to Unity Player',
				'body': {
					'name': 'Unity: Attach to Unity Player',
					'type': 'unity',
					'request': 'launch',
					'address': '127.0.0.1',
					'port': 0
				},
			},
		]
