# 011 — SSH と SFTP は純 Clay の同期のクライアントにし、方式を絞り、strict kex と known_hosts の照合を持ち、SFTP の読み書きは要求を重ねる

状態: **採用** (2026-10-11。lib/ssh は 66af45e、lib/sftp を libssh2 から替えたのは 91be748)

## 決定

### 層

- `mulay.lib.sshwire` (RFC 4251 のデータ型)、`mulay.lib.sshpkt` (binary packet)、`mulay.lib.sshkex` (鍵交換の部品)、`mulay.lib.sshkey`
  (ホスト鍵の署名と known_hosts) はソケットを知らない。`mulay.lib.ssh` が転送・認証・チャネルを、`mulay.lib.sftp` が SFTP v3 を持つ。
- 1 つの `Conn` (と `Sess`) は 1 本の TCP 接続で、同時に複数のスレッドから使わない。`Conn` は値で受け取り、更新したものを返す (同期で動く)。

### SSH

- 方式: 鍵交換は curve25519-sha256 と diffie-hellman-group14-sha256 / group16-sha512 (RFC 3526 の MODP、生成元 2)。暗号は
  chacha20-poly1305@openssh.com、aes128/256-gcm@openssh.com、aes128/192/256-ctr と hmac-sha2-256/512 (と -etm)。ホスト鍵は ssh-ed25519、
  ecdsa-sha2-nistp256、rsa-sha2-256/512。`client-lists` は CPU に AES 命令があるとき AES-GCM を chacha20-poly1305 より先に置く。
  (絞ったことは docs/compat/deviations.md の SFTP の行)
- DH の秘密の指数は 2^1024 未満 (OpenSSH と同じく鍵の長さの 2 倍以上のビット数)。相手の公開値は 1 < f < p - 1 を確かめる。
- strict kex (OpenSSH の kex-strict-*-v00、Terrapin の対策): 最初の鍵交換の間に鍵交換以外のメッセージが来れば失敗にし、NEWKEYS の
  たびに連番を 0 に戻す。strict かどうかは最初の鍵交換で決まり、後の KEXINIT の印は見ない (OpenSSH の PROTOCOL の kex-strict の節)。
  サーバーの最初のパケットは KEXINIT でなければならない。
- 鍵交換の署名は known_hosts が無くても常に確かめる。RSA の法は 1024 ビット以上 (OpenSSH の RequiredRSASize の既定)。
- known_hosts に行のある種類のホスト鍵の方式を先に出す (`connect-with` の hostkeys、`sshkey/known-algorithms`)。そうすればサーバーは
  その種類の鍵を使う。kex・enc・mac を 1 つに絞る引数は、テストで方式ごとに実サーバーと確かめるため。
- known_hosts の照合 (`known?`): sshd(8) の SSH_KNOWN_HOSTS FILE FORMAT。同じ名前で同じ鍵の @revoked の行があれば他の行に関わらず
  false。@cert-authority の行は使わない。読めない行は飛ばす。
- 転送の層: IGNORE・DEBUG・UNIMPLEMENTED・EXT_INFO は読み捨て、GLOBAL_REQUEST は want-reply なら REQUEST_FAILURE、DISCONNECT は失敗。
  チャネルの層: CHANNEL_REQUEST は want-reply なら CHANNEL_FAILURE、EXTENDED_DATA は窓だけ数えて捨てる。
- こちらの窓は `LOCAL-WINDOW` で、半分を使ったら WINDOW_ADJUST で戻す。送りと受けの合計が `REKEY-BYTES` (1 GB) を超えたら、
  こちらから鍵交換をやり直す。こちらから始めた鍵交換で、サーバーの KEXINIT より前に届いた鍵交換以外のメッセージは held に貯めて後で渡す。
- binary packet (`sshpkt`): 長さの欄は `MAX-PACKET` (256 KB) まで。MAC (タグ) は復号の前に、時間が一定の比較 (`ct-eq`) で確かめる。
  連番は 32 ビットで一周する。`unseal-at` は受けたバイト列をパケットごとに詰め直さずに続けて取り出す。

### SFTP

- 読み書きは要求を重ねて出す (先読み)。1 回の大きさはサーバーの limits@openssh.com に従い、無ければ `DEFAULT-IO` (32 KB)。重ねる要求は
  `IN-FLIGHT` (4 MB) まで。書き込みの答えは、OpenSSH が順に答えるので一番古い要求から受ける。
- 読み込みは短い答えなら残りを頼み直し、EOF は STATUS の EOF だけで決める。
- `rename` は v3 の RENAME (先があれば失敗する)。上書きは呼ぶ側で先に消す (`overwrite` は使わない)。
- 接続が切れたなどで答えが得られなければ状態コードは `CONNECTION-LOST`。

## 理由

- 外部ライブラリ (libssh2) を外す。232 MB の書き込みと読み込み (同じ機械、CPU 3 に固定) で純 Clay 322 / 300 ms、libssh2 843 / 752 ms
  (91be748)。
- 状態を値で持ち回す書き方と Sess の Atom の扱いは ADR 001。

## 場所

- `mulay.lib.ssh/connect-with`、`my-kexinit`、`kex-start`、`recv-kex`、`finish-kex`、`dh-pm1`、`chan-send`、`LOCAL-WINDOW`、`REKEY-BYTES`
- `mulay.lib.sshkex/client-lists`、`negotiate`、`mulay.lib.sshkey/verify-signature`、`rsa-bits-ok?`、`known?`、`known-algorithms`
- `mulay.lib.sshpkt/MAX-PACKET`、`ct-eq`、`unseal-at`
- `mulay.lib.sftp/DEFAULT-IO`、`IN-FLIGHT`、`write-at`、`read-all`、`rename`、`CONNECTION-LOST`
