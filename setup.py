from setuptools import setup, find_packages

setup(
	name="pysh",
	version="0.1.0",
	description="Python shell deconstruction",
	packages=find_packages(exclude=[
		"bin",
		"tests",
		]),
)
