.PHONY: test clean
.ONESHELL:

install:
	uv sync
	uv pip install -e ../../traiter/traiter
	uv run -- python -m spacy download en_core_web_md

test:
	uv run -m unittest discover

clean:
	rm -rf .venv
	rm -rf build
	find -iname "*.pyc" -delete
