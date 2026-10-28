PYTHON ?= python3

.PHONY: test evaluate diagram

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m unittest discover -s eval/tests -v

evaluate:
	$(PYTHON) eval/main.py score

diagram:
	cd docs && latexmk -pdf -interaction=nonstopmode -halt-on-error architecture.tex
	pdftocairo -svg docs/architecture.pdf docs/architecture.svg
	pdftoppm -png -singlefile -r 110 docs/architecture.pdf docs/architecture
	cd eval/docs/figures && for name in tiers pipeline; do pdflatex -interaction=nonstopmode -halt-on-error $$name.tex && latex -interaction=nonstopmode -halt-on-error $$name.tex && dvisvgm --no-fonts --linkmark=none -o $$name.svg $$name.dvi && pdftoppm -png -singlefile -r 110 $$name.pdf $$name || exit 1; done; rm -f *.aux *.log *.dvi *.out
