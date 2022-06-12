import argparse
from ui.Cli import Cli
from ui.p2p_file_sharing import P2PFileSharing
from status.status import Status


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed-only', dest='seed_only',
                        help='co', action='store_true', default=False)
    args = parser.parse_args()

    peer = P2PFileSharing()

    while not args.seed_only:
        Cli.print_log('enter your query:', 'Info')
        query = input()
        res = peer.request_file(query)
        if res == Status.SUCCESS:
            Cli.print_log('file successfully transmitted', 'Success')
        elif res == Status.NO_CHOICE:
            Cli.print_log('no files transmitted', 'Error')
        elif res == Status.NO_OFFERS:
            Cli.print_log('no offers received', 'Error')
