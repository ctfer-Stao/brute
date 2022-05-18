import datetime

from web import DB



class SrcDomain(DB.Model):
    '''主域名表'''

    __tablename__ = 'src_domain'
    domain = DB.Column(DB.String(100), primary_key=True)
    domain_name = DB.Column(DB.String(100), nullable=True)
    domain_time = DB.Column(DB.String(30))
    flag = DB.Column(DB.String(30))

    def __init__(self, domain, domain_name, flag="null"):
        self.domain = domain
        self.domain_name = domain_name
        self.flag = flag
        self.domain_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class SrcSubDomain(DB.Model):
    '''子域名表'''

    __tablename__ = 'src_subdomain'
    subdomain = DB.Column(DB.String(150), primary_key=True)
    domain_name = DB.Column(DB.String(100))
    subdomain_ip = DB.Column(DB.String(20))
    cdn = DB.Column(DB.Boolean)
    flag = DB.Column(DB.Boolean)
    flag_url = DB.Column(DB.Boolean)
    flag_jg = DB.Column(DB.Boolean)
    subdomain_time = DB.Column(DB.String(30))


    def __init__(self, subdomain, domain, subdomain_ip, cdn, flag=False,flag_url=False,flag_jg=False):
        self.subdomain = subdomain
        self.domain_name = domain
        self.subdomain_ip = subdomain_ip
        self.cdn = cdn
        self.flag = flag
        self.flag_url = flag_url
        self.flag_jg=flag_jg
        self.subdomain_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

