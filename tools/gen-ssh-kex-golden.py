#!/usr/bin/env python3
# SSH の鍵交換の部品 (RFC 4253 7 節、RFC 8731) の golden を作り、test/ssh/kex_test.clay に書く。期待値は paramiko (別の実装):
#   KEXINIT の payload: paramiko の Message で組んだもの
#   交換ハッシュ H (curve25519-sha256): paramiko の KexCurve25519._parse_kexecdh_reply と同じ順に Message で組んで SHA-256
#   交換ハッシュ H (diffie-hellman-group14-sha256、group16-sha512): paramiko の KexGroup14 の _parse_kexdh_reply と同じ順
#   DH の素数: paramiko の KexGroup14SHA256.P と KexGroup16SHA512.P (RFC 3526 の 2048 / 4096 ビットの MODP)
#   鍵の導出: paramiko の Transport._compute_key (K は X25519 の 32 バイトを大きい順の符号なし整数とした mpint)
# 使い方: python3 -I tools/gen-ssh-kex-golden.py > test/ssh/kex_test.clay  (paramiko 5.0.0 で作った)
import hashlib, socket
import paramiko
from paramiko.message import Message

def pat(n, m, a):
    return bytes((i * m + a) % 256 for i in range(n))

COOKIE = pat(16, 7, 1)
LISTS = [
    ["curve25519-sha256", "curve25519-sha256@libssh.org", "kex-strict-c-v00@openssh.com"],
    ["ssh-ed25519", "rsa-sha2-512", "rsa-sha2-256"],
    ["aes128-gcm@openssh.com", "chacha20-poly1305@openssh.com", "aes256-ctr"],
    ["aes128-gcm@openssh.com", "chacha20-poly1305@openssh.com", "aes256-ctr"],
    ["hmac-sha2-256-etm@openssh.com", "hmac-sha2-256"],
    ["hmac-sha2-256-etm@openssh.com", "hmac-sha2-256"],
    ["none"], ["none"], [], [],
]

def kexinit(cookie, lists, follows):
    m = Message()
    m.add_byte(bytes([20]))
    m.add_bytes(cookie)
    for l in lists:
        m.add_list(l)
    m.add_boolean(follows)
    m.add_int(0)
    return m.asbytes()

V_C = b"SSH-2.0-mulay_1.0"
V_S = b"SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u10"
I_C = kexinit(COOKIE, LISTS, False)
I_S = kexinit(pat(16, 5, 9), LISTS, False)
K_S = pat(51, 3, 2)
Q_C = pat(32, 9, 4)
Q_S = pat(32, 15, 6)
KRAW = bytes([0x91]) + pat(31, 21, 8)   # 最上位のビットが立つ (mpint に 0 が付く)

hm = Message()
hm.add(V_C.decode(), V_S.decode(), I_C, I_S)
hm.add_string(K_S)
hm.add_string(Q_C)
hm.add_string(Q_S)
K = int(KRAW.hex(), 16)
hm.add_mpint(K)
H = hashlib.sha256(hm.asbytes()).digest()

from paramiko.kex_group14 import KexGroup14SHA256
from paramiko.kex_group16 import KexGroup16SHA512
DH_E = int.from_bytes(bytes([0x83]) + pat(255, 17, 2), "big")
DH_F = int.from_bytes(pat(256, 23, 5), "big")
def dh_hash(algo):
    m = Message()
    m.add(V_C.decode(), V_S.decode(), I_C, I_S)
    m.add_string(K_S)
    m.add_mpint(DH_E)
    m.add_mpint(DH_F)
    m.add_mpint(K)
    return algo(m.asbytes()).digest()
