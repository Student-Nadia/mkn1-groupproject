.PHONY: build test clean

build:
	$(MAKE) -C filter

test:
	PYTHONPATH=common:logd:cli:authd:integrityd python3 -m unittest discover -s tests/unit -t tests/unit -p "test_*.py" -v

clean:
	$(MAKE) -C filter clean
