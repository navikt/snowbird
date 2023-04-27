build:
	rm -r dist
	poetry build
	poetry check
	twine check ./dist/*

test:
	poetry run pytest ./tests