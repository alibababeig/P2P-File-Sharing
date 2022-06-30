from typing import Literal

from ui.color import Color


class Cli:
    offer_row = '{}{: <7}{}{: <15}{: <13}{:}'

    @staticmethod
    def print_log(str, _type: Literal['Debug', 'Info', 'Error', 'Success'] = 'Info', print_log=False):
        if not print_log and _type == 'Debug':
            return
        s = ''
        if _type == 'Debug':
            s += Color.WARNING.value
        elif _type == 'Error':
            s += Color.FAIL.value
        elif _type == 'Success':
            s += Color.OKGREEN.value
        else:
            s += ''

        print(s + str + Color.ENDC.value)

    @staticmethod
    def choose_offer(offers):
        offer_cnt = 0
        for _, matching_files in offers.items():
            offer_cnt += len(matching_files)

        if offer_cnt == 0:
            return None

        valid = False
        while not valid:
            Cli.print_log(
                f'Choose one of the above offers [{1}..{offer_cnt} / 0 to cancel]: ')
            choice = input()
            try:
                choice = int(choice)
                if choice == 0:
                    return None
            except:
                pass
            valid = choice in range(1, offer_cnt + 1)
            if not valid:
                Cli.print_log('Invalid choice! Please try again.', 'Error')

        for offerer, matching_files in offers.items():
            for dic in matching_files:
                choice -= 1
                if choice == 0:
                    return (offerer, dic)

    @staticmethod
    def show_offers(offers):
        print(Color.BOLD.value + Cli.offer_row
              .format('', '', '', 'Offerer ID', 'File Size', 'File Name') + Color.ENDC.value)
        line = 0
        for offerer, matching_files in offers.items():
            for dic in matching_files:
                filename = dic['name']
                filesize = Cli.__generate_filesize_string(dic['size'])
                line += 1

                print(Cli.offer_row
                      .format(Color.BOLD.value, f'[{line}]', Color.ENDC.value, offerer, filesize, filename))

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

    @staticmethod
    def print_progress_bar(iteration, total, speed, prefix='Progress:',
                           suffix='Completed', decimals=1, length=20, fill='█',
                           printEnd="\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                         (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)

        print(
            f'\r{"".join(map(str, [" " for i in range(55)]))}', end=printEnd)

        if iteration < total:
            print(
                f'\r{Color.OKBLUE.value}{prefix} |{bar}| {percent}%{Color.ENDC.value}  {Color.OKGREEN.value}{speed}{Color.ENDC.value}', end=printEnd)
        else:
            print(
                f'\r{Color.OKBLUE.value}{prefix} |{bar}| {suffix}{Color.ENDC.value} {Color.OKGREEN.value}{speed}{Color.ENDC.value}', end=printEnd)
            print()
