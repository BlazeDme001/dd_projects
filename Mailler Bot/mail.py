from configparser import ConfigParser
import yagmail

user_name = 'dme@shreenathgroup.in'
password = 'vofa ojog ekyx tagx'

def send_mail(to_add, to_cc, sub: str, body: str, attach=[]):
    try:
        yag = yagmail.SMTP(user_name, password)

        # Create an HTML email with the given body
        html_body = f"""
        <html>
            <body style="font-family: 'Arial', sans-serif; padding: 20px;">
                {body}
            </body>
        </html>
        """

        yag.send(to=to_add, cc=to_cc, subject=sub, contents=html_body, attachments=attach)
        yag.close()
        print('Mail Sent Successfully')
        return True
    except Exception as e:
        print(f'Error sending email: {e}')
        return False
