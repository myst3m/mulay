# mulay の実行イメージ。ホストで clay build した ./mulay を入れる (docker build -f deploy/Dockerfile -t mulay:dev .)。
#   アプリは /app にマウントして渡す: mulay run /app [key=value ...] (プロジェクトのディレクトリ、jar、単独の xml)
#   プロパティは key=value の引数か環境変数 (${name} が環境変数からも読まれる)
#   ルート FS は読み取り専用で動く。書き込むのは永続ストア (ObjectStore、VM) の作業ディレクトリ /work だけ
#   (emptyDir を /work にマウントする。使わないアプリは何も書かない)
# mulay がリンクするのは libc と libm だけ (glibc)。ca-certificates はシステムの CA (TLS の相手の確かめ)
FROM debian:trixie-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir /app /work && chown 1000:1000 /work
COPY mulay /usr/local/bin/mulay
USER 1000:1000
WORKDIR /work
ENTRYPOINT ["mulay"]
CMD ["run", "/app"]
