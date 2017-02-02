# The defunct answer.market

October 5th 2015 to Febuary 1st 2016.

Unfortunately, I had no customers. There was no interesting data on the site. The site was seldomly accessed.

SporeStack is starting to take off a bit and needs more of my time. The domain is also far too pricey -- over $100 a year.

To save money and free up time and focus, I am shutting down answer.market and open sourcing it.

Parts written by me are releasd into the public domain. It's kinda ugly in a lot of ways, but hopefully you can find a use for it.

Pretty easy to make this run on multiple boxes. JSON files don't get modified, only created.


Backing up:

* `cd /; ssh -i ~/.ssh/answer.market answer.market tar czf - /var/tmp/answer.market | tar xzvf -`

Testing:

* `uwsgi --master --wsgi-file wsgi.py --http-socket :8080 -p 10 --limit-post 150240`

Deploying:

```
tar --exclude README.md --exclude wsgi.pyc --exclude .git -cvf - answer.market | ssh -i ~/.ssh/answer.market 104.238.144.75  'tar -xf -'


freebsd-update fetch
freebsd-update install
pkg upgrade -y
pkg install -y uwsgi python py27-pip ca_root_nss
pip install -r ~/answer.market/requirements.txt
mkdir /var/tmp/answer.market
chmod 700 /var/tmp/answer.market

DD_API_KEY=-nope- sh -c "$(curl -L https://raw.githubusercontent.com/DataDog/dd-agent/master/packaging/datadog-agent/source/setup_agent.sh)"

echo 'cd /root/answer.market; /usr/local/bin/uwsgi -L -p 10 --limit-post 150240 --master --wsgi-file wsgi.py --http-socket [::]:80 --http-socket :80 >> /var/log/uwsgi 2>&1 &
cd /root/.datadog-agent; bin/agent >> /var/log/datadoge 2>&1 &' > /etc/rc.local
```

Oddities:

Each Python process has separate dicts / caches. Memcache could be better.

Next steps:
