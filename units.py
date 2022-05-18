import asyncio
import multiprocessing
import re
import socket
import sys
import threading
import aiodns
from loguru import logger

from iscdn import iscdn
from web import DB
from web.models import SrcSubDomain, SrcDomain
def is_intranet(ip):
    ret = ip.split('.')
    if len(ret) != 4:
        return True
    if ret[0] == '10':
        return True
    if ret[0] == '172' and 16 <= int(ret[1]) <= 31:
        return True
    if ret[0] == '192' and ret[1] == '168':
        return True
    return False

def user_abort(sig, frame):
    exit(-1)

def load_sub_names(file):
    normal_lines = []
    wildcard_lines = []
    wildcard_set = set()
    regex_list = []
    lines = set()
    normal_names_set=set()
    with open(file) as inFile:
        for line in inFile.readlines():
            sub = line.strip()
            if not sub or sub in lines:
                continue
            lines.add(sub)

            brace_count = sub.count('{')
            if brace_count > 0:
                wildcard_lines.append((brace_count, sub))
                sub = sub.replace('{alphnum}', '[a-z0-9]')
                sub = sub.replace('{alpha}', '[a-z]')
                sub = sub.replace('{num}', '[0-9]')
                if sub not in wildcard_set:
                    wildcard_set.add(sub)
                    regex_list.append('^' + sub + '$')
            else:
                normal_lines.append(sub)
                normal_names_set.add(sub)

    if regex_list:
        pattern = '|'.join(regex_list)
        _regex = re.compile(pattern)
        for line in normal_lines:
            if _regex.search(line):
                normal_lines.remove(line)
    return normal_names_set,normal_lines,wildcard_lines

async def test_server_python3(server, dns_servers):
    resolver = aiodns.DNSResolver()
    try:
        resolver.nameservers = [server]
        answers = await resolver.query('public-dns-a.baidu.com', 'A')    # an existed domain
        if answers[0].host != '180.76.76.76':
            raise Exception('Incorrect DNS response')
        try:
            await resolver.query('test.bad.dns.lijiejie.com', 'A')    # non-existed domain
            with open('bad_dns_servers.txt', 'a') as f:
                f.write(server + '\n')
            logger.info('[+] Bad DNS Server found %s' % server)
        except Exception as e:
            dns_servers.append(server)
        logger.info('[+] Server %s < OK >   Found %s' % (server.ljust(16), len(dns_servers)))
    except Exception as e:
        logger.info('[+] Server %s <Fail>   Found %s' % (server.ljust(16), len(dns_servers)))
async def async_load_dns_servers(servers_to_test, dns_servers):
    tasks = []
    for server in servers_to_test:
        task = test_server_python3(server, dns_servers)
        tasks.append(task)
    await asyncio.gather(*tasks)
def load_dns_servers():
    logger.info('Validate DNS servers')
    dns_servers = []

    servers_to_test = []
    for server in open('dict/dns_servers.txt').readlines():
        server = server.strip()
        if server and not server.startswith('#'):
            servers_to_test.append(server)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_load_dns_servers(servers_to_test, dns_servers))
    # loop.close()

    server_count = len(dns_servers)
    logger.info('\n[+] %s DNS Servers found' % server_count, line_feed=True)
    if server_count == 0:
        logger.info('[ERROR] No valid DNS Server !', line_feed=True)
        sys.exit(-1)
    return dns_servers

def load_next_sub(file):
    next_subs = []
    _file = file
    with open(_file) as f:
        for line in f:
            sub = line.strip()
            if sub and sub not in next_subs:
                tmp_set = {sub}
                while tmp_set:
                    item = tmp_set.pop()
                    if item.find('{alphnum}') >= 0:
                        for _letter in 'abcdefghijklmnopqrstuvwxyz0123456789':
                            tmp_set.add(item.replace('{alphnum}', _letter, 1))
                    elif item.find('{alpha}') >= 0:
                        for _letter in 'abcdefghijklmnopqrstuvwxyz':
                            tmp_set.add(item.replace('{alpha}', _letter, 1))
                    elif item.find('{num}') >= 0:
                        for _letter in '0123456789':
                            tmp_set.add(item.replace('{num}', _letter, 1))
                    elif item not in next_subs:
                        next_subs.append(item)
    return next_subs

def WriteDb(subdomain, domain, subdomain_ip, cdn,LOCK):
    process_name = multiprocessing.current_process().name
    LOCK.acquire()
    # logger.info("{}拿到锁".format(process_name))
    '''写入数据库'''
    result = SrcSubDomain.query.filter(SrcSubDomain.subdomain == subdomain).count()
    if result:
        logger.info( f'{process_name}数据库已有该子域名[{subdomain}]')
        LOCK.release()
        # logger.info("{}私贩到锁".format(process_name))
        return None
    query=SrcDomain.query.filter(SrcDomain.domain == domain).first()
    if not query:
        logger.info( f'{process_name}数据库无已主域名[{domain}]')
        LOCK.release()
        # logger.info("{}私贩到锁".format(process_name))
        return None
    sql = SrcSubDomain(subdomain=subdomain, domain=query.domain_name, subdomain_ip=subdomain_ip, cdn=cdn)
    DB.session.add(sql)
    try:
        DB.session.commit()
    except Exception as e:
        DB.session.rollback()
        logger.info(f'{process_name}子域名[{subdomain}]入库失败:{e}')
    LOCK.release()
    # logger.info("{}私贩到锁".format(process_name))
    logger.info("找到新域名: " + subdomain)

def Warehouse(subdomains, domain,LOCK):
    logger.info(f'开始进行子域名入库')

    ip =socket.gethostbyname(subdomains)
    cdn = iscdn(ip)
    WriteDb(subdomains, domain, ip,cdn,LOCK)
    logger.info(f'子域名入库完成')