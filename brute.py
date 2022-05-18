import asyncio
import glob
import multiprocessing
import os
import signal
import threading
import time
from asyncio import PriorityQueue

import pymysql
import requests
from loguru import logger

from SubBrute import SubBrute
from units import load_dns_servers, load_sub_names, user_abort, load_next_sub


class Brute(object):
    def __init__(self,domains,process=6,threads=256,file='dict/subnames.txt',next='dict/sub_next.txt'):
        self.domains=domains
        self.dns_servers=None
        self.process=process
        self.threads=threads
        self.sub_name=None
        self.normal_names_set=None
        self.normal_lines=None
        self.wildcard_lines=None
        self.next_subs=None
        self.ignore=True
        self.wildcard=False
        self.file=file
        self.next=next

    def brute(self,domain):
        table=domain.replace('.','_')

        tmp_dir = 'tmp/%s_%s' % (domain, int(time.time()))
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        multiprocessing.freeze_support()
        scan_count = multiprocessing.Value('i', 0)
        found_count = multiprocessing.Value('i', 0)
        queue_size_array = multiprocessing.Array('i', self.process)
        all_process = []
        start_time = time.time()
        # con = pymysql.connect(host=host, user=username, passwd=passwd, db=db)
        # cursor = con.cursor()
        # TODO 泛解析
    #     create='''CREATE TABLE IF NOT EXISTS `%s` (
	#   `id` int(11) NOT NULL AUTO_INCREMENT,
	#   `subdomain` varchar(255) NOT NULL,
	#   PRIMARY KEY (`id`)
	# )'''%domain.replace('.','_')
    #     cursor.execute(create)
    #     query='''select subdomain from %s'''%domain.replace('.','_')
    #     cursor.execute(query)
    #     exit_domains=[result[0] for result in cursor.fetchall()]
    #     #logger.info(exit_domains)
    #     cursor.close()
        exit_domains=[]
        LOCK = multiprocessing.Lock()
        try:

            for process_num in range(self.process):

                p = multiprocessing.Process(target=self.run_process,
                                            args=(domain, self.normal_lines,self.normal_names_set,self.wildcard_lines,self.threads, process_num, self.ignore,self.dns_servers, self.next_subs,
                                                  scan_count, found_count, queue_size_array,self.process, self.wildcard ,exit_domains,tmp_dir,LOCK)
                                            )
                all_process.append(p)
                p.start()
            char_set = ['\\', '|', '/', '-']
            count = 0
            notice_count=1
            while all_process:
                for p in all_process:
                    print("alive")
                    if not p.is_alive():
                        all_process.remove(p)
                groups_count = 0
                for c in queue_size_array:
                    groups_count += c
                msg = '%s: [%s] %s found, %s scanned in %.1f seconds, %s groups left' % (
                    domain,char_set[count % 4], found_count.value, scan_count.value, time.time() - start_time, groups_count)
                logger.info(msg)
                # if(time.time()-start_time>=notice_count*3600):
                #     notice_count+=1
                #     data = {"title": "continue scan", "desp": '%s found, %s scanned'%(found_count.value, scan_count.value)}
                #     requests.post(url=repurl, data=data)
                count += 1
                time.sleep(60)
        except KeyboardInterrupt as e:
            print('[ERROR] User aborted the scan!')
            for p in all_process:
                p.terminate()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print('[ERROR] %s' % str(e))


        # all_domains = set()
        # domain_count = 0
        # con = pymysql.connect(host=host, user=username, passwd=passwd, db=db)
        # cur = con.cursor()
        #
        # for _file in glob.glob(tmp_dir + '/*.txt'):
        #     with open(_file, 'r') as tmp_f:
        #         for domain in tmp_f:
        #             if domain not in all_domains:
        #                 domain_count += 1
        #                 all_domains.add(domain)       # cname query can result in duplicated domains
        #                 sql = "insert into {} values(null,'{}')".format(table, domain.strip('\n'))
        #                 #logger.info(sql)
        #                 cur.execute(sql)
        # cur.close()
        # con.commit()
        # con.close()
        #
        # msg = 'All Done. %s found, %s scanned in %.1f seconds.' % (
        #     domain_count, scan_count.value, time.time() - start_time)
        # logger.info(msg, line_feed=True)



    def run(self):
        self.dns_servers = load_dns_servers()
        self.normal_names_set,self.normal_lines,self.wildcard_lines=load_sub_names(file=self.file)

        self.next_subs=load_next_sub(file=self.next)
        for domain in self.domains:
            self.brute(domain=domain)

    def run_process(self,*params):
        signal.signal(signal.SIGINT, user_abort)
        s=SubBrute(*params)
        s.run()



