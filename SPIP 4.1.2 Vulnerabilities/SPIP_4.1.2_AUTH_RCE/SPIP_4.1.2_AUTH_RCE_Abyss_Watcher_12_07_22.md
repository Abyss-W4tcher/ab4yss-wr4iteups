# How a security fix introduced a security issue in SPIP 4.1.2
---
#### Author : Abyss Watcher
---
# Context

SPIP is a free french CMS, developed in PHP. Here is a short resume from their [website](https://www.spip.net/en_rubrique25.html) : 

>SPIP is a publishing system for the Internet in which great importance is attached to collaborative working, to multilingual environments, and to simplicity of use for web authors. It is free software, distributed under the GNU/GPL licence. This means that it can be used for any Internet site, whether personal or institutional, non-profit or commercial.

One of their main consumer is [Root Me](https://www.root-me.org), a learning website oriented in cybersecurity.
After Root Me introduced two SPIP related challenges on their platform, I got more familiar with the SPIP core, as I needed to setup a local environment to resolve them.

Two Root Me users discovered some SQLi and RCE on the site [recently](https://www.root-me.org/en/Information/Hacks/) ([real](https://www.root-me.org/real) also found an SQLi but isn't mentioned on the "hacks" page) :

<img src="../images/5dbc6efe458fabf2981192f240d412f58823443caa1bb7039bc37bc3e86f48a8.png">

As I wanted the little medal <del>of honor</del><img src="../images/d96c965a03e85d319b924e69c9f489745eb14c3eecf1979ad269842afa37ad57.svg" width=32 height=20> given to Root Me pwners, I started investigating SPIP.

The local test environment was composed of the latest SPIP version (4.1.2 from 20/05/2022), runned by PHP 8.0.0 and MySQL 5.6. "parano" mode activated (anti-XSS).

<div style="page-break-after: always;"></div>

# Stored XSS (+ CSRF and RCE)

You can find details on this part in the report named "SPIP_4.1.2_XSS_Abyss_Watcher_30_06_22.pdf"¨(it's in french sorry :)). They were my first discoveries, and already gave me the right to have the holy medal (and my name in the pwners) : 

![picture 3](../images/a2a16921932a73e2303756f1da070291054740346985f6b3e8ba2e355905043f.png)  

>Traduction : "*has identified a stored XSS vulnerability in any rendered field*"

I was happy, but it wasn't **enough**. 

<div style="page-break-after: always;"></div>

# Post-Auth RCE

## privileges needed to exploit

You need to have the "author" role, or be able to see articles in the backend.

## work in pair, maximise your chances

As I am not really a bug bounty guy, I asked [SpawnZii](https://www.root-me.org/SpawnZii) (http://yeswefiak.fr:1313/) to join me in my researches. We'll cover more surface and help each other see things that could have been missed. 

## check what have already been done

How could I write these lines without mentioning the work done here by Laluka : https://thinkloveshare.com/hacking/rce_on_spip_and_root_me/. He basically destroyed the scope, by building tools and manually reviewing everything. He pulled out many vulnerabilities (as mentionned earlier), which where all **ｆｉｘｅｄ** at the time we were doing the bounty. Or maybe not :).

## "on est bon, rien a faire"

After many hours trying to exploit via file upload, dns rebinding etc., I decided to read the Laluka article one more time. I noticed this PHP comment in a SPIP commit, which fixed the RCE :

![picture 4](../images/eeee1b1aa2c2fd34f489212d2b9bab942aa1e79cba9e06c4597f7a5f8187b631.png)  

> Traduction : "**we are good, nothing to do**"

At the instant I saw this text, I knew something was wrong. I felt it in my spine.

<div style="page-break-after: always;"></div>

## debug, try to understand what is going on

The _oups parameter allows to cancel an action, like a miss click on "Remove author" from the "edit_article" page. The previous code can be found in "prive/formulaires/editer_liens.php" :

L133 -> 143 (formulaires_editer_liens_charger_dist) :

```
$oups = _request('_oups') ?? '';
	if ($oups) {
		if (unserialize(base64_decode($oups))) {
			// on est bon, rien a faire
		} elseif (unserialize($oups)) {
			// il faut encoder
			$oups = base64_encode($oups);
		} else {
			$oups = '';
		}
	}
```

We can see that it is checking for the GET parameter "_oups". Let's add some glorious `print_r`, and try to pass the `if`s :

![picture 5](../images/85612877c76dafcb54cda62cd453bdc5efdb8558960dd998cc6a3837ea3cd91b.png)  

Well, it was easy. We just needed to pass a valid PHP object encoded in base64 : `'czoxOiJhIjtpOjE6MDs=' : 's:1:"a";i:1:0;'`.  
The value is reflected in an HTML field : 

`<input type="hidden" name="_oups" value="czoxOiJhIjtpOjE6MDs=">`

Yup, yup, yup. Wanna XSS ?

<img src="../images/c746d4efba320c498aa67bdac1d74f1aa1fc22f1f1baea086d913fc263a4be9b.png" width=350> 

## quotes everywhere, xss everywhere

Let's inject random quotes and angle brackets `_oups=czoxOiJhIjtpOjE6MDs='">` :

![picture 12](../images/9d24128350cc6d7957e3c75afd050493e5c1a54ed5d151e9f74a4593c5e2197a.png)  

![picture 13](../images/257127c4c4ab9a3e4aaa6c4dfc6dc56d76f056fdb5709ebb668e5cffaf7f90bf.png)  

<img src="../images/b20123d86d2c1428de66b36d119f808526ff80bc1865475610a1191daaf9d1ae.png" width=250> 

This does not look good, noting that at this point, I didn't even checked what was the rest of the code. The only observation I could make was that the unserialize function only checked if "_oups" started with a valid base_64 object.  

Does it mean that everything after the b64 is processed without restiction ?

<div style="page-break-after: always;"></div>

## investigate a bit

The code here is the end of the function. Let's check with `print_r` what it looks like :
```
$valeurs = [
		'id' => "$table_source-$objet-$id_objet-$objet_lien", // identifiant unique pour les id du form
		'_vue_liee' => $skel_vue,
		'_vue_ajout' => $skel_ajout,
		'_objet_lien' => $objet_lien,
		'id_lien_ajoute' => _request('id_lien_ajoute'),
		'objet' => $objet,
		'id_objet' => $id_objet,
		'objet_source' => $objet_source,
		'table_source' => $table_source,
		'recherche' => '',
		'visible' => 0,
		'ajouter_lien' => '',
		'supprimer_lien' => '',
		'qualifier_lien' => '',
		'ordonner_lien' => '',
		'desordonner_liens' => '',
		'_roles' => $roles, # description des roles
		'_oups' => $oups,
		'editable' => $editable,
	];

	// les options non definies dans $valeurs sont passees telles quelles au formulaire html
	$valeurs = array_merge($options, $valeurs);
	print_r($valeurs);
	return $valeurs;
```

<div style="page-break-after: always;"></div>

Try to render an HTML tag `<b>BOLD ?</b>`: 

![picture 14](../images/572d0439615d9f2152b807155a879889f1b880057be33f4ad09ff1d09a5c034c.png)  

We can see that the "_oups" value holds our valid base64 object, and everything that comes after. I don't know SPIP enough to explain why this is rendered like that, but my guess is that the "templates" interprets it as if it was valid code passed from the server.

Soooooo ?

<div style="page-break-after: always;"></div>

## _oupsed

Retranscription (screenshot from the conversation with SpawnZii) :

>Dude, I think I found a reflected XSS with this payload :

![picture 17](../images/b57caf30d2ff829ef42b3d6be145d083cd252603f9b47d3617ae10f7c225b20d.png)  

*45 seconds later* :

![picture 18](../images/973be6b2653cc3b01e7cf3612356719304de456c2aba68c72efcad66210502a7.png)  

Well, well, well, what could have happened between those two messages ? 

Hint :

<img src="../images/49dd8834df7e677b12ff2505ad2a9b50ebbccb5feda0e8145469e178a44adbb6.png" width=450>

Answer (`_oups=czoxOiJhIjtpOjE6MDs=%27"><?php%20echo(%27RCE%27)?>`) :

![picture 21](../images/268dc8e7967375a7ec418d84cba4f56b5405477f8758cb073c6cb9d9bcb30dd9.png)  

The php tags are gone, and we can see the letters "R","C","E" kindly appearing on our screen :).

What is happening :

```
if (_request('annuler_oups') and $oups = _request('_oups') and $oups = base64_decode($oups) and $oups = unserialize($oups))
```

So, it first checks for a valid base64_decode, which is true. Then for a valid base64 object, which is also true (the object instantiates a string "a" of length 1) :

![picture 40](../images/test_b64decode_unserialize.png) 

It considers the user input as valid, and sends it to further processing (dynamic eval engine of SPIP) which renders our code.

We now have the ability to execute arbitrary code on the server, with any author account. A first approach could be to dump the `phpinfo()` to check the disabled functions, then build payloads to exfiltrate files, secrets (e.g. : SQL creds in `config/connect.php`), try to privesc etc.

After this discovery, we decided to create POC's for exploit automation. It is joined in this folder, under the name "SPIP_4.1.2_AUTH_RCE_POC.py". We did not pushed it really far, just an interactive webshell on terminal, with basic error handling.

## be good, report to SPIP

We decided to report the vulnerability to SPIP, because we had no interest into exploiting or selling it. [g0uZ](https://www.root-me.org/g0uZ), foundator of Root Me, is also in charge of the security in SPIP core. They were both quickly capable to fix the issue.

# Conclusion

It was a great experience to work in team with SpawnZii, and being able to make Root Me and SPIP a little more secure is great. We managed to generate two POC, one led to CSRF/RCE via a stored XSS, the other to RCE via logic errors. 

There are certainly still bugs present, but we don't think continuing pentesting it for now.
I hope that you had pleasure to read these lines, and that it motivated into finding exploits (in a white hat way). Also, don't forget to double check your security fixes :).

<img src="../images/2d9a35b486096e2b7914d46b2abf9feb28145298306e19b63ed60569104e7499.png" width=200> 


## Fix :

- https://git.spip.net/spip/spip/pulls/5253

