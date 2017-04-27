#!/usr/bin/env python
"""
ES Curator.

Usage:
  es_curator -h | --help
  es_curator [--dry] [--period <days>] [--prefix <prefix>] <url>

Options:
  <url>                     The base url to use.
  --prefix <prefix>         Index prefix
  -p --period <days>        Retention period in days [default: 7]
  -h --help                 Show this help.
  --dry                     Dry run, do not change anything.

Examples:

  es_curator http://localhost:9200

"""
import datetime
import requests
import arrow

TODAY = arrow.utcnow().floor('day')


def main():
    """
    Entry point for the command line application.
    We use docopt to parse command line arguments.

    """
    from docopt import docopt

    arguments = docopt(__doc__, version='ES Curator')

    url = arguments.get('<url>', None)
    if not url:
        print 'Invalid ES URL'
        return

    period = arguments.get('--period')
    if not period:
        print 'Invalid retention period'
        return

    prefix = arguments.get('--prefix')
    if not prefix:
        print 'Invalid index prefix'
        return

    retention = datetime.timedelta(days=int(period))

    print 'Using url: %s' % url
    r = requests.get(url + '/_aliases')
    if r.status_code != requests.codes.ok:
        print "Error %s\n " % r.text
        exit(1)

    indices = r.json().keys()

    indices = filter(lambda index: index.startswith(prefix), indices)

    print 'Total %s indices' % len(indices)

    index_time_map = dict([(name, arrow.get(name[-10:])) for name in indices])

    indices_to_delete = dict([(name, arrow.get(name[-10:]))
                              for name, time in index_time_map.items()
                              if TODAY - time > retention])

    indices_to_delete = sorted(indices_to_delete.keys())

    print 'Indices to delete:'
    for name in indices_to_delete:
        print '  '+name

    if arguments.get('--dry'):
        print 'DRY mode, no changes made.'
        return

    for name in indices_to_delete:
        print 'Deleting index: %s ... ' % name,
        r = requests.delete(url + '/%s' % name)
        if r.status_code != requests.codes.ok:
            print "Error %s\n " % r.text
            exit(1)

    print 'Deleted %s indices' % len(indices_to_delete)

if __name__ == '__main__':
    main()
