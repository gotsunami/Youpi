#
# $Id$

include ../doc.pre.mk

# Overwrite entry point
BASE=handbook
XMLSRC=${BASE}.xml

DOCNAME=handbook
FIGURES=figures
# Custom options for XSLT processor, well suited for books
XSL_OPTS=--stringparam chapter.autolabel 1 \
		 --stringparam section.autolabel 0 \
		 --stringparam table.cell.border.thickness 1px \
		 --stringparam table.cell.border.style solid \
		 --stringparam table.borders.with.css 1

pre-figures:
	@echo; echo "===> [${DOCNAME}] Converting figures (dot)"
	@for fig in ${FIGURES}/mandatory_vars ${FIGURES}/function_calls; do \
		dot -o $$fig.eps -Tps $$fig.dot && \
		dot -o $$fig.svg -Tsvg $$fig.dot && \
		dot -o $$fig.png -Tpng $$fig.dot; \
	done

bootstrap:
	@echo "===> [${DOCNAME}] Building DB entities"
	@./gen_dict_xml.py

include ../doc.post.mk
