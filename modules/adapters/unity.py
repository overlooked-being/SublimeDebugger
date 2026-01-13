from __future__ import annotations
import os
from re import sub
import stat

import sublime

from .. import dap
from .. import core
from . import util
from .util import request

class UnityInstaller(util.vscode.AdapterInstaller):
	type = 'unity'

	async def install(self, version: str|None, log: core.Logger):
		pass

	async def post_install(self, version: str|None, log: core.Logger):
		pass

	async def installable_versions(self, log: core.Logger):
		return ['1.0.0']

	def installed_version(self):
		return '1.0.0'


class Unity(dap.AdapterConfiguration):
	type = ['unity']
	docs = 'https://github.com/muhammadsammy/free-vscode-csharp/blob/master/debugger.md'

	installer = UnityInstaller()

	async def start(self, log: core.Logger, configuration: dap.ConfigurationExpanded):
		install_path = self.installer.install_path()
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

		command = ['mono', '/home/bea/Code/unity-dap/bin/Release/unity-debug-adapter.exe']

		return dap.StdioTransport(command, stderr=log.error)
