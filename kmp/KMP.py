#coding: utf8

def compute_prefix(pattern):
    tell = [-1] * len(pattern)
    k = -1
    for i, v in enumerate(pattern[1:]):
        while k>=0 and pattern[k + 1] != v:
            k = tell[k]
        if pattern[k + 1] == v:
            k += 1
        tell[i + 1] = k
    return tell

def kmp_match(text, pattern):
    tell = compute_prefix(pattern)
    m = len(pattern)
    p = -1
    for i, v in enumerate(text):
        while p >= 0 and pattern[p + 1] != v:
            p = tell[p]
        if pattern[p + 1] == v:
            p += 1
        if p == m - 1:
            print "Match in %sth position in given text!" % (i - m + 1)
            p = tell[p]

if __name__ == "__main__":
    print compute_prefix("bai")
    kmp_match("I love baiyang!", "bai")

