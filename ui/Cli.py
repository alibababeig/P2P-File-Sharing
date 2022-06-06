class Cli:
    offer_row = '{: <5}{: <25}{: <13}{:}'

    @staticmethod
    def choose_offer(offers):
        offer_cnt = 0
        for _, matching_files in offers.items():
            offer_cnt += len(matching_files)

        if offer_cnt == 0:
            return None

        valid = False
        while not valid:
            choice = input(f'Choose one of the above offers [{1}..{offer_cnt} / 0 to cancel]: ')
            try:
                choice = int(choice)
                if choice == 0:
                    return None
            except:
                pass
            valid = choice in range(1, offer_cnt + 1)
            if not valid:
                print('Invalid choice! Please try again.')

        for offerer, matching_files in offers.items():
            for dic in matching_files:
                choice -= 1
                if choice == 0:
                    return (offerer, dic)

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
