"""
Answer.Market
"""

import json
import numbers
from time import time
import os
import warnings
from pprint import pprint
from urllib2 import urlopen
from uuid import uuid4 as random_uuid

import bitcoinaddress
import jinja2
from datadog import statsd
import yaml
import coinfee

TIMEOUT = 5

# This has to make for a coinfee fee of 10,000 Satoshis or more.
FEE_MULTIPLIER = 0.1
FEE_ADDRESS = '1ansCQzgxUcy6retKnvMzTpyXnX8LWHQh'

JSON_PATH_ROOT = '/var/tmp/answer.market'
JSON_PATH = JSON_PATH_ROOT + '/{}.json'

# Bytes of sample preview that we show on /answers.
ANSWERS_SAMPLE_LENGTH = 50

# Minimum length in bytes for sample or answer.
MIN_LENGTH = 10

WALLETAPI_RECV = 'https://blockchain.info/q/getreceivedbyaddress/{}'

payment_cache = {}
legacy_payments = {}

DEBUG = True

warnings.simplefilter('always')


def pulse(metric):
    full_metric = 'answermarket.{}'.format(metric)
    statsd.increment(full_metric)
    debug('Sending stat: {}'.format(full_metric))


def debug(message):
    if DEBUG is True:
        pprint(message)
    return message


def render(template, page={}):
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader('./')
        ).get_template(template)
    return str(template.render(page=page))


def try_api(url, timeout=TIMEOUT):
    """
    Just here for legacy.
    """
    try:
        http_return = urlopen(url, timeout=timeout)
        if http_return.getcode() == 200:
            pulse('try_api.200')
            return int(http_return.read())
        else:
            pulse('try_api.not.200')
            return False
    except:
        pulse('try_api.exception')
        return False


def wallet_recv(address):
    """
    Just here for legacy.
    """
    return try_api(WALLETAPI_RECV.format(address))


def payment(answer_id, address, satoshis, epoch, fee):
    """
    Acts as a cache for payment status.
    """
    if answer_id in payment_cache:
        if payment_cache[answer_id] is True:
            pulse('payment.paid_and_in_cache')
            return True
    pulse('payment.making_coinfee_call')
    coinfee_payment = coinfee.payment(address=address,
                                      satoshis=satoshis,
                                      unique=str(epoch),
                                      fee_address=FEE_ADDRESS,
                                      fee=fee)
    payment_cache[answer_id] = coinfee_payment.status
    return coinfee_payment


def address_paid(address, satoshis):
    """
    Legacy!

    For coinfee /transaction and dual payments.
    """
    if address in legacy_payments:
        status = legacy_payments[address]
        pulse('address_paid.in_cache.{}'.format(status))
        return status
    pulse('address_paid.not_in_cache')
    funds = wallet_recv(address)
    if funds is not False:
        if funds >= satoshis:
            pulse('address_paid.already_paid')
            legacy_payments[address] = True
            return True
    pulse('address_paid.not_paid')
    legacy_payments[address] = False
    return False


