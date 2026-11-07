"""Minimal pure-Python Parquet reader (flat schemas; PLAIN/dictionary; snappy/gzip/none)."""
import struct, zlib

class TC:
    def __init__(s, b, p=0): s.b, s.p = b, p
    def byte(s):
        v = s.b[s.p]; s.p += 1; return v
    def varint(s):
        r = sh = 0
        while True:
            c = s.byte(); r |= (c & 0x7F) << sh; sh += 7
            if not c & 0x80: return r
    def zz(s):
        n = s.varint(); return (n >> 1) ^ -(n & 1)
    def val(s, t):
        if t == 1: return True
        if t == 2: return False
        if t == 3: v = struct.unpack('b', bytes([s.byte()]))[0]; return v
        if t in (4, 5, 6): return s.zz()
        if t == 7: v = struct.unpack('<d', s.b[s.p:s.p+8])[0]; s.p += 8; return v
        if t == 8:
            n = s.varint(); v = s.b[s.p:s.p+n]; s.p += n; return v
        if t in (9, 10):
            h = s.byte(); n = h >> 4; et = h & 0xF
            if n == 15: n = s.varint()
            if et in (1, 2): return [s.byte() == 1 for _ in range(n)]
            return [s.val(et) for _ in range(n)]
        if t == 11:
            n = s.varint()
            if n == 0: return {}
            kv = s.byte(); kt, vt = kv >> 4, kv & 0xF
            return {s.val(kt): s.val(vt) for _ in range(n)}
        if t == 12: return s.struct()
        raise ValueError(t)
    def struct(s):
        d = {}; fid = 0
        while True:
            h = s.byte()
            if h == 0: return d
            delta, t = h >> 4, h & 0xF
            fid = fid + delta if delta else s.zz()
            d[fid] = s.val(t)

def snappy(b):
    p = 0; n = sh = 0
    while True:
        c = b[p]; p += 1; n |= (c & 0x7F) << sh; sh += 7
        if not c & 0x80: break
    out = bytearray()
    while p < len(b):
        tag = b[p]; p += 1; t = tag & 3
        if t == 0:
            ln = tag >> 2
            if ln >= 60:
                k = ln - 59; ln = int.from_bytes(b[p:p+k], 'little'); p += k
            ln += 1; out += b[p:p+ln]; p += ln; continue
        if t == 1:
            ln = ((tag >> 2) & 7) + 4; off = ((tag >> 5) << 8) | b[p]; p += 1
        elif t == 2:
            ln = (tag >> 2) + 1; off = int.from_bytes(b[p:p+2], 'little'); p += 2
        else:
            ln = (tag >> 2) + 1; off = int.from_bytes(b[p:p+4], 'little'); p += 4
        st = len(out) - off
        if off >= ln: out += out[st:st+ln]
        else:
            for i in range(ln): out.append(out[st+i])
    return bytes(out)

import ctypes, ctypes.util
_z = None
def _zstd(b, size):
    global _z
    if _z is None:
        _z = ctypes.CDLL(ctypes.util.find_library('zstd') or 'libzstd.so.1')
        _z.ZSTD_decompress.restype = ctypes.c_size_t
        _z.ZSTD_isError.restype = ctypes.c_uint
    out = ctypes.create_string_buffer(size)
    r = _z.ZSTD_decompress(out, ctypes.c_size_t(size), b, ctypes.c_size_t(len(b)))
    if _z.ZSTD_isError(r): raise ValueError('zstd error')
    return out.raw[:r]

def decomp(codec, b, size=0):
    if codec == 6: return _zstd(b, size)
    if codec == 0: return b
    if codec == 1: return snappy(b)
    if codec == 2: return zlib.decompress(b, 47)
    raise ValueError('codec %d unsupported' % codec)

def rle(b, p, end, bw, count):
    out = []; nb = (bw + 7) // 8
    while len(out) < count and p < end:
        h = 0; sh = 0
        while True:
            c = b[p]; p += 1; h |= (c & 0x7F) << sh; sh += 7
            if not c & 0x80: break
        if h & 1:
            g = h >> 1; nbytes = g * bw; chunk = int.from_bytes(b[p:p+nbytes], 'little'); p += nbytes
            mask = (1 << bw) - 1
            for i in range(g * 8): out.append((chunk >> (i * bw)) & mask if bw else 0)
        else:
            v = int.from_bytes(b[p:p+nb], 'little'); p += nb; out += [v] * (h >> 1)
    return out[:count]

def plain(t, b, n, p=0):
    if t == 0:  # boolean bit-packed
        return [bool((b[p + i // 8] >> (i % 8)) & 1) for i in range(n)]
    if t == 1: return list(struct.unpack_from('<%di' % n, b, p))
    if t == 2: return list(struct.unpack_from('<%dq' % n, b, p))
    if t == 4: return list(struct.unpack_from('<%df' % n, b, p))
    if t == 5: return list(struct.unpack_from('<%dd' % n, b, p))
    if t == 6:
        out = []
        for _ in range(n):
            ln = struct.unpack_from('<I', b, p)[0]; p += 4; out.append(b[p:p+ln].decode('utf-8', 'replace')); p += ln
        return out
    raise ValueError('type %d' % t)

def read(path, columns=None):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[-8:-4])[0]
    md = TC(b, len(b) - 8 - n).struct()
    schema = md[2]
    leaves = {}
    for el in schema[1:]:
        if el.get(5): continue
        leaves[el[4].decode()] = el
    res = {k: [] for k in leaves if columns is None or k in columns}
    for rg in md[4]:
        for cc in rg[1]:
            cm = cc[3]; name = b'.'.join(cm[3]).decode()
            if name not in res: continue
            el = leaves[name]; t = cm[1]; codec = cm[4]
            maxdef = 1 if el.get(3, 0) == 1 else 0
            p = cm.get(11) or cm[9]
            if cm.get(11) is not None and cm[11] > cm[9]: p = cm[9]
            remaining = cm[5]; dic = None; vals = res[name]
            while remaining > 0:
                tc = TC(b, p); ph = tc.struct(); p = tc.p
                csz = ph[3]; raw = b[p:p+csz]; p += csz
                if ph[1] == 2:
                    dic = plain(t, decomp(codec, raw, ph[2]), ph[7][1]); continue
                if ph[1] == 0:
                    h = ph[5]; nv = h[1]; enc = h[2]; data = decomp(codec, raw, ph[2]); q = 0
                    if maxdef:
                        ln = struct.unpack_from('<I', data, 0)[0]
                        defs = rle(data, 4, 4 + ln, 1, nv); q = 4 + ln
                    else: defs = [1] * nv
                elif ph[1] == 3:
                    h = ph[8]; nv = h[1]; enc = h[4]; dl = h[5]; rl = h[6]
                    lv = raw[:rl + dl]; body = raw[rl + dl:]
                    if h.get(7, True): body = decomp(codec, body, ph[2] - rl - dl)
                    defs = rle(lv, rl, rl + dl, 1, nv) if maxdef else [1] * nv
                    data = body; q = 0
                else:
                    continue
                nn = sum(1 for d in defs if d)
                if enc in (2, 8):
                    bw = data[q]; idx = rle(data, q + 1, len(data), bw, nn); vv = [dic[i] for i in idx]
                elif enc == 0:
                    vv = plain(t, data, nn, q)
                else:
                    raise ValueError('encoding %d' % enc)
                it = iter(vv)
                vals.extend(next(it) if d else None for d in defs)
                remaining -= nv
    return res
