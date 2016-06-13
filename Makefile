algoRun:
	python algoRun.py

install_all:
	sudo apt-get update
	sudo apt-get install iptables-persistent
	sudo apt-get install libblas-dev
	sudo apt-get install liblapack-dev
	sudo apt-get install gfortran
	sudo apt-get install python-setuptools
	sudo apt-get install python-matplotlib
	sudo apt-get install python-sklearn
	sudo apt-get install python-numpy
	sudo apt-get install python-scipy
	sudo apt-get install python-pymssql

clean:
	rm -rf *.pyo *.pyc


