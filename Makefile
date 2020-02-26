CSCIS = host recorder remote test body

.PHONY: all
all: common cscis

.PHONY: clean
clean: clean-common clean-cscis

.PHONY: cscis
cscis: common
	@for dir in $(CSCIS); do \
	  $(MAKE) -C $$dir; \
	done

.PHONY: clean-cscis
clean-cscis:
	@for dir in $(CSCIS); do \
	  $(MAKE) -C $$dir clean; \
	done

.PHONY: common
common:
	@$(MAKE) -C common

.PHONY: clean-common
clean-common:
	@$(MAKE) -C common clean