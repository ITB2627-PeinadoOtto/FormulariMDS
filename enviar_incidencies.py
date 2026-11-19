#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enviament massiu d'incidències a un Google Form (POST directe amb requests).

==============================  CONFIGURACIÓ  ==============================
1) FORM_URL: obre el teu formulari, copia la URL i canvia el final
   ".../viewform" (o "/edit") per "/formResponse".
   Exemple: https://docs.google.com/forms/d/e/1FAIpQLSxxxxxxxx/formResponse

2) ENTRY_IDS: substitueix cada "entry.XXXXX" pel teu ID real.
   Com trobar-los:
     - Obre el formulari -> menú ⋮ -> "Obtén un enllaç prèviament emplenat"
       (omple tots els camps amb qualsevol valor i copia l'enllaç), o bé
     - Obre el formulari, clic dret -> "Inspecciona" i busca "entry." al HTML.
   Camps especials:
     - Data  -> necessita 3 IDs derivats: entry.X_year, entry.X_month, entry.X_day
                (aquí només cal posar la base "entry.X")
     - Hora  -> necessita 2 IDs derivats: entry.Y_hour, entry.Y_minute
                (aquí només cal posar la base "entry.Y")
     - Si el teu formulari té data+hora en un únic camp "Data i hora", la base
       és la mateixa per a ambdós (entry.X_year, entry.X_month, entry.X_day,
       entry.X_hour, entry.X_minute). Si són dues preguntes separades, posa
       bases diferents a DATA i HORA.

3) NUM_INCIDENCIES: nombre d'incidències a enviar (100-400).

