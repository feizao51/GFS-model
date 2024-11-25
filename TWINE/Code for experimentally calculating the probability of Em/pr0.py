import random
import time
import multiprocessing as mulp

Sbox = [0xC, 0x0, 0xF, 0xA, 0x2, 0xB, 0x9, 0x5, 0x8, 0x3, 0xD, 0x7, 0x1, 0xE, 0x6, 0x4]
pi = [5, 0, 1, 4, 7, 12, 3, 8, 13, 6, 9, 2, 15, 10, 11, 14]
c = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x03, 0x06, 0x0C,
     0x18, 0x30, 0x23, 0x05, 0x0A, 0x14, 0x28, 0x13, 0x26,
     0x0F, 0x1E, 0x3C, 0x3B, 0x35, 0x29, 0x11, 0x22, 0x07,
     0x0E, 0x1C, 0x38, 0x33, 0x25, 0x09, 0x12, 0x24]

def key_ex(prk, r, st):
    rkey = []
    k = prk.copy()
    for i in range (r - 1):
        rkey.append(k[:16])
        k[1] = Sbox[k[1]]
        k[4] = Sbox[k[4]]
        ch = c[st + i] >> 3
        cl = c[st + i] & 0x7
        k[7] ^= ch
        k[19] ^= cl
        temp = k.copy()
        k = temp[3:4].copy() + temp[0:3].copy() + temp[4:].copy()
        temp = k.copy()
        k = temp[16:].copy() + temp[:16].copy()
    rkey.append(k[:16])
    return rkey

def rf(state, rkey):
    res = [0 for _ in range (16)]
    for i in range (8):
        p = i << 1
        res[pi[p]] = state[p]
        res[pi[p + 1]] = Sbox[state[p]] ^ state[p + 1] ^ rkey[i]
    return res

def irf(state, rkey):
    res = [0 for _ in range (16)]
    for i in range(8):
        p = i << 1
        res[p] = state[pi[p]]
        res[p + 1] = Sbox[res[p]] ^ state[pi[p + 1]] ^ rkey[i]
    return res

def pr(udif, ldif, key, rm, nop, co):
    #Set the active position of the input in the upper trail of Em part
    inn = [8]
    #Set the active position of the output in the lower trail of Em part
    ott = [5]
    #Set the number of data involved to test the property
    nd = 20
    
    Lu = len(inn)
    Ll = len(ott)
    ud = [0 for _ in range (16)]
    for i in range (Lu):
        ud[inn[i]] = udif
    st = []
    con = 0
    con0 = 0
    st = [0 for _ in range (16)]
    for _ in range (1 << (nd - nop - 4)):
        for i in range (16):
            st[i] = random.randint(0, 15)
        st[inn[0]] = 0
        for i in range (16):
            con0 += 1
            statea = st.copy()
            statea[inn[0]] = i
            stateb = statea.copy()
            for j in range (Lu):
                stateb[inn[j]] = stateb[inn[j]] ^ udif
            for j in range (rm):
                statea = rf(statea, key[j])
                stateb = rf(stateb, key[j])
            statec = statea.copy()
            stated = stateb.copy()
            for j in range (Ll):
                statec[ott[j]] ^= ldif
                stated[ott[j]] ^= ldif
            for j in range (rm):
                statec = irf(statec, key[rm - 1 - j])
                stated = irf(stated, key[rm - 1 - j])
            k = 0
            for j in range (16):
                dif = statec[j] ^ stated[j]
                if dif != ud[j]:
                    k = 1
                    break
            if k == 0:
                con += 1
    co.send([con, con0])

if __name__ == '__main__':
    #Set rm
    rm = 7
    #Set r0
    r0 = 4
    #Set the number of processes
    nop = 3

    Con = 0
    Pr = 0
    dif = [0, 0]
    prkey = []
    for i in range (20):
        prkey.append(random.randint(0, 15))
    key = key_ex(prkey, rm, r0)
    udif = [1, 2 ,3 , 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    ldif = [1, 2 ,3 , 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    N = 1 << nop
    for ud in range (0, 15):
        for ld in range (0, 15):
            cp = []
            cs = []
            processes = []
            con0 = 0
            con = 0
            for i in range (N):
                cop, cos = mulp.Pipe()
                cp.append(cop)
                cs.append(cos)
                processes.append(mulp.Process(target = pr, args = (udif[ud], ldif[ld], key, rm, nop, cs[i] )))
            for i in range (N):
                processes[i].start()
            for i in range (N):
                s = cp[i].recv()
                con += s[0]
                con0 += s[1]
            for i in range (N):
                processes[i].join()
            if con > Con:
                Con = con
                dif = [udif[ud], ldif[ld]]
    Pr = Con/ con0
    print("The number of data: "con0)
    print("The number of data which fit the distinguisher:"con)
    print("Probbility:"Pr)











