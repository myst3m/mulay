#!/usr/bin/env python3
# SSH の binary packet (RFC 4253 6 節) の golden を作り、test/ssh/packet_test.clay に書く。
#   aes*-ctr + hmac-sha2-* (etm を含む)、aes*-gcm@openssh.com: paramiko の Packetizer が送ったバイト列 (別の実装)
#   chacha20-poly1305@openssh.com: paramiko に無いので、ここで cryptography (OpenSSL) の ChaCha20 と Poly1305 から組む
#     (PROTOCOL.chacha20poly1305 の読みの確かめにしかならない。本当の確かめは実サーバーとの接続)
# 各方式で 3 つのパケットを続けて封じる (CTR のカウンタと連番が次のパケットに引き継がれること)。連番は 0xfffffffe から
# 始め、32 ビットで一周するところを含む。詰め物は Packetizer が乱数で選んだものを復号して取り出し、テストはそれを渡して
# 同じバイト列になることを見る。
# 使い方: python3 -I tools/gen-ssh-packet-golden.py > test/ssh/packet_test.clay  (paramiko 5.0.0、cryptography 49.0.0 で作った)
import hashlib, hmac, socket, struct, sys
import paramiko
from paramiko.packet import Packetizer
from paramiko.message import Message
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.poly1305 import Poly1305

def pat(n, m, a):
    return bytes((i * m + a) % 256 for i in range(n))

PAYLOADS = [bytes([94]) + pat(0, 1, 0), bytes([94]) + pat(36, 7, 3), bytes([94]) + pat(299, 13, 5)]
SEQ0 = 0xfffffffe

def read_exact(s, n):
    out = b""
    while len(out) < n:
        out += s.recv(n - len(out))
    return out

def recv_all(s):
    s.setblocking(False)
    out = b""
    try:
        while True:
            x = s.recv(65536)
            if not x: break
            out += x
    except BlockingIOError:
        pass
    s.setblocking(True)
    return out

def paramiko_vectors(cipher, mac):
    keylen = {"aes128-ctr": 16, "aes192-ctr": 24, "aes256-ctr": 32, "aes128-gcm@openssh.com": 16, "aes256-gcm@openssh.com": 32}[cipher]
    gcm = cipher.endswith("gcm@openssh.com")
    key = pat(keylen, 11, 5)
    iv = pat(12 if gcm else 16, 13, 7)
    mac_name = mac.replace("-etm@openssh.com", "")
    mac_engine = {"hmac-sha2-256": hashlib.sha256, "hmac-sha2-512": hashlib.sha512}.get(mac_name)
    mac_key = pat(mac_engine().digest_size, 17, 9) if mac_engine else b""
    etm = mac.endswith("-etm@openssh.com")
    a, b = socket.socketpair()
    p = Packetizer(a)
    if gcm:
        p.set_outbound_cipher(AESGCM(key), 16, None, 16, None, aead=True, iv_out=iv)
    else:
        enc = Cipher(algorithms.AES(key), modes.CTR(iv)).encryptor()
        p.set_outbound_cipher(enc, 16, mac_engine, mac_engine().digest_size, mac_key, sdctr=True, etm=etm)
    p._Packetizer__sequence_number_out = SEQ0
    p._initial_kex_done = True
    out = []
    dec = None if gcm else Cipher(algorithms.AES(key), modes.CTR(iv)).decryptor()
    giv = iv
    for pl in PAYLOADS:
        p.send_message(Message(pl))
        wire = recv_all(b)
        mlen = 16 if gcm else mac_engine().digest_size
        body = wire[: len(wire) - mlen]
        if gcm:
            plain = wire[:4] + AESGCM(key).decrypt(giv, wire[4:], wire[:4])
            giv = giv[:4] + struct.pack(">Q", (struct.unpack(">Q", giv[4:])[0] + 1) & 0xffffffffffffffff)
        elif etm:
            plain = body[:4] + dec.update(body[4:])
        else:
            plain = dec.update(body)
        padlen = plain[4]
        pad = plain[len(plain) - padlen:]
        assert plain[5 : len(plain) - padlen] == pl
        out.append((pl, pad, wire))
    a.close(); b.close()
    return {"cipher": cipher, "mac": mac, "key": key, "iv": iv, "mac_key": mac_key, "packets": out}

def chacha_stream(key, seq, counter, data):
    nonce = struct.pack("<Q", counter) + struct.pack(">Q", seq)
    return Cipher(algorithms.ChaCha20(key, nonce), None).encryptor().update(data)

def chacha_vectors():
    key = pat(64, 19, 1)
    k2, k1 = key[:32], key[32:]
    out = []
    seq = SEQ0
    for i, pl in enumerate(PAYLOADS):
        bs = 8
        padlen = bs - ((1 + len(pl)) % bs)
        if padlen < 4: padlen += bs
        pad = pat(padlen, 23, i + 1)
        plain = struct.pack(">I", 1 + len(pl) + padlen) + bytes([padlen]) + pl + pad
        elen = chacha_stream(k1, seq, 0, plain[:4])
        polykey = chacha_stream(k2, seq, 0, bytes(32))
        ebody = chacha_stream(k2, seq, 1, plain[4:])
        tag = Poly1305.generate_tag(polykey, elen + ebody)
        out.append((pl, pad, elen + ebody + tag))
        seq = (seq + 1) & 0xffffffff
    return {"cipher": "chacha20-poly1305@openssh.com", "mac": "", "key": key, "iv": b"", "mac_key": b"", "packets": out}

