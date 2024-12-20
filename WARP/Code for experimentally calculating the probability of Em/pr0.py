import random
import time
import multiprocessing as mulp

Sbox = [0xc, 0xa, 0xd, 0x3, 0xe, 0xb, 0xf, 0x7, 0x8, 0x9, 0x1, 0x5, 0x0, 0x2, 0x4, 0x6]
pi = [31, 6, 29, 14, 1, 12, 21, 8, 27, 2, 3, 0, 25, 4, 23, 10, 15, 22, 13, 30, 17, 28, 5, 24, 11, 18, 19, 16, 9, 20, 7, 26]
rc0 = [0x0, 0x0, 0x1, 0x3, 0x7, 0xf, 0xf, 0xf, 0xe, 0xd]
rc1 = [0x4, 0xc, 0xc, 0xc, 0xc, 0xc, 0x8, 0x4, 0x8, 0x4]

def rf(state, key, rn):
    res = [0 for _ in range (32)]
    k = key[rn & 1]
    for i in range (16):
        p = i << 1
        res[pi[p]] = state[p]
        res[pi[p + 1]] = Sbox[state[p]] ^ state[p + 1] ^ k[i]
    res[6] ^= rc0[rn]
    res[14] ^= rc1[rn]
    return res

def irf(state, key, rn):
    res = [0 for _ in range (32)]
    k = key[rn & 1]
    state[6] ^= rc0[rn]
    state[14] ^= rc1[rn]
    for i in range(16):
        p = i << 1
        res[p] = state[pi[p]]
        res[p + 1] = Sbox[res[p]] ^ state[pi[p + 1]] ^ k[i]
    return res

def pr(nop, co):
    #Set rm
    rm = 10
    #Set the active position of the input in the upper trail of Em part
    inn = [16, 19]
    #Set the active position of the output in the lower trail of Em part
    ott = [23]
    #Set the number of data involved to test the property
    nd = 25
    
    Lu = len(inn)
    Ll = len(ott)
    udif = 0xa
    ldif = 0xa
    ud = [0 for _ in range (32)]
    for i in range (Lu):
        ud[inn[i]] = udif
    st = []
    con = 0
    con0 = 0
    st = [0 for _ in range (32)]
    key = [[],[]]
    for i in range (16):
        key[0].append(random.randint(0, 15))
        key[1].append(random.randint(0, 15))
    for _ in range (1 << (nd - nop - 4)):
        for i in range (32):
            st[i] = random.randint(0, 15)
        st[inn[0]] = 0
        for i in range (1, 16):
            con0 += 1
            statea = st.copy()
            statea[inn[0]] = i
            stateb = statea.copy()
            for j in range (Lu):
                stateb[inn[j]] = stateb[inn[j]] ^ udif
            for j in range (rm):
                statea = rf(statea, key, j)
                stateb = rf(stateb, key, j)
            statec = statea.copy()
            stated = stateb.copy()
            for j in range (Ll):
                statec[ott[j]] = statec[ott[j]] ^ ldif
                stated[ott[j]] = stated[ott[j]] ^ ldif
            for j in range (rm):
                statec = irf(statec, key, rm - 1 - j)
                stated = irf(stated, key, rm - 1 - j)
            k = 0
            for j in range (32):
                dif = statec[j] ^ stated[j]
                if dif != ud[j]:
                    k = 1
                    break
            if k == 0:
                con += 1
    co.send([con, con0])

if __name__=='__main__':
    #Set the number of processes
    nop = 3

    N = 1 << 3
    cp = []
    cs = []
    processes = []
    con0s = []
    cons = []
    con0 = 0
    con = 0
    for i in range (N):
        cop, cos = mulp.Pipe()
        cp.append(cop)
        cs.append(cos)
        processes.append(mulp.Process(target = pr, args = (nop, cs[i], )))
    for i in range (N):
        processes[i].start()
    for i in range (N):
        s = cp[i].recv()
        con += s[0]
        con0 += s[1]
    for i in range (N):
        processes[i].join()
    print("The number of data: "con0)
    print("The number of data which fit the distinguisher:"con)
    print("Probbility:"con / con0)












