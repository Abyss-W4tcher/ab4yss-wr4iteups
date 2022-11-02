# How to easily setup SPIP with docker compose

## Disclaimer

Do not use this in a production environment. It is for testing purposes only.

## Setup

For my researches, I needed the possibility to deploy quickly a SPIP environment on our machines. For that, I took the `docker-compose` from https://thinkloveshare.com/hacking/rce_on_spip_and_root_me/ as a base.

Steps :

1. Install `docker-compose` and `docker`
2. Create a directory (e.g. `docker_spip`) and position yourself inside it.
3. Paste the `spip-compose.yml` file.
4. Create a `html` directory.
5. You have : 
   ```
   docker_spip/
   |-   html/
   |-   spip-compose.yml
   ```
6. Edit the `spip-compose.yml`, to match the PHP/MySQL versions (https://www.spip.net/en_article4351.html), according to the version of SPIP you want.
7. Execute `docker-compose -f spip-compose.yml up` and the dockers will setup.
8. Access SPIP loader on http://127.0.0.1:3309/spip_loader.php and install the version wanted (https://www.spip.net/en_article6650.html).   
**TIP** : The version you are looking for may not be listed in the dropdown menu. However, you can send this GET request to initiate the procedure with a custom version :
`/spip_loader.php?chemin=spip%2Farchives%2Fspip-v[version number (e.g. 4.1.5)].zip&dest=&range=0&etape=charger`
9.  Once everything is downloaded, go to http://127.0.0.1:3309/ecrire to continue (if not already redirected).
10. For MySQL, do not specify `localhost:3307` or `127.0.0.1:3307` as IP, but the one assigned to your interface (e.g. 192.168.1.1:3307). Credentials : `root:root`.
11. Follow the instructions and SPIP will be setup !
12. Bonus step : change the permissions of the `html` folder, because it is owned by root. It may be annoying when editing or removing files.

Useful one-liner (step 1 to 4):  

`mkdir docker_spip && cd docker_spip && wget https://github.com/Abyss-W4tcher/ab4yss-wr4iteups/raw/master/SPIP%204.1.2%20Vulnerabilities/How%20to%20easily%20setup%20SPIP%20with%20docker-compose/spip-compose.yml && mkdir html`

## Infos

I added a lot of dependencies needed by SPIP in the docker-compose. Be careful that this is PHP, and some of them may not be compatible from one version to another. If you have to retrograde (or if in the future there are compatibility issues), you can remove all the `libXX` and `gd` statements from spip-compose.yml. Some functionalities may not work correctly though.  
The best choice would still be to adapt the dependencies, by changing the syntax.
You can change the binding ports as you want in the docker-compose, or even add other images (e.g. phpMyAdmin).

---

/!\ The spip_loader is now compressed into a phar archive. The problem was that I couldn't managed to setup with it, as the browser was trying to download the PHP file `spip_loader.php/index.php` and not display them. I had to make a trick to extract the phar archive and obtain the plain PHP files.
Unfortunately, all the spip_loader files are in the root directory, because it doesn't give us the opportunity to choose the spip install location.


## Ressources

https://github.com/laradock/php-fpm/blob/master/Dockerfile-8.1
