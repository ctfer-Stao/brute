import time
import multiprocessing

from brute import Brute
from web.models import SrcDomain
from web import DB
from  loguru import logger


def ReadDomain():
    '''读取主域名任务'''
    results = SrcDomain.query.filter(SrcDomain.flag == "oneforall").first()
    DB.session.commit()
    return results

def WriteDomain(results):
    '''修改主域名任务状态'''
    results.flag = "fastbrute"
    try:
        DB.session.commit()
    except Exception as e:
        DB.session.rollback()
        logger.info('修改主域名任务状态SQL错误:%s' % e)

def action(domain):
    '''子程序执行'''
    b = Brute(domains=[domain], process=2, threads=100, file='dict/random.txt', next='dict/sub_next.txt')
    b.run()

def main():
    '''主方法'''
    process_name = multiprocessing.current_process().name
    logger.info(f'子域名扫描进程启动:{process_name}')
    while True:
        results = ReadDomain()
        if not results:
            # logger.info("30")
            time.sleep(30)  # 没有任务延迟点时间
        else:
            action(results.domain)
            WriteDomain(results)

if __name__ == '__main__':
    main()