H14 = dh_hash(hashlib.sha256)
H16 = dh_hash(hashlib.sha512)
def ib(n): return n.to_bytes((n.bit_length() + 7) // 8, "big")

a, b = socket.socketpair()
t = paramiko.Transport(a)
class Eng: hash_algo = hashlib.sha256
t.kex_engine = Eng()
t.K = K
t.H = H
t.session_id = pat(32, 27, 3)
keys = {c: t._compute_key(c, 64 if c in "CD" else 16 if c in "AB" else 32) for c in "ABCDEF"}
long_key = t._compute_key("C", 100)
a.close(); b.close()

def h(x): return x.hex()

print(";; tools/gen-ssh-kex-golden.py で作った (手で直さない)。期待値は paramiko 5.0.0")
print("(ns kex-test (:require [mulay.lib.sshkex :as kx] [mulay.dw.lib.binaries :as bin]))")
print()
print("(defn- hexd Int [c: Int] (if (<= c 57) (- c 48) (- c 87)))")
print("(defn- unhex Str [h: &Str]")
print("  (loop [i 0 out \"\"] (if (>= i (count h)) out")
print("    (recur (+ i 2) (str out (chr (+ (* 16 (hexd (nth h i))) (hexd (nth h (+ i 1))))))))))")
print()
print("(defn- lists Vec(Vec(Str)) []")
print("  [" + " ".join("[" + " ".join(f'"{x}"' for x in l) + "]" if l else "(let [e: Vec(Str) []] e)" for l in LISTS) + "])")
print()
print(";; KEXINIT の payload を作ると paramiko と同じバイト列になり、読み戻すと同じ中身になる")
print("(deftest kexinit-build")
print(f'  (is (= (bin/hex-lower (kx/kexinit-payload (kx/->Kexinit (unhex "{h(COOKIE)}") (lists) false))) "{h(I_C)}")))')
print()
print("(deftest kexinit-parse")
print(f'  (let [[k ok] (kx/parse-kexinit (unhex "{h(I_S)}"))]')
print("    (is ok)")
print(f'    (is (= (bin/hex-lower (:cookie k)) "{h(pat(16, 5, 9))}"))')
print("    (is (= (:lists k) (lists)))")
print("    (is (not (:first-follows k)))")
print(f'    (is (= (bin/hex-lower (kx/kexinit-payload k)) "{h(I_S)}"))))')
print()
print(";; curve25519-sha256 の交換ハッシュ H (RFC 8731 3 節)。K の最上位のビットが立つので mpint に 0 が付く")
print("(deftest exchange-hash")
print(f'  (is (= (bin/hex-lower (kx/exchange-hash "SHA256" "{V_C.decode()}" "{V_S.decode()}" (unhex "{h(I_C)}") (unhex "{h(I_S)}")')
print(f'                                          (unhex "{h(K_S)}") (unhex "{h(Q_C)}") (unhex "{h(Q_S)}") (unhex "{h(KRAW)}")))')
print(f'         "{h(H)}")))')
print()
print(";; 鍵の導出 (RFC 4253 7.2): A〜F と、ハッシュより長い鍵 (100 バイト、K1 || K2 || ..)")
print("(deftest derive-keys")
for c in "ABCDEF":
    n = len(keys[c])
    print(f'  (is (= (bin/hex-lower (kx/derive "SHA256" (unhex "{h(KRAW)}") (unhex "{h(H)}") "{c}" (unhex "{h(pat(32, 27, 3))}") {n})) "{h(keys[c])}"))')
print(f'  (is (= (bin/hex-lower (kx/derive "SHA256" (unhex "{h(KRAW)}") (unhex "{h(H)}") "C" (unhex "{h(pat(32, 27, 3))}") 100)) "{h(long_key)}")))')
print()
print(";; DH (diffie-hellman-group14-sha256 / group16-sha512) の交換ハッシュ: e と f は mpint (RFC 4253 8 節)")
print("(deftest exchange-hash-dh")
for name, hname, hv in (("group14", "SHA256", H14), ("group16", "SHA512", H16)):
    print(f'  (is (= (bin/hex-lower (kx/exchange-hash-dh "{hname}" "{V_C.decode()}" "{V_S.decode()}" (unhex "{h(I_C)}") (unhex "{h(I_S)}")')
    print(f'                                             (unhex "{h(K_S)}") (unhex "{h(ib(DH_E))}") (unhex "{h(ib(DH_F))}") (unhex "{h(KRAW)}")))')
    print(f'         "{h(hv)}"))')
print("  )")
print()
print(";; DH の素数と生成元、要約の名前")
print("(deftest dh-groups")
print(f'  (is (= (bin/hex-lower (kx/dh-prime "diffie-hellman-group14-sha256")) "{h(ib(KexGroup14SHA256.P))}"))')
print(f'  (is (= (bin/hex-lower (kx/dh-prime "diffie-hellman-group16-sha512")) "{h(ib(KexGroup16SHA512.P))}"))')
print('  (is (= (kx/dh-prime "curve25519-sha256") ""))')
print('  (is (= (kx/kex-hash "diffie-hellman-group16-sha512") "SHA512"))')
print('  (is (= (kx/kex-hash "diffie-hellman-group14-sha256") "SHA256"))')
print('  (is (= (kx/kex-hash "curve25519-sha256@libssh.org") "SHA256")))')
