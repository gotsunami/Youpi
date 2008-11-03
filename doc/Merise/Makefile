
# To be parsed with GNU make
#
SRC=merise

.PHONY: all view v p clean

all: ${SRC}.tex
	@dot -o mcd.eps -Tps mcd.dot
	@dot -o codasyl.eps -Tps codasyl.dot
	@latex $^ && latex $^
	@dvips ${SRC}.dvi -o ${SRC}.ps && ps2pdf ${SRC}.ps

view: v

v:
	xdvi ${SRC}.dvi

p:
	xpdf ${SRC}.pdf

clean:
	@rm -f *~ *.aux *.log *.toc *.log