IMPORTANT: Fes-lo servir només sobre formularis teus o en entorns de prova.
=============================================================================
"""

import random
import string
import sys
import time
from datetime import datetime, timedelta

import requests

# ------------------------------- CONFIG -----------------------------------
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd9Y7WZHei0xpZo6y2pEB6Cu2yyEuRFLo4_MwxjMK0qAXzGng/formResponse"

NUM_INCIDENCIES = 3000      # Canvia a un valor entre 100 i 400
PAUSA_SEGONS = 0.00005         # Pausa entre peticions
TIMEOUT = 15               # Timeout de cada petició (segons)
DIES_ENRERE = 30           # Rang de dates: últims N dies

ENTRY_IDS = {
    "reportant": "entry.112120754",      # 1. Nom i cognoms de qui reporta
    "correu": "entry.213771520",         # 2. Correu de contacte
    "afectat": "entry.762065113",        # 3. Persona afectada
    "ubicacio": "entry.1479404175",      # 4. Ubicació
    "data": "entry.1968293302",          # 5a. Data (base per a _year, _month, _day)
    "hora": "entry.1968293302",          # 5b. Hora (base per a _hour, _minute)
    "tipus_equip": "entry.432632866",    # 6. Tipus d'equip
    "marca_model": "entry.154359071",    # 7. Marca i model
    "codi": "entry.812968272",           # 8. Codi / etiqueta
    "resum": "entry.1037154107",         # 9. Resum del problema
    "descripcio": "entry.1656687285",    # 10. Descripció extensa
    "recurrent": "entry.470542549",     # 11. Ha ocorregut anteriorment?
    "urgencia": "entry.1314883198",      # 12. Nivell d'impacte
}

# --------------------------- DADES DE MOSTRA ------------------------------
NOMS = [
    "Marta", "Jordi", "Núria", "Pau", "Laia", "Marc", "Anna", "Oriol", "Clara",
    "Joan", "Montserrat", "Albert", "Queralt", "Arnau", "Mireia", "Sergi",
    "Carla", "Pere", "Aina", "Xavier", "Judit", "Ferran", "Berta", "Eric",
    "Neus", "Guillem", "Roser", "Biel", "Ona", "Ramon", "Cristina", "Isaac",
    "Gemma", "Roger", "Sílvia", "Adrià", "Maria", "Josep", "Alba", "Francesc",
    "Èlia", "Jaume", "Meritxell", "Hugo", "Paula", "David", "Raquel", "Nil",
    "Laura", "Ivan", "Helena", "Carles", "Eva", "Lluís", "Mar", "Àlex",
]

COGNOMS = [
    "Garcia", "Martínez", "Puig", "Vila", "Ferrer", "Soler", "Serra", "Roca",
    "Vidal", "Pons", "Ribas", "Costa", "Font", "Mas", "Casals", "Pujol",
    "Sala", "Prat", "Camps", "Bosch", "Molina", "Torres", "Ferrando", "Sans",
    "Güell", "Ortega", "Rovira", "Fabra", "Baró", "Planas", "Abad", "Navarro",
    "Gil", "Llobet", "Domènech", "Vallès", "Mir", "Esteve", "Carbonell",
    "Bonet", "Jover", "Marquès", "Rius", "Palau", "Salvador", "Subirats",
    "Cabré", "Riera", "Tarrés", "Aguilar", "Montoya", "Blasco", "Quintana",
]

UBICACIONS = (
    [f"Aula {n}" for n in range(200, 206)]
    + [f"Departament {n}" for n in range(1, 6)]
    + [f"Oficina {n}" for n in range(1, 6)]
)

# Tipus d'equip -> models realistes
EQUIPS = {
    "Ordinador de sobretaula": [
        "HP ProDesk 400 G7", "Dell OptiPlex 3080", "Lenovo ThinkCentre M70s",
        "HP EliteDesk 800 G6", "Dell OptiPlex 7090", "Lenovo ThinkCentre M920s",
        "ASUS ExpertCenter D500", "Acer Veriton X2690G",
    ],
    "Ordinador portàtil": [
        "HP ProBook 450 G8", "Lenovo ThinkPad E14", "Dell Latitude 5420",
        "Acer TravelMate P215", "ASUS ExpertBook B1", "Lenovo IdeaPad 3 15",
        "HP EliteBook 840 G7", "Dell Vostro 3510", "Lenovo ThinkPad L15",
    ],
    "Tauleta tàctil": [
        "Samsung Galaxy Tab A8", "Apple iPad 9a gen", "Lenovo Tab M10",
        "Huawei MatePad T10s", "Samsung Galaxy Tab S6 Lite", "Apple iPad Air 4",
    ],
    "Telèfon d'empresa": [
        "Samsung Galaxy A53", "iPhone 12", "Xiaomi Redmi Note 11",
        "Motorola Moto G62", "Samsung Galaxy S21 FE", "Google Pixel 6a",
        "Cisco IP Phone 8841", "Yealink T54W",
    ],
    "Monitor": [
        "Dell P2422H", "HP P24h G4", "Lenovo ThinkVision T24i", "LG 24MK430H",
        "Samsung S24R350", "AOC 24B1H", "Philips 243V7QDSB", "BenQ GW2480",
    ],
    "Teclat": [
        "Logitech K120", "HP 125 Wired Keyboard", "Dell KB216",
        "Lenovo Essential Wired", "Logitech MK270 (combo)", "Microsoft Wired 600",
        "Genius KB-110",
    ],
    "Ratolí": [
        "Logitech M185", "HP X500", "Dell MS116", "Lenovo 300 USB",
        "Logitech B100", "Microsoft Basic Optical", "Trust Primo",
    ],
    "Impressora": [
        "Epson EcoTank ET-2850", "HP LaserJet Pro M404dn", "Brother HL-L2350DW",
        "Canon PIXMA G3510", "HP OfficeJet Pro 9015e", "Xerox B210",
        "Kyocera ECOSYS P2040dw", "Brother MFC-L3750CDW", "Ricoh SP 213w",
    ],
    "Projector": [
        "Epson EB-W49", "BenQ MH733", "Optoma HD146X", "ViewSonic PA503W",
        "Epson EB-X49", "Acer X1226H", "NEC M403H",
    ],
    "Pantalla interactiva": [
        "Promethean ActivPanel 9", "Samsung Flip 2 WM55R", "ViewSonic ViewBoard IFP6550",
        "SMART Board MX065", "Newline Flex TT-6520", "BenQ RP6502",
    ],
    "Altaveus": [
        "Logitech Z313", "Creative Pebble V2", "Trust Leto 2.0", "Genius SP-HF160",
        "Logitech Z200", "JBL Control 1 Pro", "Edifier R1280DB",
    ],
    "Càmera web": [
        "Logitech C920 HD Pro", "Logitech C270", "Microsoft LifeCam HD-3000",
        "Trust Taxon QHD", "Razer Kiyo", "Logitech Brio 4K", "Genius FaceCam 1000X",
    ],
    "Auriculars": [
        "Logitech H390", "Jabra Evolve 40", "Plantronics Blackwire 3220",
        "Sennheiser SC 60", "HP H3100", "Logitech H151", "Jabra Evolve2 30",
    ],
    "Router": [
        "TP-Link Archer AX55", "Cisco RV340", "MikroTik hAP ac2",
        "Ubiquiti UniFi Dream Router", "ASUS RT-AX58U", "Netgear Nighthawk R7000",
        "Zyxel VMG8825", "Huawei HG8245H",
    ],
    "Switch de xarxa": [
        "Cisco SG350-28", "TP-Link TL-SG1024D", "HPE OfficeConnect 1920S",
        "Netgear GS748T", "Ubiquiti UniFi Switch 24", "D-Link DGS-1210-24",
        "Aruba Instant On 1930", "Zyxel GS1900-24E",
    ],
    "Servidor": [
        "Dell PowerEdge R340", "HPE ProLiant DL360 Gen10", "Lenovo ThinkSystem SR250",
        "Dell PowerEdge T140", "HPE ProLiant ML350 Gen10", "Supermicro SYS-5019P",
        "Synology RackStation RS1221+", "QNAP TS-453D (NAS)",
    ],
}

# Problemes per tipus d'equip: (resum, [detalls ampliats])
PROBLEMES = {
    "Ordinador de sobretaula": [
        ("No s'encén l'ordinador", ["En prémer el botó d'engegada no reacciona ni s'il·lumina cap LED.", "S'ha comprovat el cable d'alimentació i la regleta i continua sense donar senyal."]),
        ("Va molt lent", ["Tarda més de cinc minuts a arrencar i en obrir qualsevol programa es queda penjat.", "El rendiment ha empitjorat durant l'última setmana, sobretot en obrir el navegador."]),
        ("Pantalla blava recurrent", ["Es reinicia sol amb una pantalla blava un parell de vegades al dia.", "Surt un error de memòria just quan s'inicia sessió amb l'usuari del domini."]),
        ("Fa un soroll estrany", ["El ventilador fa un brunzit fort i l'equip s'escalfa molt després de mitja hora.", "Se sent un clic repetitiu que sembla provenir del disc dur."]),
        ("No es connecta a la xarxa", ["Mostra «xarxa no identificada» i no obté adreça IP malgrat canviar de cable.", "No té accés a les unitats compartides ni a internet des d'aquest matí."]),
    ],
    "Ordinador portàtil": [
        ("La bateria no carrega", ["Connectat al carregador indica «connectat, no carrega» i s'apaga en desendollar-lo.", "La bateria dura menys de deu minuts malgrat estar al 100 %."]),
        ("Pantalla trencada", ["La pantalla té una esquerda a l'angle inferior dret i apareixen línies verticals.", "Va caure de la taula durant el canvi de classe i la imatge es veu distorsionada."]),
        ("El teclat no respon", ["Diverses tecles (A, S, Enter) han deixat de funcionar i cal prémer-les amb força.", "Una part del teclat no escriu res després d'haver-se vessat una mica d'aigua."]),
        ("No arrenca el sistema", ["Es queda a la pantalla del logotip i apareix el missatge «No bootable device».", "Després d'una actualització de Windows entra en bucle de reparació automàtica."]),
        ("No detecta el Wi-Fi", ["No apareix cap xarxa sense fil disponible i l'adaptador sembla desactivat.", "Es connecta però cau constantment i demana la contrasenya cada pocs minuts."]),
    ],
    "Tauleta tàctil": [
        ("La pantalla tàctil no respon", ["El tàctil només respon a zones concretes i de vegades fa tocs fantasma.", "Després d'una caiguda la meitat de la pantalla ha deixat de detectar els dits."]),
        ("No carrega", ["El connector de càrrega sembla fluix i només carrega movent el cable.", "Ha deixat de carregar amb tots els carregadors que s'han provat."]),
        ("Aplicacions que es tanquen soles", ["Les aplicacions educatives es tanquen sense avís quan s'obren per tercer cop.", "Després de l'última actualització l'aplicació de classe es bloqueja a l'inici."]),
    ],
    "Telèfon d'empresa": [
        ("No hi ha cobertura", ["Mostra «sense servei» a l'edifici, però el d'un company funciona bé.", "La targeta SIM no és reconeguda després de reiniciar el dispositiu."]),
        ("Micròfon no funciona", ["L'interlocutor no sent res durant les trucades, només amb altaveu.", "El so surt bé però el micròfon queda mut intermitentment."]),
        ("Bateria s'esgota ràpid", ["Passa del 100 % al 20 % en poques hores sense gairebé usar-lo.", "Es calenta de manera anormal fins i tot en estat de repòs."]),
    ],
    "Monitor": [
        ("No dona imatge", ["La llum indicadora és verda però la pantalla queda en negre.", "Mostra «sense senyal» tot i canviar de cable HDMI i de port."]),
        ("Pantalla parpelleja", ["La imatge tremola de manera intermitent, sobretot en canviar de finestra.", "El parpelleig apareix en arrencar i desapareix si es mou el cable."]),
        ("Franges de colors a la pantalla", ["Hi ha línies verticals de colors que ocupen una tercera part de la pantalla.", "Ha aparegut una taca fosca a la part central que va creixent."]),
    ],
    "Teclat": [
        ("Tecles que no funcionen", ["Algunes tecles no registren la pulsació i cal prémer-les diverses vegades.", "El teclat escriu caràcters repetits sense parar en prémer una tecla."]),
        ("El teclat no és detectat", ["L'ordinador no detecta el dispositiu per USB en cap dels ports.", "El receptor sense fil no es vincula i la llum del teclat no s'il·lumina."]),
    ],
    "Ratolí": [
        ("El cursor es mou sol", ["El punter salta per la pantalla i fa clics que ningú no ha fet.", "El moviment és erràtic sobre qualsevol superfície, fins i tot amb catifa."]),
        ("El ratolí no respon", ["No s'encén el làser inferior i l'ordinador no el detecta.", "El botó esquerre es queda encallat i fa doble clic constant."]),
    ],
    "Impressora": [
        ("Atasco de paper continu", ["Es produeix un encallament de paper cada vegada que s'imprimeix a doble cara.", "Mostra «embús de paper» tot i que la safata és buida."]),
        ("No imprimeix", ["Els treballs es queden a la cua i la impressora apareix com a fora de línia.", "Imprimeix pàgines en blanc amb el tòner/tinta aparentment nou."]),
        ("Impressió amb ratlles", ["Les pàgines surten amb línies horitzontals i colors apagats.", "El cap d'impressió sembla obstruït i la neteja automàtica no ha servit."]),
        ("Falta tòner/tinta", ["Indica nivell baix i ja no es pot imprimir cap document.", "Hi ha cartutxos de recanvi però cal algú que n'expliqui el canvi."]),
    ],
    "Projector": [
        ("La imatge surt borrosa", ["No es pot enfocar bé la imatge, sobretot als marges de la projecció.", "La lent sembla bruta o amb vapor, i la nitidesa és molt baixa."]),
        ("El projector s'apaga sol", ["Es desconnecta als deu minuts amb un llum d'avís vermell intermitent.", "Es sobreescalfa i s'atura durant les classes de l'última hora."]),
        ("No detecta la font", ["Mostra «sense senyal» connectat per HDMI i VGA a l'ordinador de l'aula.", "La imatge apareix amb tonalitat verda o rosada."]),
    ],
    "Pantalla interactiva": [
        ("El tàctil està desajustat", ["En tocar un punt el cursor apareix desplaçat uns centímetres.", "El calibratge perd la precisió cada cop que es reinicia."]),
        ("No es connecta amb l'ordinador", ["No es transmet la imatge i el USB tàctil no és reconegut.", "El mode de pantalla compartida es talla cada pocs minuts."]),
    ],
    "Altaveus": [
        ("No surt so", ["Estan connectats i encesos però no emeten cap so.", "Només sona un dels dos altaveus i amb molta distorsió."]),
        ("Soroll de fons", ["Se sent un brunzit constant i petits cops al canviar el volum.", "L'altaveu fa un xiulet agut en connectar-los al jack."]),
    ],
    "Càmera web": [
        ("La càmera no es detecta", ["Les aplicacions de videotrucada no mostren cap dispositiu de vídeo.", "Apareix amb un signe d'exclamació al gestor de dispositius."]),
        ("La imatge és fosca o borrosa", ["La imatge surt molt fosca i amb soroll fins i tot amb bona llum.", "L'autofocus no s'ajusta i la imatge es veu desenfocada."]),
    ],
    "Auriculars": [
        ("Només sona per un costat", ["L'auricular esquerre no emet so i el dret funciona bé.", "El so es talla en moure el cable i té un mal contacte."]),
        ("El micròfon no funciona", ["Els interlocutors no senten la veu a les videotrucades.", "El micròfon es detecta però el nivell d'entrada és gairebé nul."]),
    ],
    "Router": [
        ("Sense connexió a internet", ["Totes les persones de la planta es queden sense internet des d'aquest matí.", "El LED WAN és vermell i no assigna adreces per DHCP."]),
        ("Connexió inestable", ["La connexió cau cada pocs minuts i hi ha pèrdua de paquets.", "El Wi-Fi té poca cobertura al final del passadís."]),
    ],
    "Switch de xarxa": [
        ("Ports sense activitat", ["Diversos ports no mostren llum i els equips connectats no tenen xarxa.", "Alguns ports van a 10 Mbps en lloc de 1 Gbps."]),
        ("Switch es reinicia", ["Es reinicia de manera intermitent i talla la xarxa unes quantes vegades al dia.", "El ventilador fa soroll i l'aparell s'escalfa de manera excessiva."]),
    ],
    "Servidor": [
        ("Servidor no respon", ["Els serveis de fitxers són inaccessibles i no respon al ping.", "L'accés remot no funciona i els usuaris no poden obrir sessió."]),
        ("Alerta de disc", ["El sistema avisa que un dels discos del RAID és degradat.", "L'espai lliure és inferior al 5 % i les còpies de seguretat han fallat."]),
        ("Temperatura alta", ["La sala és calenta i el servidor registra alertes tèrmiques.", "Els ventiladors van a màxima velocitat i l'aparell es reinicia."]),
    ],
}

CONTEXTOS = [
    "Passa des de fa uns dies.", "Va començar aquest matí.", "Ho ha notat un company.",
    "Ha passat just després d'un tall de llum.", "Va passar durant una classe.",
    "S'ha intentat reiniciar sense èxit.", "Cal revisar-ho amb urgència.",
    "Afecta el treball de tot el grup.", "No és la primera vegada que ho detecto.",
    "Es pot reproduir de forma consistent.", "Succeeix de manera intermitent.",
    "Va començar després d'una actualització.", "Ningú ha tocat la configuració.",
    "Ho vaig comunicar verbalment però no s'ha resolt.", "Cal una solució abans de demà.",
]

PREFIXOS_CODI = ["EQ", "INV", "ACT", "TIC", "IT", "ED"]

# Pesos per fer les dades més realistes
RECURRENT_OPCIONS = [("Sí", 3), ("No", 5), ("No ho sé", 2)]
URGENCIA_OPCIONS = [("1", 4), ("2", 4), ("3", 2)]


# ----------------------------- GENERADORS ---------------------------------
def pesat(opcions):
    valors, pesos = zip(*opcions)
    return random.choices(valors, weights=pesos, k=1)[0]


def nom_complet():
    return f"{random.choice(NOMS)} {random.choice(COGNOMS)} {random.choice(COGNOMS)}"


def data_hora_aleatoria():
    ara = datetime.now()
    delta = timedelta(
        days=random.randint(0, DIES_ENRERE - 1),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    dt = ara - delta
    # Concentrar-ho en horari lectiu/laboral la majoria de vegades
    if random.random() < 0.85:
        dt = dt.replace(hour=random.randint(8, 18), minute=random.randint(0, 59))
    return dt


def codi_equip():
    pref = random.choice(PREFIXOS_CODI)
    estil = random.choice(["any", "num", "mixt"])
    if estil == "any":
        return f"{pref}-{random.randint(2019, 2026)}-{random.randint(1, 999):03d}"
    if estil == "num":
        return f"{pref}-{random.randint(1000, 99999)}"
    lletres = "".join(random.choices(string.ascii_uppercase, k=2))
    return f"{pref}-{lletres}{random.randint(100, 9999)}"


def generar_incidencia():
    tipus = random.choice(list(EQUIPS.keys()))
    model = random.choice(EQUIPS[tipus])
    resum, detalls = random.choice(PROBLEMES[tipus])
    descripcio = f"{random.choice(detalls)} {random.choice(CONTEXTOS)}"
    reportant = nom_complet()
    afectat = nom_complet() if random.random() < 0.7 else reportant

    # Generació de correu dinàmic
    nom_net = reportant.lower().replace(" ", ".").replace("ç", "c")
    domini = random.choice(["itb.cat", "gmail.com", "outlook.com", "hotmail.com"])
    correu = f"{nom_net}@{domini}"

    return {
        "reportant": reportant,
        "afectat": afectat,
        "correu": correu,                # <--- Nou camp
        "ubicacio": random.choice(UBICACIONS),
        "datetime": data_hora_aleatoria(),
        "tipus_equip": tipus,
        "marca_model": model,
        "codi": codi_equip(),
        "resum": resum,
        "descripcio": descripcio,
        "recurrent": pesat(RECURRENT_OPCIONS),
        "urgencia": pesat(URGENCIA_OPCIONS),
    }


def construir_payload(inc):
    dt = inc["datetime"]
    e = ENTRY_IDS
    return {
        e["reportant"]: inc["reportant"],
        e["afectat"]: inc["afectat"],
        e["correu"]: inc["correu"],      # <--- Envia el correu al seu entry.XXXXX
        e["ubicacio"]: inc["ubicacio"],
        f"{e['data']}_year": dt.year,
        f"{e['data']}_month": dt.month,
        f"{e['data']}_day": dt.day,
        f"{e['hora']}_hour": f"{dt.hour:02d}",
        f"{e['hora']}_minute": f"{dt.minute:02d}",
        e["tipus_equip"]: inc["tipus_equip"],
        e["marca_model"]: inc["marca_model"],
        e["codi"]: inc["codi"],
        e["resum"]: inc["resum"],
        e["descripcio"]: inc["descripcio"],
        e["recurrent"]: inc["recurrent"],
        e["urgencia"]: inc["urgencia"],
        "fvv": "1",
        "pageHistory": "0",
    }


# ------------------------------- MAIN -------------------------------------
def main():
    if "XXXXXXXX" in FORM_URL or any("1111111111" in v for v in ENTRY_IDS.values()):
        print("⚠️  Configura FORM_URL i ENTRY_IDS a l'inici del fitxer abans d'executar.")
        sys.exit(1)

    total = NUM_INCIDENCIES
    sessio = requests.Session()
    sessio.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    })

    ok, errors = 0, 0
    vistes = set()

    for i in range(1, total + 1):
        # Evitar duplicats exactes
        for _ in range(10):
            inc = generar_incidencia()
            clau = (inc["reportant"], inc["codi"], inc["descripcio"], inc["datetime"])
            if clau not in vistes:
                vistes.add(clau)
                break

        try:
            resp = sessio.post(FORM_URL, data=construir_payload(inc), timeout=TIMEOUT)
            if resp.status_code == 200:
                ok += 1
                print(f"[{i}/{total}] Incidencia enviada correctamente")
            else:
                errors += 1
                print(f"[{i}/{total}] ERROR HTTP {resp.status_code}")
        except requests.exceptions.RequestException as exc:
            errors += 1
            print(f"[{i}/{total}] ERROR de connexió: {exc}")

        time.sleep(PAUSA_SEGONS)

    print(f"\nFinalitzat: {ok} correctes, {errors} amb error, de {total}.")


if __name__ == "__main__":
    main()
