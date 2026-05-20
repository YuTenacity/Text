from math import *
def isPrime(n):
    if n<2:
        return False
    k=floor(sqrt(n))
    for  i in range(2,k+1):
        if n%i==0:
            return False
    return True

n=int(input("请输入一个整数："))
if isPrime(n):
    print("isPrime")
else:
    print("no isPrime")