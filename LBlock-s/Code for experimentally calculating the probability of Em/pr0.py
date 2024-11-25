import random
import multiprocessing as mulp

Sbox = [14, 9, 15, 0, 13, 4, 10, 11, 1, 2, 8, 3, 7, 6, 12, 5]

p1 = [2, 0, 3, 1, 6, 4, 7, 5]
ip1 = [1, 3, 0, 2, 5, 7, 4, 6]
p2 = [6, 7, 0, 1, 2, 3, 4, 5]
ip2 = [2, 3, 4, 5, 6, 7, 0, 1]

def keyex(prkey, r, st):
    k = []
    k.append(prkey[0: 8])
    for i in range(r - 1):
        temp = prkey.copy()
        for j in range (20):
            x = (j + 7) % 20
            y = (x + 1) % 20
            prkey[j] = ((temp[x] << 1) & 0xe) ^ (temp[y] >> 3)
        prkey[0] = Sbox[prkey[0]]
        prkey[1] = Sbox[prkey[1]]
        a = (i + st) >> 1
        b = ((i + st) & 1) << 3
        prkey[2] ^= a
        prkey[3] ^= b
        k.append(prkey[0: 8])
    return k

def rf(state, rk):
    res = [0 for _ in range (16)]
    for i in range (8):
        x0 = ip1[i]
        x1 = ip2[i] + 8
        res[i] = Sbox[state[x0] ^ rk[x0]] ^ state[x1]
        res[i + 8] = state[i]
    return res

def irf(state, rk):
    res = [0 for _ in range (16)]
    for i in range (8):
        x0 = p2[i]
        x1 = ip1[x0]
        res[i + 8] = Sbox[state[x1 + 8] ^ rk[x1]] ^ state[x0]
        res[i] = state[i + 8]
    return res

def pr(udif, ldif, key, rm, nop, co):
    #Set the active position of the input in the upper trail of Em part
    inn = [1]
    #Set the active position of the output in the lower trail of Em part
    ott = [14]
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
    nop = 8

    Con = 0
    Pr = 0
    dif = [0, 0]
    prkey = []
    for i in range (20):
        prkey.append(random.randint(0, 15))
    key = keyex(prkey, rm, r0)
    udif = [1, 2 ,3 , 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    ldif = [1, 2 ,3 , 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    N = 1 << nop
    for ud in range (15):
        for ld in range (15):
            cp = []
            cs = []
            processes = []
            con0 = 0
            con = 0
            for i in range (N):
                cop, cos = mulp.Pipe()
                cp.append(cop)
                cs.append(cos)
                processes.append(mulp.Process(target = pr, args = (udif[ud], ldif[ld], key, rm, nop, cs[i], )))
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
                dif = [ud, ld]
    Pr = Con/ con0
    print("The number of data: "con0)
    print("The number of data which fit the distinguisher:"con)
    print("Probbility:"Pr)



































