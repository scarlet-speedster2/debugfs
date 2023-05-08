install:
	sudo pip3 install -r requirement.txt

run:
ifndef ARG
	@echo "Please provide a Device File name as argument."
	@echo "For eg. make run ARG=/dev/sdb9."
else
	sudo python3 main.py $(ARG)
endif	

.PHONY: install run

