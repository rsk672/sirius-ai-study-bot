from socket import *
import select
import errno
import random
import time
import random


google_query = \
b"""GET http://ifconfig.io/country_code HTTP/1.1
Host: ifconfig.io
User-Agent: curl/8.7.1
Accept: */*
Proxy-Connection: Keep-Alive\n\n"""


def download_list():
    import httpx
    res = httpx.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/refs/heads/master/http.txt")
    proxies = [(p.split(":")[0], int(p.split(":")[1])) for p in res.text.split("\n")]
    random.shuffle(proxies)
    return proxies


def diff(a, b): # assert a>=b
    a.sort(key=id)
    b.sort(key=id)
    ans = []
    i = 0
    for x in a:
        if i < len(b) and b[i] == x:
            i += 1
        else:
            ans.append(x)
    return ans


def get_working(ps, max_n):
    start_t = {}
    end_t = {}
    def build_socks_gen():
        i = 0
        for p in ps:
            i+=1
            s = socket(AF_INET, SOCK_STREAM)
            s.setblocking(False)
            st = s.connect_ex(p)
            if st == 0 or st == errno.EINPROGRESS:
                start_t[p] = time.time()
                yield s

    socks_gen = build_socks_gen()
    bsz = 200
    waiting_w = []

    waiting_r = []
    def add_socc():
        try:
            waiting_w.append(next(socks_gen))
            return True
        except StopIteration:
            return False
        except Exception as e:
            return True
    all_got = False
    for i in range(200):
        res = add_socc()
        
        if not res:
            all_got = True
            break
    ans = []
    while len(ans) <= max_n:
        rs, ws, es = select.select(waiting_r, waiting_w, [], 2) 

        to_rm_r = []
        to_rm_w = []
        for e in es:
            if e in waiting_r:
                to_rm_r.append(e)
            if e in waiting_w:
                to_rm_w.append(e)
            e.close()
        if all_got and not rs and not ws:
            break

        for w in ws:
            try:
                w.sendall(google_query)
                waiting_r.append(w)
            except Exception as e:
                w.close()
                pass
            to_rm_w.append(w)
        for r in rs:
            try:
                res = r.recv(4096)
                if res and b"\r\n\r\n" in res and b" " in res:
                    head, body = res.split(b"\r\n\r\n")
                    code = int(head.split(b" ")[1])
                    stripped = body.strip(b" \n\r")
                    if code == 200 and stripped and stripped != b"RU":
                        end_t[r.getpeername()] = time.time()
                        ans.append(r.getpeername())

            except Exception as e:
                pass
            to_rm_r.append(r)
            r.close()
        while (not all_got) and len(waiting_w) + len(waiting_r) <= bsz:
            res = add_socc()
            if not res:
                all_got = True
                break
        waiting_r = diff(waiting_r, to_rm_r)
        waiting_w = diff(waiting_w, to_rm_w)
    ans.sort(key = lambda v: end_t[v]-start_t[v])
    return ans[:max_n]
        

class ProxyGetter:
    def __init__(pg, n=20):
        pg.n = n
        pg.ps = []

    def precomp(pg):
        plist = download_list()
        pg.ps = get_working(plist, pg.n)

    def get(pg):
        if not len(pg.ps):
            pg.precomp()
        host, port = random.choice(pg.ps)
        return f"http://{host}:{port}"

