PYTHON ?= python3

.PHONY: test evaluate diagram

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m unittest discover -s skills/rustify-validate/tests -v

evaluate:
	$(PYTHON) scripts/evaluate.py

diagram:
	cd docs && latexmk -pdf -interaction=nonstopmode -halt-on-error architecture.tex
	pdftocairo -svg docs/architecture.pdf docs/architecture.svg
	pdftoppm -png -singlefile -r 110 docs/architecture.pdf docs/architecture
