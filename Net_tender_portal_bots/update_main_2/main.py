import time
import schedule
import update_main

def main():
    bot_list = ['GoaTenders GOV NICGEP BOT','HPtenders GOV NICGEP BOT','HRYtenders GOV NICGEP BOT',
                'Iocletenders_NIC Nicgep BOT','J&KTenders GOV NICGEP BOT','JKDTenders GOV NICGEP BOT',
                'KeralaTenders GOV NICGEP BOT','LEHTenders GOV NICGEP BOT','LKDPTenders GOV NICGEP BOT',
                'Mahatenders GOV BOT','ManipurTenders GOV NICGEP BOT','MeghTenders GOV NICGEP BOT',
                'MizoramTenders GOV NICGEP BOT','Mptenders GOV BOT','NagalandTenders GOV NICGEP BOT',
                'Pmgsytenders GOV Nicgep BOT','PuducherryTenders GOV NICGEP BOT','PBTenders GOV NICGEP BOT',
                'SikkimTenders GOV NICGEP BOT','Tendersodisha GOV BOT','Tntenders GOV NIC BOT',
                'TripuraTenders GOV NICGEP BOT','UKtenders GOV NICGEP BOT','WBtenders GOV NICGEP BOT']

    for bot in bot_list:
        if bot == 'GoaTenders GOV NICGEP BOT':
            update_main.GoaTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'HPtenders GOV NICGEP BOT':
            update_main.HPtenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'HRYtenders GOV NICGEP BOT':
            update_main.HRYtenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Iocletenders_NIC Nicgep BOT':
            update_main.Iocletenders_NIC_Nicgep_BOT_main(bot)
        elif bot == 'J&KTenders GOV NICGEP BOT':
            update_main.J_KTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'JKDTenders GOV NICGEP BOT':
            update_main.JKDTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'KeralaTenders GOV NICGEP BOT':
            update_main.KeralaTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'LEHTenders GOV NICGEP BOT':
            update_main.LEHTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'LKDPTenders GOV NICGEP BOT':
            update_main.LKDPTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Mahatenders GOV BOT':
            update_main.Mahatenders_GOV_BOT_main(bot)
        elif bot == 'ManipurTenders GOV NICGEP BOT':
            update_main.ManipurTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'MeghTenders GOV NICGEP BOT':
            update_main.MeghTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'MizoramTenders GOV NICGEP BOT':
            update_main.MizoramTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Mptenders GOV BOT':
            update_main.Mptenders_GOV_BOT_main(bot)
        elif bot == 'NagalandTenders GOV NICGEP BOT':
            update_main.NagalandTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Pmgsytenders GOV Nicgep BOT':
            update_main.Pmgsytenders_GOV_Nicgep_BOT_main(bot)
        elif bot == 'PuducherryTenders GOV NICGEP BOT':
            update_main.PuducherryTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'PBTenders GOV NICGEP BOT':
            update_main.PBTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'SikkimTenders GOV NICGEP BOT':
            update_main.SikkimTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Tendersodisha GOV BOT':
            update_main.Tendersodisha_GOV_BOT_main(bot)
        elif bot == 'Tntenders GOV NIC BOT':
            update_main.Tntenders_GOV_NIC_BOT_main(bot)
        elif bot == 'TripuraTenders GOV NICGEP BOT':
            update_main.TripuraTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'UKtenders GOV NICGEP BOT':
            update_main.UKtenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'WBtenders GOV NICGEP BOT':
            update_main.WBtenders_GOV_NICGEP_BOT_main(bot)


def job():
    try:
        main()
    except:
        pass
    print('BOT executed at 4:45 AM')


if __name__ == '__main__':
    schedule.every().day.at('04:45').do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)


