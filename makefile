SPHINXSOURCEDIR	= docs
SPHINXBUILDDIR  = docs/_build

docs: makefile
	sphinx-apidoc -o "$(SPHINXSOURCEDIR)" .
	sphinx-build -M html "$(SPHINXSOURCEDIR)" "$(SPHINXBUILDDIR)"