def none_vectors():
    out = []
    for i, pl in enumerate(PAYLOADS):
        padlen = 8 - ((5 + len(pl)) % 8)
        if padlen < 4: padlen += 8
        pad = pat(padlen, 29, i)
        out.append((pl, pad, struct.pack(">I", 1 + len(pl) + padlen) + bytes([padlen]) + pl + pad))
    return {"cipher": "none", "mac": "", "key": b"", "iv": b"", "mac_key": b"", "packets": out}

SETS = [
    none_vectors(),
    paramiko_vectors("aes128-ctr", "hmac-sha2-256"),
    paramiko_vectors("aes256-ctr", "hmac-sha2-512"),
    paramiko_vectors("aes192-ctr", "hmac-sha2-256-etm@openssh.com"),
    paramiko_vectors("aes256-ctr", "hmac-sha2-512-etm@openssh.com"),
    paramiko_vectors("aes128-gcm@openssh.com", ""),
    paramiko_vectors("aes256-gcm@openssh.com", ""),
    chacha_vectors(),
]

def h(b): return b.hex()

print(";; tools/gen-ssh-packet-golden.py で作った (手で直さない)。方式ごとに 3 つのパケットを、連番 0xfffffffe から続けて封じたもの")
print("(ns packet-test (:require [mulay.lib.sshpkt :as p] [mulay.dw.lib.binaries :as bin]))")
print()
print("(defn- hexd Int [c: Int] (if (<= c 57) (- c 48) (- c 87)))")
print("(defn- unhex Str [h: &Str]")
print("  (loop [i 0 out \"\"] (if (>= i (count h)) out")
print("    (recur (+ i 2) (str out (chr (+ (* 16 (hexd (nth h i))) (hexd (nth h (+ i 1))))))))))")
print()
print(";; 3 つのパケットを順に封じて、golden と同じバイト列になるか")
print("(defn- seal3 Bool [cipher: Str mac: Str key: Str iv: Str mk: Str pl0: Str pad0: Str w0: Str pl1: Str pad1: Str w1: Str pl2: Str pad2: Str w2: Str]")
print("  (let [[d0 err] (p/new-dir cipher mac (unhex key) (unhex iv) (unhex mk))")
print("        [x0 d1] (p/seal-padded (p/with-seq d0 4294967294) (unhex pl0) (unhex pad0))")
print("        [x1 d2] (p/seal-padded d1 (unhex pl1) (unhex pad1))")
print("        [x2 d3] (p/seal-padded d2 (unhex pl2) (unhex pad2))]")
print("    (and (= err \"\") (= (bin/hex-lower x0) w0) (= (bin/hex-lower x1) w1) (= (bin/hex-lower x2) w2))))")
print()
print(";; 3 つをつないだバイト列から、順に取り出せるか (最後の 1 バイトが無ければ need-more)")
print("(defn- open3 Bool [cipher: Str mac: Str key: Str iv: Str mk: Str pl0: Str w0: Str pl1: Str w1: Str pl2: Str w2: Str]")
print("  (let [[d0 err] (p/new-dir cipher mac (unhex key) (unhex iv) (unhex mk))")
print("        buf (unhex (str w0 w1 w2))")
print("        [s0 x0 n0 d1 e0] (p/unseal (p/with-seq d0 4294967294) buf)")
print("        rest1 (subs buf n0 (count buf))")
print("        [s1 x1 n1 d2 e1] (p/unseal d1 rest1)")
print("        rest2 (subs rest1 n1 (count rest1))")
print("        [sm xm nm dm em] (p/unseal d2 (subs rest2 0 (- (count rest2) 1)))")
print("        [s2 x2 n2 d3 e2] (p/unseal d2 rest2)]")
print("    (and (= err \"\") (= s0 0) (= s1 0) (= s2 0) (= sm 1) (= n2 (count rest2))")
print("         (= (bin/hex-lower x0) pl0) (= (bin/hex-lower x1) pl1) (= (bin/hex-lower x2) pl2))))")
print()
for s in SETS:
    name = s["cipher"] + ("-" + s["mac"] if s["mac"] else "")
    t = name.replace("@openssh.com", "").replace(".", "-")
    ps = s["packets"]
    args = f'"{s["cipher"]}" "{s["mac"]}" "{h(s["key"])}" "{h(s["iv"])}" "{h(s["mac_key"])}"'
    print(f"(deftest seal-{t}")
    print(f"  (is (seal3 {args}")
    for pl, pad, w in ps:
        print(f'             "{h(pl)}" "{h(pad)}" "{h(w)}"')
    print("             )))")
    print()
    print(f"(deftest open-{t}")
    print(f"  (is (open3 {args}")
    for pl, pad, w in ps:
        print(f'             "{h(pl)}" "{h(w)}"')
    print("             )))")
    print()
