import schedule
import mail
import time


def send_new_year_email():
   html_message = """
   <!DOCTYPE html>
   <html lang="en">
   <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Happy New Year 2024</title>
   </head>
   <body style="font-family: 'Arial', sans-serif; background-color: #f4f4f4; color: #333; padding: 20px;">

      <table cellspacing="0" cellpadding="0" border="0" align="center" width="600" style="background-color: #fff; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); margin: 0 auto;">
         <tr>
               <td style="padding: 20px;">
                  <h1 style="color: #007BFF;">Dear Team Shreenath,</h1>

                  <p style="line-height: 1.6;">
                     As we stand on the threshold of a brand new year, I want to express my heartfelt gratitude for the incredible journey we've shared together in 2023. Your hard work, dedication, and team spirit have been the driving force behind our success.
                  </p>
                  <p style="line-height: 1.6;">
                     As we reflect on the achievements and milestones of the past year, it's clear that each member of our team has played a crucial role in our collective success. Your dedication and unwavering commitment have truly set us apart.
                  </p>
                  <p style="line-height: 1.6;">
                     As we embark on the journey that is 2024, let's carry forward the lessons learned, celebrate our shared victories, and welcome the new opportunities that lie ahead. Together, as Team Shreenath, we can overcome any challenge and reach new heights.
                  </p>
                  <p style="line-height: 1.6;">
                     Wishing you all a Happy New Year filled with excitement, prosperity, and the realization of your dreams! May the coming year be marked by even greater accomplishments and moments of joy for each and every one of you.
                  </p>

                  <p style="line-height: 1.6;">Cheers to 2024!</p>
                  <p style="line-height: 1.6;">Warm regards,<br>Shreenath Enterprise</p>
               </td>
         </tr>
      </table>

   </body>
   </html>
   """

   email_addresses = [
      'ashish@shreenathgroup.in',
      'raman@shreenathgroup.in',
      'gurpreetlamby@shreenathgroup.in',
      'technical@shreenathgroup.in',
      'sentmhl@gmail.com',
      'pooja@shreenathgroup.in',
      'ramit.shreenath@gmail.com',
      'admin@shreenathgroup.in',
      'pintu@shreenathgroup.in',
      'installation@shreenathgroup.in',
      'ramit.shreenath@gmail.com'
   ]

   mail.send_mail(to_add=email_addresses, to_cc=[], sub='Happy New Year 2024', body=html_message)


def send_new_year_wp():
   num_dict = {
      'Ashis': '9988880885',
      'Raman': '8528529292',
      'Gurpreet': '6283287354',
      'Pooja': '7347008054',
      'Ramit': '6283287351'
   }


schedule.every().day.at("00:00").do(send_new_year_email)


while True:
   print('Starting the bot')
   schedule.run_pending()
   time.sleep(1)

