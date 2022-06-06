import argparse
from ui.p2p_file_sharing import P2PFileSharing


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed-only', dest='seed_only', help='co', action='store_true', default=False)
    args = parser.parse_args()

    peer = P2PFileSharing()
    
    while not args.seed_only:
        query = input('enter your query:')
        res = peer.request_file(query)
        if res == 0:
            print('file successfully transmitted')
        elif res == -1:
            print('no files transmitted')