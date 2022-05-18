from brute import Brute
# import requests
# import pymysql
# if __name__ == '__main__':
#     b=Brute(domains=['vpal.com'],process=2,threads=100,file='dict/subnames_big.txt',next='dict/sub_next.txt')
#     b.run()

def run(domain):
    b=Brute(domains=[domain],process=2,threads=100,file='dict/subnames_big.txt',next='dict/sub_next.txt')
    b.run()





