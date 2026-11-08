#!/usr/bin/env bash
# protoc を ~/.m2 の com.google.protobuf:protoc から動かす (well-known types の .proto は protobuf-java の jar から取り出す)。
#   tools/protoc.sh --proto_path=<dir> --include_imports --descriptor_set_out=<out.desc> <file.proto>...
# 記述子の作り直し:
#   tools/protoc.sh --proto_path=test/fixtures/dw/protobuf_test/proto --include_imports \
#     --descriptor_set_out=test/fixtures/dw/protobuf_test/types.desc test/fixtures/dw/protobuf_test/proto/types.proto test/fixtures/dw/protobuf_test/proto/p2.proto
set -eu
cd "$(dirname "$0")/.."
V=4.29.3
M2="$HOME/.m2/repository/com/google/protobuf"
bin=target/protoc/protoc-$V
inc=target/protoc/include
if [ ! -x "$bin" ]; then
  mkdir -p target/protoc
  cp "$M2/protoc/$V/protoc-$V-linux-x86_64.exe" "$bin"
  chmod +x "$bin"
fi
if [ ! -f "$inc/google/protobuf/timestamp.proto" ]; then
  mkdir -p "$inc"
  (cd "$inc" && unzip -q -o "$M2/protobuf-java/$V/protobuf-java-$V.jar" 'google/protobuf/*.proto')
fi
exec "$bin" --proto_path="$inc" "$@"
