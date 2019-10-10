SPHINXSOURCEDIR	= docs
SPHINXBUILDDIR  = docs/_build

docs: Makefile
	sphinx-apidoc -o "$(SPHINXSOURCEDIR)" .
	sphinx-build -M html "$(SPHINXSOURCEDIR)" "$(SPHINXBUILDDIR)"
