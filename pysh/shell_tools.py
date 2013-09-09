import pipes


class ShellCommand(object):
	def __init__(self, command):
		self.command = command

	def __str__(self):
		return str(self.command)

	def __repr__(self):
		return '%s(%r)' % (type(self).__name__, self.command)

class ShellGroup(ShellCommand):
	def __str__(self):
		command = str(self.command).strip()
		return '{\n%s\n}' % command


class ShellAdvertised(ShellCommand):
	def __init__(self, advertised_command, actual_command=None):
		self.advertised_command = advertised_command
		self.actual_command = actual_command or advertised_command

	def __str__(self):
		def colorize(string):
			return '\\x1b[36;1m%s\\x1b[0m' % string

		to_print = '$ %s\\n' % '\\n> '.join(map(colorize, str(self.advertised_command).replace('%', '%%').split('\n')))
		print_command = 'printf %s' % pipes.quote(to_print)
		return str(ShellAnd(print_command, self.actual_command))

	def __repr__(self):
		if self.actual_command is not self.advertised_command:
			return '%s(%r, ACTUAL(%r))' % (type(self).__name__, self.advertised_command, self.actual_command)
		return '%s(%r)' % (type(self).__name__, self.advertised_command)


class ShellTest(ShellCommand):
	def __str__(self):
		return '[ %s ]' % self.command


class ShellIf(ShellCommand):
	def __init__(self, cond, success_command, failure_command=None):
		self.cond = cond
		self.success_command = success_command
		self.failure_command = failure_command

	def __str__(self):
		if_cond = 'if %s; then' % self.cond
		do_success = str(self.success_command)
		do_failure = 'else\n%s' % self.failure_command if self.failure_command else ''
		end = 'fi'

		return '\n'.join(filter(bool, [if_cond, do_success, do_failure, end]))

	def __repr__(self):
		if self.failure_command:
			return '%s(IF(%r) THEN(%r) ELSE(%r))' % (type(self).__name__, self.cond, self.success_command, self.failure_command)
		return '%s(IF(%r) THEN(%r))' % (type(self).__name__, self.cond, self.success_command)


class ShellNot(ShellCommand):
	def __str__(self):
		return '! %s' % ShellGroup(self.command)


class ShellAnd(ShellCommand):
	def __init__(self, *commands):
		self.commands = commands

	def __str__(self):
		return ' && '.join(map(lambda command: str(ShellGroup(command)), self.commands))

	def __repr__(self):
		return '%s(%s)' % (type(self).__name__, ', '.join(map(repr, self.commands)))


class ShellOr(ShellCommand):
	def __init__(self, *commands):
		self.commands = commands

	def __str__(self):
		return ' || '.join(map(lambda command: str(ShellGroup(command)), self.commands))

	def __repr__(self):
		return '%s(%s)' % (type(self).__name__, ', '.join(map(repr, self.commands)))


class ShellChain(ShellCommand):
	def __init__(self, *commands):
		self.commands = commands

	def __str__(self):
		return '\n'.join(map(str, self.commands))

	def __repr__(self):
		return '%s(%s)' % (type(self).__name__, ', '.join(map(repr, self.commands)))


class ShellBackground(ShellCommand):
	def __str__(self):
		return '%s &' % self.command


class ShellSubshell(ShellCommand):
	def __str__(self):
		return '(%s)' % self.command


class ShellCapture(ShellCommand):
	def __str__(self):
		return '$(%s)' % self.command


class ShellPipe(ShellCommand):
	def __init__(self, *commands):
		self.commands = commands

	def __str__(self):
		return ' | '.join(map(str, self.commands))

	def __repr__(self):
		return '%s(%s)' % (type(self).__name__, ', '.join(map(repr, self.commands)))


class ShellRedirect(ShellCommand):
	def __init__(self, command, outfile, include_stderr=False):
		self.command = command
		self.outfile = outfile
		self.include_stderr = include_stderr

	def __str__(self):
		redirect = '%s > %s' % (ShellGroup(self.command), self.outfile)
		if self.include_stderr:
			return '%s 2>&1' % redirect
		return redirect

	def __repr__(self):
		if self.include_stderr:
			return '%s(REDIRECT(%r) AND STDERR TO (%r))' % (type(self).__name__, self.command, self.outfile)
		return '%s(REDIRECT(%r) TO (%r))' % (type(self).__name__, self.command, self.outfile)


class ShellAppend(ShellCommand):
	def __init__(self, command, outfile, include_stderr=False):
		self.command = command
		self.outfile = outfile
		self.include_stderr = include_stderr

	def __str__(self):
		append = '%s >> %s' % (ShellGroup(self.command), self.outfile)
		if self.include_stderr:
			return '%s 2>&1' % append
		return append

	def __repr__(self):
		if self.include_stderr:
			return '%s(APPEND(%r) AND STDERR TO (%r))' % (type(self).__name__, self.command, self.outfile)
		return '%s(APPEND(%r) TO (%r))' % (type(self).__name__, self.command, self.outfile)


class ShellSilent(ShellRedirect):
	def __init__(self, command):
		super(ShellSilent, self).__init__(command, '/dev/null', include_stderr=True)

	def __repr__(self):
		return '%s(%r)' % (type(self).__name__, self.command)


class ShellLogin(ShellCommand):
	def __str__(self):
		return 'bash --login -c %s' % pipes.quote(str(self.command))


class ShellSudo(ShellCommand):
	def __str__(self):
		return 'sudo -E HOME="$HOME" PATH="$PATH" bash -c %s' % pipes.quote(str(self.command))
