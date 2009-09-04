
#include ../doc.pre.mk
#
## Overwrite entry point
#BASE=handbook
#XMLSRC=${BASE}.xml
#DOCNAME=handbook
#
## Custom options for XSLT processor, well suited for books
#XSL_OPTS=--stringparam chapter.autolabel 1 \
#		 --stringparam section.autolabel 1 \
#		 --stringparam table.cell.border.thickness 1px \
#		 --stringparam table.cell.border.style solid \
#		 --stringparam table.borders.with.css 1 \
#		 --stringparam toc.section.depth 1 \
#		 --stringparam section.label.includes.component.label 1
#
#pre-figures:

.PHONY: figures

DOTERR=dot-error.log
FIGURES=figures

all: figures
figures:
	@echo; echo "===> Converting figures (dot)"
	@for fig in ${FIGURES}/mandatory_vars ${FIGURES}/function_calls ${FIGURES}/mcd ${FIGURES}/codasyl; do \
		dot -o $$fig.eps -Tps $$fig.dot 2>${DOTERR} && \
		dot -o $$fig.svg -Tsvg $$fig.dot 2>${DOTERR} && \
		dot -o $$fig.png -Tpng $$fig.dot 2>${DOTERR}; \
	done

#bootstrap:
#	@echo "===> [${DOCNAME}] Building DB entities"
#	@./gen_dict_xml.py
#
#include ../doc.post.mk
