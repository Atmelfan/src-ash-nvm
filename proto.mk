PROTOC = protoc

PROTO_GENERATED = $(PROTO_SOURCES:.proto=_pb2.py)
PROTO_INCLUDE_OPTIONS = $(addprefix -I ,$(PROTO_INCLUDE))

.PHONY: proto
proto: $(PROTO_GENERATED)

%_pb2.py : %.proto
	$(PROTOC) -I . $(PROTO_INCLUDE_OPTIONS) --python_out=. $^

.PHONY: clean-proto
clean-proto:
	rm -f $(PROTO_GENERATED)