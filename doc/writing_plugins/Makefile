#
# $Id$

include ../doc.pre.mk

# Overwrite entry point
BASE=writing_plugins
XMLSRC=${BASE}.xml

DOCNAME=writing_plugins
FIGURES=figures

pre-figures:
	@echo; echo "===> [${DOCNAME}] Converting figures (dot)"
	@for fig in ${FIGURES}/mandatory_vars ${FIGURES}/function_calls; do \
		dot -o $$fig.eps -Tps $$fig.dot && \
		dot -o $$fig.svg -Tsvg $$fig.dot && \
		dot -o $$fig.png -Tpng $$fig.dot; \
	done

include ../doc.post.mk
