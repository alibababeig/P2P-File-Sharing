from importlib.metadata import files
from os import stat


class Cli:
    offer_row = '{: <5}{: <25}{: <13}{:}'

    @staticmethod
    def show_offers(offers):
        print(Cli.offer_row
              .format('', 'Offerer Address', 'File Size', 'File Name'))
        line = 0
        for offerer, matching_files in offers.items():
            offerer_ip, offerer_port = offerer

            for dic in matching_files:
                filename = dic['name']
                filesize = Cli.__generate_filesize_string(dic['size'])
                line += 1

                print(Cli.offer_row
                      .format(line, f'{offerer_ip}:{offerer_port}', filesize, filename))

    def __generate_filesize_string(filesize):
        if filesize < 1000:
            return f'{filesize} B'

        if filesize < 1000 ** 2:
            return f'{filesize / 1000:.2f} KB'

        if filesize < 1000 ** 3:
            return f'{filesize / (1000 ** 2):.2f} MB'

        if filesize < 1000 ** 4:
            return f'{filesize / (1000 ** 3):.2f} GB'

        return 'TOO BIG!'
