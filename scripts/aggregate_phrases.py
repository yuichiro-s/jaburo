import sys
from collections import defaultdict


def main(args):
    d = defaultdict(int)
    for path in args.data:
        with open(path) as f:
            for line in f:
                freq, phrase, tags = line.split('\t')
                d[(phrase, tags)] += int(freq)
    items = d.items()
    if args.min > 1:
        items = filter(lambda k_v: k_v[1] >= args.min, items)
    items = sorted(items, key=lambda k_v: -k_v[1])
    for (phrase, tags), freq in items:
        tags = tags.strip()
        try:
            print('{}\t{}\t{}'.format(freq, phrase, tags))
        except Exception as e:
            print('Failed to print: {}'.format(str((phrase, tags, freq))), file=sys.stderr)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Aggregate extracted phrases')
    parser.add_argument('data', nargs='+', help='frequency files')
    parser.add_argument('--min', default=2, type=int, help='minimum frequency')
    main(parser.parse_args())
