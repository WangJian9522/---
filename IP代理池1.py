import requests
from lxml import etree
import MySQLdb
import telnetlib
import json

# 数据库存储代理
class ProxiesPool(object):
    def __init__(self, max_sill=10, limit_sill=3):
        self.max_sill = max_sill
        self.limit_sill = limit_sill
        self.initialization_of_db()

    # 获取目标网站
    def get_target_web(self, url='https://cn-proxy.com/'):
        while self.throw_count() < self.max_sill:
            data = etree.HTML(requests.get(url).text)
            temp = data.xpath('//tbody//tr')
            for i in temp:
                if self.throw_count() >= self.max_sill:
                    break
                self.ip_code, self.ip_port = i.xpath(".//td[1]/text() | .//td[2]/text()")
                ip = {"http": self.ip_code + ":" + self.ip_port}
                # 验证是否可用
                if self.check_ip(self.ip_code, self.ip_port):
                    # 可用 入库
                    self.save_ip(ip)
        self.keep_check_ip()

    # 抛出一个可用的ip
    def throw_a_ip(self):

        self.cursor.execute(self.selectSQL)

        ip = json.loads(self.cursor.fetchone()[0].replace("'", '"'))

        # 标记已用IP
        self.cursor.execute(self.updateSQL, [ip])
        self.conn.commit()
        self.auto_full_ip()
        # 返回一个代理ip
        return ip

    # 定义代理池
    def auto_full_ip(self):
        if self.throw_count() <= self.limit_sill:
            # 扫描是否有不可用的ip
            self.keep_check_ip()
            # 有不可用的ip，则从网站添加
            self.get_target_web()

    # 保存可用的ip
    def initialization_of_db(self):
        self.conn = MySQLdb.Connection(
            host='localhost',
            port=3306, user='root',
            password='138522',
            db='webspider',
            charset='utf8')
        self.cursor = self.conn.cursor()
        self.insertSQL = 'insert into proxies(proxy,status) values(%s,%s)'
        self.countSQL = 'select status from proxies where status=1'
        self.selectSQL = 'select proxy from proxies where status=1 limit 0,1'
        self.updateSQL = 'update proxies set status=0 where proxy=%s'

    def save_ip(self, ip):
        self.cursor.execute(self.insertSQL, [str(ip), 1])
        self.conn.commit()

    # 检查可用性
    def check_ip(self, ip_code, ip_port):
        try:
            telnetlib.Telnet('%s' % ip_code, port='%s' % ip_port, timeout=20)

        except:
            # print(ip_code, ip_code, '不可用')
            return False
        else:
            # print(ip_code, ip_code, '可用')
            return True

    # 返回池内可用ip数量
    def throw_count(self):
        # print(self.cursor.execute(self.countSQL))
        return self.cursor.execute(self.countSQL)

    # 定期扫描
    def keep_check_ip(self):
        for i in self.throw_all_ip():
            i = i.replace("'", '"')
            i = json.loads(i)
            ip_code = (i['http'].split(':'))[0]
            # print(ip_code)
            ip_port = (i['http'].split(':'))[1]
            if self.check_ip(ip_code, ip_port):
                # 可用
                self.cursor.execute('update proxies set status=1 where proxy="%s"' % str(i))
                self.conn.commit()

    # 获取池内所有ip
    def throw_all_ip(self):
        self.cursor.execute('select proxy from proxies')
        for ip_item in [i[0] for i in self.cursor.fetchall()]:
            yield ip_item

#
# if __name__ == '__main__':
#     temp = ProxiesPool()
#     temp.throw_a_ip() # 从库获取一个可用
