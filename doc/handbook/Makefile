
.PHONY: figures

DOTERR=dot-error.log
FIGURES=figures

all: figures
figures:
	@echo; echo "===> Converting figures (dot)"
	@for fig in ${FIGURES}/mandatory_vars ${FIGURES}/function_calls ${FIGURES}/mcd ${FIGURES}/codasyl ${FIGURES}/dependencies_tree_standalone ${FIGURES}/dependencies_tree_cluster; do \
		dot -o $$fig.eps -Tps $$fig.dot 2>${DOTERR} && \
		dot -o $$fig.svg -Tsvg $$fig.dot 2>${DOTERR} && \
		dot -o $$fig.png -Tpng $$fig.dot 2>${DOTERR}; \
	done
