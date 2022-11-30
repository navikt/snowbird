build:
	rm -r dist
	poetry build
	poetry check
	twine check ./dist/*