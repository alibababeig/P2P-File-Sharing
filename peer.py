import argparse
from ui.Cli import Cli
from core.p2p_file_sharing import P2PFileSharing
from status.status import Status


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed-only', '-so', dest='seed_only',
                        help='enable this flag if you don\'t want to download any files',
                        action='store_true', default=False)
    parser.add_argument('--chunk-size', '-cs', dest='chunk_size',
                        help='set a custom value for chunk size', default='10000')
    args = parser.parse_args()
    try:
        chunk_size = int(args.chunk_size)
    except:
        Cli.print_log('bad input type', 'Error')
        exit()

    peer = P2PFileSharing(chunck_size=chunk_size)

    while not args.seed_only:
        res = peer.request_file()
        if res == Status.SUCCESS:
            Cli.print_log('file successfully transmitted', 'Success')
        elif res == Status.NO_CHOICE:
            Cli.print_log('no files transmitted', 'Error')
        elif res == Status.NO_OFFERS:
            Cli.print_log('no offers received', 'Error')
        elif res == Status.TRANSFER_INTERRUPTED:
            Cli.print_log('transmission interrupted', 'Error')
