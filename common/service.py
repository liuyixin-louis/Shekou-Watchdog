from datetime import datetime
from time import sleep, time
from common.utils import utils
from common.logger import logger
from common.config import config
from common.account import account
from common.report import report
from common.push import push


class Service:
    @logger.catch
    def __init__(self):
        self._str_now_time = "0.1"
        self._time_interval = ""
        self._account_cnt = account.row
        self._email_switch = None
        self._timer_switch = None
        self._all_departure_date = None
        self._all_date_userid = {}
        self.fetch_param()

    @logger.catch
    def fetch_param(self):
        self._email_switch = config.config('/setting/push/email/switch', utils.get_call_loc())
        self._timer_switch = config.config('/setting/timer/switch', utils.get_call_loc())
        self._time_interval = config.config('/setting/timer/time_interval', utils.get_call_loc())
        logger.debug("Fetched [ReportService] params.")

    @logger.catch
    def _get_now_time(self):
        now = datetime.now()
        self._str_now_time = now.strftime("%H.%M")
        return self._str_now_time

    @logger.catch
    def _sort_departure_date(self):
        self._all_departure_date = []
        for i in range(self._account_cnt):
            self._all_departure_date.append(account.sail_date(i))
        self._all_departure_date = list(set(self._all_departure_date))
        logger.debug(f"All departure date:{self._all_departure_date}")

    @logger.catch
    def _task(self):
        """
        先分类日期，后分别查询并群发通知
        """
        self._sort_departure_date()
        for i in self._all_departure_date:
            self._all_date_userid[i] = ""
        for i in range(self._account_cnt):
            self._all_date_userid[account.sail_date(i)] += f"|{account.userid(i)}"
        logger.debug(f"All date userid:{self._all_date_userid}")
        dates_cnt = len(self._all_departure_date)
        for i in self._all_departure_date:
            index = self._all_departure_date.index(i)
            log_info = f"[{index + 1}/{dates_cnt}] Checking and pushing date:{i}".center(46, '-')
            logger.info(log_info)
            ret = report.main(i)
            if "10:00" in ret[1]:
                push.push(ret, "Hi", account.wechat_push(index), account.email_push(index), account.sendkey(index),
                      self._all_date_userid[i][1:], account.email(index))
                sleep(1)

    @logger.catch
    def _gen(self):
        start_time = time()
        if self._account_cnt == 0:
            logger.error("Account does not exist.")
        else:
            if self._email_switch == "on":
                push.bot_email.login()
            self._task()
        end_time = time()
        cost = f"{(end_time - start_time):.2f}"
        logger.info(f"Reports are completed. Cost time:{cost}(s)".center(50, '-'))

    @logger.catch
    def start(self):
        if self._timer_switch == "on":
            logger.info("Timer is enabled.")
            logger.info(f"Time interval:{self._time_interval}min(s).")
            while True:
                logger.info("Time arrived. Start to report.")
                config.refresh()
                account.refresh()
                utils.refresh_param()
                self._gen()
                logger.info(f"{self._time_interval} min(s) to wait for the next run.")
                sleep(int(self._time_interval) * 60)

        else:
            logger.info("Timer is disabled.")
            logger.info("Start to report.")
            self._gen()


service = Service()
