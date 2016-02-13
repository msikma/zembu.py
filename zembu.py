#!/usr/bin/env python
# coding=utf8
#
# zembu.py 0.1
# Script that checks whether dictionary words are available as domain names.

import subprocess
import datetime
import argparse
import pprint
import time
import sys
import os

# Get current console size.
ROWS, COLS = [int(n) for n in os.popen('stty size', 'r').read().split()]
VERSION = '0.2'


def rate_limited(max_per_second):
    '''
    Decorator function to rate limit a function to run n times per second.
    Usage is as follows:

        @rate_limited(2)  # 2 per second at most
        def my_function(n):
            print('hello %d' % n)

        # Takes 50 seconds to complete
        for n in range(100):
            my_function(n)

    Modified version of the following Stack Overflow answer:
    <http://stackoverflow.com/a/667706/3553425>
    '''
    min_interval = 1.0 / float(max_per_second)

    def decorate(func):
        last_time_called = [0.0]

        def rate_limited_function(*args, **kargs):
            elapsed = time.clock() - last_time_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            ret = func(*args, **kargs)
            last_time_called[0] = time.clock()

            return ret

        return rate_limited_function

    return decorate


def get_exec_unsafe(cmd, ignore_errors=False):
    '''
    Returns the output of a subprocess command.

    NOTE: DO NOT PASS UNSANITIZED INPUT TO THIS FUNCTION.
    '''
    try:
        return subprocess.check_output(cmd, shell=True).strip()
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            return e.output.strip()
        else:
            return False


def print_progress(curr, amount, domain, is_available):
    '''
    Shows the current progress indicator as a percentage.
    '''
    sys.stdout.write('\r{}'.format(' ' * ROWS))
    sys.stdout.write('\r[{:7.3f}%] {}'.format(
        (float(curr) / amount) * 100,
        domain
    ))
    sys.stdout.flush()


def get_dict_words(dict_file):
    '''
    Extracts the individual words from a dictionary file, with whitespace
    stripped, and returns them as a list.
    '''
    word_info = []
    
    with open(dict_file) as file:
        words = [word.strip().lower() for word in file.readlines()]
        
    # If we've got semicolons, we're saving extra information
    # about the words.
    if ';' in words[0]:
        new_words = []
        for word in words:
            slices = word.split(';')
            new_words.append(slices[0])
            word_info.append(slices[1:])
        words = new_words
    else:
        words = filter(None, words)  # remove empty strings
        words = list(set(words))  # remove duplicates
        words.sort()
    
    return [words, word_info]


@rate_limited(1)
def check_domain(domain, verbose=False):
    if verbose:
        print('whois "%s"' % (domain))

    output = get_exec_unsafe('whois "%s"' % (domain))

    if 'no match for' in output.lower():
        return True
    else:
        return False


def check_domains(words, word_info, tlds=['com'], log='zembu_output.log', verbose=False):
    '''
    Iterates through a provided list of words and checks their availability
    as domain names with the given tld.
    '''
    amount = len(words) * len(tlds)
    print('Checking %d domain names. This might take a while.' % amount)
    print('Upon completion, the results will be saved to %s.' % log)
    print('The escape sequence is ^C.')

    available = []
    n = 0
    for n in range(len(words)):
        word = words[n]
        info = word_info[n]
        for tld in tlds:
            domain = (word + '.' + tld).lower()
            is_available = check_domain(domain, verbose)
            if is_available:
                available.append(domain + ' (' + (', '.join(info)) + ')')

            n += 1
            if not verbose:
                print_progress(n, amount, domain, is_available)

    return (amount, available)


def is_writable(log):
    '''
    Returns whether the log file can be opened for writing.
    '''
    try:
        filehandle = open(log, 'w')
        filehandle.close()
        return True
    except IOError:
        return False


def log_output(version, amount, available, words, duration, args, log):
    '''
    Writes the results of the script to the log file.
    '''
    available_list = '\n'.join(available)
    now = str(datetime.datetime.utcnow()) + ' UTC'
    settings = {
        'version': version,
        'duration': duration,
        'checked': amount,
        'words': len(words),
        'available': len(available),
        'options': args
    }
    print('\nThe following domains are available:\n%s' % available_list)
    print('Saving output to %s...' % log)
    with open(log, 'w') as file:
        file.write('zembu.py: %s:\n' % now)
        file.write(pprint.pformat(settings))
        file.write('\n----\n')
        file.write(available_list)
        file.write('\n')
    print('Saved.')


def main():
    '''
    Checks the user's command line input and runs the main program.
    '''
    argparser = argparse.ArgumentParser(add_help=False)
    argparser.description = 'zembu.py: checks all entries in a list of words \
for domain availability'
    argparser.add_argument(
        '-h', '--help',
        action='help',
        help='Show this help message and exit.'
    )
    argparser.add_argument(
        '-V', '--version',
        action='version', version='zembu.py: ' + VERSION,
        help='Show version number and exit.'
    )
    argparser.add_argument(
        '--dict',
        action='store',
        default='/usr/share/dict/words',
        required=True,
        help='Path to the dictionary file to use. Must contain one word per '
             'line.'
    )
    argparser.add_argument(
        '--tlds',
        action='store',
        default='com',
        help='Top-level domain to check, e.g. "com,net" to check "<word>.com" '
             'and "<word>.net". (Default: "com")'
    )
    argparser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Outputs all Whois commands we run. (Default: False)'
    )
    argparser.add_argument(
        '--log-file',
        action='store',
        default='zembu_output.log',
        help='Saves a list of all available domain names to a text file. '
             '(Default: "zembu_output.log")'
    )
    args = argparser.parse_args()
    argdict = args.__dict__
    words, word_info = get_dict_words(args.dict)
    tlds = args.tlds.split(',')
    log = args.log_file

    # Ensure the log file is writable before we check 200,000 domains.
    if not is_writable(log):
        print('The log file %s is not available for writing.' % log)
        exit(1)

    start = time.time()

    # Go through the entire words list and check the domains, or until
    # interrupted by the escape sequence.
    try:
        amount, available = check_domains(words, word_info, tlds, log, args.verbose)
        end = time.time()
        duration = int(end - start)
        log_output(VERSION, amount, available, words, duration, argdict, log)
        exit(0)
    except KeyboardInterrupt:
        print('\nCanceled.\n')
        exit(2)


if __name__ == '__main__':
    main()
