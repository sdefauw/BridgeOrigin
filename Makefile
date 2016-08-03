all: clean init

init: bower

bower:
	cd brorig/www/; bower update; cd -

distrib:
	python setup.py sdist

install: distrib
	sudo pip install dist/*.tar.gz

uninstall:
	sudo pip uninstall Bridge-Origin

upgrade: distrib
	sudo pip install --upgrade dist/*.tar.gz

cleandata:
	rm -rf brorig/data/

clean: cleandata
	rm -rf brorig/www/libs/* dist/ build/ *.egg-info/