def application(env, start_response):
    """
    This is where uwsgi calls us.
    """
    def reply(status, data, headers=[]):
        """
        Need to use this as return reply().
        """
        start_response(str(status), headers)
        return data

    path = env['REQUEST_URI']
    method = env['REQUEST_METHOD']

    pulse('hit')

    if 'HTTP_REFERER' in env:
        referer = env['HTTP_REFERER']
        debug('{} to {} from {} referer'.format(method,
                                                path,
                                                referer))
        pulse('hit.has_referer')
    else:
        pulse('hit.no_referer')

    if '..' in path:
        return reply(401, '')
    if path.startswith('/static/'):
        if method == 'GET':
            pulse('static.hit')
            try:
                # This doesn't work with reply() :-/
                with open('.' + path) as fp:
                    pulse('static.200')
                    return reply(200,
                                 fp.read(),
                                 [('Cache-Control', 'max-age=300')])
            except IOError:
                pulse('static.404')
                return reply(404, '')
    # Bought / unbought filters would probably be too expensive the
    # way we are doing things.
    # This is ugly and should be refactored. It's not obscenely
    # slow for our current size. For now...
    if path == '/answers':
        answers = []
        for json_file in os.listdir(JSON_PATH_ROOT):
            json_file_path = os.path.join(JSON_PATH_ROOT, json_file)
            with open(json_file_path) as answer_json_file:
                input_json = json.dumps(json.load(answer_json_file))
                answer_load = yaml.safe_load(input_json)
                if 'public' in answer_load:
                    if answer_load['public'] is False:
                        continue
                else:
                    continue
                strip_dot_json = len(json_file) - len('.json')
                answer_id = json_file[:strip_dot_json]
                # This is mainly for legacy, kinda.
                answer = {}
                answer['id'] = answer_id
                if len(answer_load['sample']) > ANSWERS_SAMPLE_LENGTH:
                    full_sample = answer_load['sample']
                    short_sample = full_sample[:ANSWERS_SAMPLE_LENGTH]
                    answer['sample'] = short_sample + '...'
                else:
                    answer['sample'] = answer_load['sample']
                answers.append(answer)
        pulse('answers.hit')
        return reply(200, render('answers.html', answers))
    # Legacy from 2016-10-20.
    # Used to give answers off /answers/. I wanted to have /answers
    # as an answer index, and /answer/answer makes more sense. So,
    # we have this generic redirect in place. May want to make it
    # smarter down the road, maybe not.
    if path.startswith('/answers/'):
        pulse('answers.redirect_to_answer')
        answer = path[len('/answers/'):]
        new_path = '/answer/{}'.format(answer)
        return reply(301, '', [('Location', new_path)])
    if path.startswith('/answer/'):
        if method == 'GET':
            pulse('answer.hit')
            answer_id = path[len('/answer/'):]
            json_file = JSON_PATH.format(answer_id)
            if os.path.isfile(json_file):
                with open(json_file) as answer_json_file:
                    input_json = json.dumps(json.load(answer_json_file))
                    page = yaml.safe_load(input_json)
                page['paid'] = False
                # For pre-coinfee /payment legacy answers.
                if 'epoch' not in page:
                    if 'coinfee' in page:
                        legacy_address = page['coinfee']['address']
                    else:
                        legacy_address = page['address']
                    if 'fee' not in page:
                        # Our minimum possible fee, circa 2016-11-26.
                        legacy_fee = 10000
                    else:
                        legacy_fee = page['fee']
                    if 'total_satoshis' not in page:
                        total_satoshis = page['satoshis'] + legacy_fee
                    else:
                        total_satoshis = page['total_satoshis']
                    page['paid'] = address_paid(legacy_address,
                                                total_satoshis)
                    if page['paid'] is not True:
                        page['address'] = legacy_address
                        page['fee'] = legacy_fee
                        page['epoch'] = legacy_address[:19]
                        answer_id = page['address']
                # Leaving legacy land.
                if page['paid'] is False:
                    payment_details = payment(answer_id=answer_id,
                                              address=page['address'],
                                              satoshis=page['satoshis'],
                                              epoch=page['epoch'],
                                              fee=page['fee'])
                    if payment_details is True:
                        page['paid'] = True
                    else:
                        page['paid'] = payment_details.status
                        page['address'] = payment_details.address
                        page['total_satoshis'] = payment_details.satoshis
                        bitcoins = page['total_satoshis'] * 0.00000001
                        page['bitcoins'] = "{0:.8f}".format(bitcoins)
                pulse('answer.200')
                return reply(200, render('answer.html', page))
            else:
                pulse('answer.404')
                return reply(404, 'Answer not found')
    if path == '/answer':
        if method == 'POST':
            pulse('answer.post.hit')
            # http://stackoverflow.com/questions/956867
            # Doing the json dump -> yaml_safeload is supposedly safer,
            # and it gives us the data as a string instead of unicode.
            # If we try to return unicode to uwsgi, it seems to bomb out
            # and return nothing other than the status header to the user.
            try:
                input_json = json.dumps(json.load(env['wsgi.input']))
                data = yaml.safe_load(input_json)
            except:
                pulse('answer.post.400.invalid_json')
                return reply(400, 'Where\'s your json?')
            if 'address' in data:
                address = data['address']
            else:
                pulse('answer.post.400.no_address_given')
                return reply(400, 'No address given.')
            # bitcoinaddress.validate is stupid. It allows Dogecoin
            # addresses. We make sure it begins with '1'
            if bitcoinaddress.validate(address) is False or \
                    address[0] != '1':
                pulse('answer.post.400.invalid_bitcoin_address')
                return reply(400, 'Invalid Bitcoin address.')
            if 'public' in data:
                if not isinstance(data['public'], bool):
                    pulse('answer.post.400.public_must_be_boolean')
                    return reply(400, 'public must be a boolean.')
            for key in ['sample', 'answer', 'satoshis']:
                if key in data:
                    if key == 'satoshis':
                        if not isinstance(data[key], numbers.Integral):
                            return reply(400, 'satoshis must be integer.')
                        # FIXME, hardcode this properly.
                        if data[key] < 100000:
                            message = 'Must be 100,000 Satoshis or more.'
                            return reply(400, message)
                    else:
                        if not isinstance(data[key], basestring):
                            message = 'Bad JSON key type for {}'.format(key)
                            return reply(400, message)
                        else:
                            if len(data[key]) <= MIN_LENGTH:
                                message = ('{} cannot be less than {} '
                                           'characters!').format(key,
                                                                 MIN_LENGTH)
                                return reply(400, message)
                else:
                    return reply(400, 'Missing JSON keys!')
            data['fee'] = int(data['satoshis'] * FEE_MULTIPLIER)
            data['epoch'] = int(time())
            answer_id = str(random_uuid())[:23]
            json_file = JSON_PATH.format(answer_id)
            if os.path.isfile(json_file):
                pulse('answer.post.URGENTURGENTURGENT')
                return reply(500, 'OOPS, something broke badly.')
            with open(json_file, 'w') as answer_json_file:
                json.dump(data, answer_json_file)
            msg = '/answer/{}'.format(answer_id)
            pulse('answer.post.201')
            return reply(201, msg)
    if path == '/submit':
        pulse('submit.redirect_to_slash')
        return reply(301, '', [('Location', '/')])
    if path == '/about':
        pulse('about.hit')
        return reply(200, render('about.html'))
    if path == '/':
        pulse('index.hit')
        return reply(200, render('index.html'))

    pulse('404')
    return reply(404, 'Try something else.')
