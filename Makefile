PLATFORM ?= linux/amd64
PUSH ?= 0
REPOSITORY := $(if $(USERNAME),$(USERNAME)/,)$(IMAGENAME)
OUTPUT := $(if $(filter 1 true yes,$(PUSH)),--push,--load)

.DEFAULT_GOAL := all
.PHONY: all check-env

all: check-env
	docker buildx build --platform "$(PLATFORM)" -t "$(REPOSITORY):latest" $(OUTPUT) .

check-env:
	@test -n "$(IMAGENAME)" || { echo "IMAGENAME is required"; exit 1; }
