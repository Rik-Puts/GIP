#Made by Rik Puts
#De poort 5050 kan je beneden aanpassen, maar er draait al een apache server op poort 80.
#voor de ledstrip library te krijgen doe: sudo pip install rpi_ws281x
import RPi.GPIO as GPIO
from rpi_ws281x import *	#Gebruik sudo.
from RPLCD.gpio import CharLCD		#De lcd library.
import spidev						#Voor gewoon SPI te kunnen sturen, om mijn MCP3008 in te lezen.
import atexit #Om een functie te doorlopen wanneer de server afsluit
from flask import Flask, render_template, request	#Voor flask, mogelijk moet er meer voor uitbereiding.
import time
from random import randint			#Voor random getallen.
import _thread as thread	#Voor multithreading
import MFRC522						#De RFID library
from colorsys import hls_to_rgb	#Om van HLS waardes naar RGB waardes te gaan, dit is goed voor regenboog effecten.
import math
import pymysql	#Voor database connectie


#Het ip adres wordt statisch verkregen
#De template folder (default templates, meestal gebruikt voor html enzo) veranderen we in www
#De static folder (default static, meestal gebruikt voor CSS enzo) veranderen we in www
app = Flask(__name__, static_url_path='', static_folder='www', template_folder='www')
#Als de host (ip van je raspberry pi) opgevraagd wordt op de root directory ('/') 
#dan gaan we de functie "index" uitvoeren
#functie "index"

#https://github.com/jgarff/rpi_ws281x/blob/master/python/neopixel.py

#LED strip configuration:
LED_COUNT = 256			# Number of LED pixels.
LED_PIN = 18			# GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN = 10			# GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000	# LED signal frequency in hertz (usually 800khz)
LED_DMA = 10			# DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 20		# Set to 0 for darkest and 255 for brightest
LED_INVERT = False		# True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0			# set to '1' for GPIOs 13, 19, 41, 45 or 53
#GPIO
BUTTON_UP = 6
BUTTON_LEFT = 13
BUTTON_RIGHT = 19
BUTTON_DOWN = 26
BUTTON_MID = 5
GPIO.setmode(GPIO.BCM)	#De pins "aanzetten".
GPIO.setup(BUTTON_UP, GPIO.IN)	#GPIO pin instellen als input.
GPIO.setup(BUTTON_LEFT, GPIO.IN)
GPIO.setup(BUTTON_RIGHT, GPIO.IN)
GPIO.setup(BUTTON_DOWN, GPIO.IN)
GPIO.setup(BUTTON_MID, GPIO.IN)
#CharLCD
lcd = CharLCD(cols=16, rows=2 ,pin_rs=27, pin_e=14, pins_data=[12, 16, 20, 21], numbering_mode=GPIO.BCM)
#Aansluiten: CharLCD((cols=16,rows=2 geen pins),pin_rs=[RS],pin_e=[E],pins_data=[ [D4],[D5],[D6],[D7] ]) (andere D pins laat je zweven.) tussen de [] staan de poorten van het lcd.
#Steek de VSS, RW en K moeten in GND, De VDD en de A in 5V, en de VO via 2200 ohm naar de GND.

#Database connectie
conn = pymysql.connect(host='127.0.0.1',port=3306,user='Rik',passwd='Puts',db='GIP',autocommit=True) #Connectie database
cur = conn.cursor()

#MCP3008 SPI
spi = spidev.SpiDev()
spi.open(0, 1) #SPI bus openen (tweede getal is welke cs, 0 -> GPIO8, 1 -> GPIO7) (Dus omdat ik al een RC522 op GPIO8 heb gebruik ik hier GPIO7.)
spi.max_speed_hz = 5000 #Max speed instellen
Joystick = [512, 512]	#X, Y

#Andere globale variablen
slen = 16	#de lengte van de zijde van het led scherm (side length)
background_color = Color(50, 0, 0)
wie = "Speler"	#Deze text verschijnt als er geen badge gescanned wordt.
wieId = 0
game_active = False

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()	#Initializeer library, moet 1 keer gecalled worden voor andere functies gecalled kunnen worden.


#Globale functies
def convert(get):		#De oneven rijen omdraaien.
	if get // slen % 2:	#Kijken of de rij oneven is.
		rijen = get // slen
		rijpos = get % slen
		get = rijen * slen + slen - rijpos - 1
		return get
	else:				#else hoeft niet door return, maar voor de zekerheid...
		return get

def convertPos(xPos, yPos):	#X,Y omzetten naar enkel X. (Eig gwn lange ledstrip.)
	waarde = yPos * slen + xPos
	waarde = convert(waarde)
	return waarde

def background():
	for x in range(0, LED_COUNT):
		strip.setPixelColor(x, background_color)

def aftellen():
	#De cijfers nemen 4 bij 7 pixels in.
	baseX = (slen - 4) // 2
	baseY = (slen - 7) // 2 + 1
	kleur = Color(0, 20, 255)

	def clearMiddle():	#Deze functie bestaat alleen binnen de scope van zijn parent functie.
		for x in range(0, 4):
			for y in range(0, 7):
				strip.setPixelColor(convertPos(baseX + x, baseY + y), background_color)

	#Drie
	clearMiddle()
	for i in range(0, 3):													#3 streepjes in het midden.
		strip.setPixelColor(convertPos(baseX + 1, baseY + i * 3), kleur)
		strip.setPixelColor(convertPos(baseX + 2, baseY + i * 3), kleur)
	strip.setPixelColor(convertPos(baseX + 3, baseY + 5), kleur)
	strip.setPixelColor(convertPos(baseX + 3, baseY + 4), kleur)
	strip.setPixelColor(convertPos(baseX + 3, baseY + 2), kleur)
	strip.setPixelColor(convertPos(baseX + 3, baseY + 1), kleur)
	strip.setPixelColor(convertPos(baseX, baseY + 1), kleur)
	strip.setPixelColor(convertPos(baseX, baseY + 5), kleur)
	strip.show()
	time.sleep(1)

	#Twee
	clearMiddle()
	for i in range(0, 4):
		strip.setPixelColor(convertPos(baseX + i, baseY), kleur)			#Onderste streep
		strip.setPixelColor(convertPos(baseX + i, baseY + 1 + i), kleur)	#Schuine streep
	strip.setPixelColor(convertPos(baseX + 3, baseY + 5), kleur)
	strip.setPixelColor(convertPos(baseX + 2, baseY + 6), kleur)
	strip.setPixelColor(convertPos(baseX + 1, baseY + 6), kleur)
	strip.setPixelColor(convertPos(baseX, baseY + 5), kleur)
	strip.show()
	time.sleep(1)


	#Een
	clearMiddle()
	for i in range(0, 7):
		strip.setPixelColor(convertPos(baseX + 3, baseY + i), kleur)
	strip.setPixelColor(convertPos(baseX + 2, baseY + 5), kleur)
	strip.setPixelColor(convertPos(baseX + 1, baseY + 4), kleur)
	strip.show()
	time.sleep(1)

def lezen():
	global wie
	global wieId
	lezen = True
	MIFAREReader = MFRC522.MFRC522()
	#Aansluitingen:
	#RFIDchip			:			raspberry pi
	#SDA				:			GPIO8
	#SCK				:			GPIO11
	#MOSI				:			GPIO10
	#MISO				:			GPIO9
	#IRQ				:			(niks, gwn laten zweven)
	#GND				:			GND
	#RST				:			GPIO25
	#3.3V				:			3.3V
	while lezen:
		#Scannen voor kaarten.
		(status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

		#De UID van de kaart lezen.
		(status, uid) = MIFAREReader.MFRC522_Anticoll()

		if status == MIFAREReader.MI_OK:	#Als we een kaart hebben.
			lezen = False
			print("UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))	#Print UID

			#kaart opslaan
			wie = str(uid[0]) + str(uid[1]) + str(uid[2]) + str(uid[3])
			wieId = wie
			print(wie)

			# cur.execute("INSERT INTO tblLogin(Id,UID,Naam,Tijd,Duur) VALUES (%s,%s,%s,%s,%s)",(wieId,"FlappyBird",flappy.score,time.strftime("%H:%M:%S"),game_duur))
			# print("Uploading -> FlappyBird -> score:" + str(flappy.score) + " Tijd:" + time.strftime("%H:%M:%S") + " Duur:" + str(game_duur) + " SpelerId: " + str(wie))
			cur.execute("SELECT Naam FROM tblLogin WHERE UID='%s'" % (wie))
			result = str(cur.fetchone())

			if result == "None":
				print("uid: " + wie + "      -> Bezoeker (Niet gekend)")
				wie = "Bezoeker"
			else:
				#De eerste 2 en de laatste 3 karakters moeten weg, dit doe ik in volgende for loop.
				wie = ""
				for i in range(len(result) - 5):
					wie = wie + result[i + 2]
				print("Login Result: " + str(wie))

def joystick():
	global Joystick
	#MCP3008scannen
	for ch in range(2): #ch is 0 en 1 voor de eerste 2 channels van mijn MCP3008
		result = spi.xfer2([1, (8 + ch) << 4, 0])			#zie scriptie
		Joystick[ch] = (((result[1] & 3) << 8) + result[2])	#zie scriptie

#Games
def game_Flappybird(doAI = False):	#Standaard dus als er niks word meegegeven False
	global background_color
	global wie					#Moet global zijn omdat ik hem op het einde aanpas naar speler voor als de volgende speler zich niet aanmeldt.
	game_active = True
	background_color = Color(50, 0, 0)
	game_duur = time.time()
	#AI variablen
	voorsteWall = 0		#De wall waar de AI op moet focussen

	class FlappyBird:
		#bijna hetzelfde als static variables van C++. (Behoren tot "wall", dus niet tot een object van wall. dus wall.width werkt, wall1.width verwijst naar wall.width)
		color = Color(0, 100, 255)

		def __init__(self):			#__init__ is zoals de contructor in C++
			self.x = 2				#3 van kant (begin met 0)
			self.y = slen // 2 + 1	#hoogte / 2
			self.score = 0
			self.vel = 0			#velocity (snelheid)
			self.jump = False
			self.alive = True	#Wordt 1 als flappy dood gaat
			self.levens = 3
			self.color = FlappyBird.color
			self.Iteller = 0		#invincibility teller, voor als je dood gaat

		def update(self):
			#Velocity update
			if self.jump == 1:
				self.jump = False
				self.vel = 2
			elif self.vel >= 0:	#Zo gaat hij tem -1
				self.vel -= 1
			#Position update
			self.y += self.vel
			if self.y < 0:
				self.y = 0
			elif self.y >= slen:
				self.y = slen - 1	#0 tem (slen - 1)
			#Death check
			if strip.getPixelColor(convertPos(self.x, self.y)) != background_color and flappy.alive == True:
				self.alive = False
				self.levens -= 1
				# thread.start_new_thread(sound,(3,))
				print("Levens: " + str(self.levens))
			#In scherm-array zetten
			if not self.alive:
				self.Iteller += 1
				if self.Iteller % 4 <= 2:	#Om de 2 keer veranderen van dood kleur
					self.color = Color(130, 25, 25)
				else:
					self.color = Color(255, 28, 230)
				if self.Iteller >= 10:
					self.Iteller = 0
					self.alive = True
					self.color = FlappyBird.color
			strip.setPixelColor(convertPos(self.x, self.y), self.color)

	class wall:
		#bijna hetzelfde als static variables van C++. (Behoren tot "wall", dus niet tot een object van wall. dus wall.width werkt, wall1.width verwijst naar wall.width)
		totaant = 3		#Hoeveel wall-objecten er in totaal zijn.
		num = 0			#Voor te kijken het hoeveelste wall-object het is bij de init functie.
		width = 3		#De breedte van elke wall (Op deze manier makkelijk aanpasbaar)
		opening = 4
		min_spacing = opening + 1	#De minimum spacing tussen een doorgang en de boven/onderkant. (moet minstens de opening + 1 zijn)
		extra_plek = (slen + width) % totaant	#Als de verdeling van de pixels niet uitkomt moet de (denkbeeldige) breedte groter worden zodat de muren toch even ver uiteen staan.
		color = Color(0, 100, 20)
		beweging = False			#Bewegende muren

		def __init__(self):		#__init__ is zoals de contructor in C++
			wall.num += 1
			self.y = randint(wall.min_spacing - 1, slen - wall.min_spacing - wall.opening)
			self.x = wall.num * (slen + wall.width + 1) // wall.totaant
			self.richting = pow(-1, wall.num)			#Voor bewegende muren, 1 is naar boven, -1 naar beneden.
			self.bewegingTeller = 0			#Voor de muren maar om de x frames te laten bewegen		

		def update(self):
			self.x -= 1
			if self.x < -wall.width:	#Als de muur met zijn hele breedte voorbij het schermm is, wordt hij naar de andere kant verplaatst met een nieuwe opening-hoogte.
				self.x = slen + wall.extra_plek
				self.y = randint(wall.min_spacing - 1, slen - wall.min_spacing - wall.opening)
			#Temp variablen
			if self.x + wall.width >= slen:				#Voor als de muur een stukje voorbij het scherm steekt. (De muur smaller maken zodat hij past.)
				tempWallEnd = slen
			else:
				tempWallEnd = self.x + wall.width

			if self.x < 0:								#Voor als de muur een stukje voor het scherm steekt. (De muur smaller maken zodat hij past.)
				tempX = 0
			else:
				tempX = self.x
			#Muur beweging
			if wall.beweging:
				self.bewegingTeller += 1
				if self.bewegingTeller >= 3:
					self.bewegingTeller = 0
					self.y += self.richting
					if self.y < 0 or self.y > slen - wall.opening:
						self.richting *= -1
						self.y += self.richting * 2
			#Flappy Score
			if flappy.x == self.x:
				flappy.score += 1
				print("Score: " + str(flappy.score))
				# thread.start_new_thread(sound,(2,))
				#LCD score updaten
				lcd.clear()	#Lcd clearen
				lcd.cursor_pos = (0, 0)		#Naam erop zetten.
				lcd.write_string(wie)		#Naam erop zetten.
				for i in range(0, flappy.levens):		#Levens erop zetten.
					lcd.cursor_pos = (0, 11 + i)	#Op de juiste plek zetten. (max levens is 4 en het gaat tot tabel 15 dus 15 - 3 + i).
					lcd.write_string(chr(0))		#Zet er een hartje, maar als je minder levens hebt komen er dus minder hartjes.
				lcd.cursor_pos = (1, 0)							#Score erop zetten.
				lcd.write_string("Score: " + str(flappy.score))	#Score erop zetten.
				lcd.cursor_pos = (1, 11)
				#lcd.write_string("HS:" + str(0))		#High score erop zetten
			#in scherm-array zetten
			for wx in range(tempX, tempWallEnd):
				for wy in range(0, self.y):								#Onderste deel
					strip.setPixelColor(convertPos(wx, wy), wall.color)
				for wy in range(self.y + wall.opening, slen):			#Bovenste deel
					strip.setPixelColor(convertPos(wx, wy), wall.color)

	def inputs():
		while flappy.levens > 0:
			if GPIO.input(BUTTON_UP) or GPIO.input(BUTTON_MID):
				flappy.jump = True
				# thread.start_new_thread(sound,(1,))
				while GPIO.input(BUTTON_UP) or GPIO.input(BUTTON_MID):
					time.sleep(0.05)
			time.sleep(0.05)

	#Objecten initialiseren
	flappy = FlappyBird()
	if not doAI:
		thread.start_new_thread(inputs,())	#Moet na initialiseren van flappy.
	walls = [wall() for i in range(wall.totaant)]	#Zet wall.totaant (3) keer een object van de class wall in de list walls
	# for i in range(0, wall.totaant):
	# 	walls[i].append(i * 3)

	#Andere variablen initialiseren
	frameStart = 0.0
	frameStop = 0.0
	frameProcessDuration = 0.0
	frameDuration = 0.17

	#Begin aftellen
	background()
	for i in range(wall.totaant):
		walls[i].update()
	flappy.update()		#Moet na de muren, anders werkt dood check niet.

	#De lcd regelen
	lcd.clear()		#De lcd leeg maken.
	#Een eigen character maken. (Het hartje van de levens.)
	lcd.create_char(0, 
		(
			0b00000,
			0b01010,
			0b10101,
			0b10001,
			0b10001,
			0b01010,
			0b00100,
			0b00000
		)
	)
	#lezen()
	#Verwelkomen
	lcd.clear()
	lcd.cursor_pos = (0, 0)
	if not doAI:
		lcd.write_string("Hey " + wie + '!')
		lcd.cursor_pos = (1, 0)
		lcd.write_string("Flappy Bird")
	else:
		lcd.write_string("AI playing")
		lcd.cursor_pos = (1, 0)
		lcd.write_string("Flappy Bird")
		wie = "AI"
	time.sleep(2)

	aftellen()

	while flappy.levens > 0:
		frameStart = time.time()
		background()
		for i in range(0, wall.totaant):
			walls[i].update()
		flappy.update()		#Moet na de muren, anders werkt dood check niet.
		strip.show()
		if doAI:	#De berekeningen van de AI
			if walls[voorsteWall].x + wall.width - 2 < flappy.x:	#Kijken of de voorste wall verandert is. (-2 omdat: 1 omdat je het er bij op telt, en nog 1 omdat je bij de laatste pixel geen rekening meer moet houden met een wall.)
				voorsteWall += 1
				if voorsteWall >= wall.totaant:	#Kijken of de volgende wall terug de eerste moet zijn, >= omdat we van 0 beginnen te tellen.
					voorsteWall = 0
			elif flappy.y - 1 <= walls[voorsteWall].y - 1:		#Kijken of flappy volgende frame lager dan de voorste zou kunnen wall zijn y gaat zijn als hij niet springt. (-1 bij flappy: minimum velocity van flappy is -1. -1 bij y: for loop gaat tot. (niet tem))
				flappy.jump = True
		framestop = time.time()
		if (frameProcessDuration > frameDuration):
			print("Ik kan niet volgen, ik loop " + str(frameProcessDuration - frameDuration) + "s achter.")
		else:
			time.sleep(frameDuration - frameProcessDuration)

	#Lcd Death screen
	lcd.clear()
	lcd.cursor_pos = (0, 0)
	lcd.write_string("Aaahh, you died.")
	lcd.cursor_pos = (1, 0)
	lcd.write_string("Final score:" + str(flappy.score))

	#Blinking flappy
	for i in range(0, 3):
		time.sleep(0.2)
		strip.setPixelColor(convertPos(flappy.x, flappy.y), wall.color)
		strip.show()
		time.sleep(0.2)
		strip.setPixelColor(convertPos(flappy.x, flappy.y), flappy.color)
		strip.show()
	time.sleep(1)

	# while True:
	# 	strip.setPixelColor(randint(0, LED_COUNT - 1), Color(randint(0, 201), randint(0, 201), randint(0, 201)))
	# 	strip.show()
	for i in range(0, LED_COUNT):	#(Scherm) Alles op nul zetten.
		strip.setPixelColor(i, 0)
	strip.show()

	wie = 0 #Temp

	game_duur = int(game_duur - time.time())
	cur.execute("INSERT INTO tblScores(SpelerId,Spel,Score,Tijd,Duur) VALUES (%s,%s,%s,%s,%s)",(wieId,"FlappyBird",flappy.score,time.strftime("%H:%M:%S"),game_duur))
	print("Uploading -> FlappyBird -> score:" + str(flappy.score) + " Tijd:" + time.strftime("%H:%M:%S") + " Duur:" + str(game_duur) + " SpelerId: " + str(wie))
	wie = "Speler"
	game_active = False
	return flappy.score

def game_Snake(doAI = False):
	global background_color
	global button_direction		#Moet global zijn want anders kan ik in de functie "inputs" de waarde van deze variable van deze functie niet aanpassen. Maar ik delete hem op het einde van deze functie.
	global wie					#Moet global zijn omdat ik hem op het einde aanpas naar speler voor als de volgende speler zich niet aanmeldt.
	game_active = True
	background_color = Color(20, 20, 20)
	button_direction = 3	#De eerste richting moet naar beneden zijn.
	game_duur = time.time()
	#Voor de gemakkelijkheid heb ik de richtingen namen gegeven.
	LEFT = 0
	RIGHT = 1
	UP = 2
	DOWN = 3
	#AI variablen
	cycle = [[0, 0, 0] for i in range(LED_COUNT)]	#LED_COUNT moet hier exact zijn. Het eerste getal is de stap, en het tweede x of y of richting, 0 is x, 1 is y, 2 is richting.
	#AI: cycle: Zig-Zag patroon, simpelste patroon. (Voor debugging)
	for y in range(slen):	#Ik laat geen kolom over om terug aan te sluiten aangezien je op het einde naar boven kan gaan en dan kom je terug beneden uit.
		for x in range(slen):
			s = y * slen + x
			if y % 2 == 0:
				s = y * slen + x
				cycle[s][0] = x
				cycle[s][2] = RIGHT
			else:
				s = y * slen + slen - 1 - x
				cycle[s][0] = slen - 1 - x
				cycle[s][2] = LEFT
			cycle[s][1] = y
		cycle[s][2] = UP
	del s

	#Test
	# for i in range(LED_COUNT):
	# 	if cycle[i][2] == 0:
	# 		testKleur = Color(0, 100, 0)
	# 	elif cycle[i][2] == 1:
	# 		testKleur = Color(0, 0, 100)
	# 	else:
	# 		testKleur = Color(100, 0, 0)
	# 	strip.setPixelColor(convertPos(cycle[i][0], cycle[i][1]), testKleur)
	# strip.show()
	# time.sleep(5)

	#Ai: cycle: vind het stapnr dat bij een positie hoort.
	def findStep(x, y):
		pos = 0
		while not (cycle[pos][0] == x and cycle[pos][1] == y) and pos <= LED_COUNT:
			pos += 1
		if pos > LED_COUNT:
			print("Error: pos niet gevonden.")
		return pos

	def inputs():
		global button_direction
		while player.alive:
			#De reden dat we direction eerst nog in een tussen variable zetten ipv direct in player.direction is zodat je niet 2 keer per frame kan veranderen van richting.
			if GPIO.input(BUTTON_UP) and player.direction != DOWN:	#Je mag niet terug in jezelf gaan, dus je kan niet in de tegenovergestelde richting gaan.
				button_direction = UP
				while GPIO.input(BUTTON_UP):
					time.sleep(0.05)
			elif (GPIO.input(BUTTON_DOWN) or GPIO.input(BUTTON_MID)) and player.direction != UP:
				button_direction = DOWN
				while GPIO.input(BUTTON_DOWN):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_LEFT) and player.direction != RIGHT:
				button_direction = LEFT
				while GPIO.input(BUTTON_LEFT):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_RIGHT) and player.direction != LEFT:
				button_direction = RIGHT
				while GPIO.input(BUTTON_RIGHT):
					time.sleep(0.05)
			time.sleep(0.05)

	class Snake:
		#Notes: 1) Bij het verplaatsten van de body snake delen, doe het ook voor het deel dat verdwijnt (dus 1 meer) voor stel dat snake een fruitje eet en 1 langer wordt. (Begin bij de staart.)
		#		2) Aangezien fruitjes zo gemaakt gaan zijn dat ze niet kunnen spawnen in een snake onderdeel, kan het nooit zijn dat je om de reden hiervoor ongedetecteerd in je staart botst.
		#		3) Omdat er geen andere grote objecten zijn (alleen candy maar die is 1px groot), heb ik alles (zelfs background) bij in de Snake class gestoken.
		color = Color(0, 255, 0)
		candyColor = Color(200, 200, 0)
		def __init__(self):
			self.direction = DOWN		#De =Down is overbodig aangezien hij toch overschreven wordt door de update functie, maar voor het overzicht laat ik hem staan.
			#Body van de snake, [hoeveelste onderdeel][0 -> x, 1 -> y]. (dus body[0][0] is de x van het hoofd, en body [0][1] is de y van het hoofd.)
			self.score = 2	#De score is de lengte van de snake, je begint al met score 2 omdat het toch onmogelijk is om met score 2 dood te gaan.
			self.body = [[25 for i in range(2)] for j in range(LED_COUNT + 1)]	#Maakt een list (python array), met daarin LED_COUNT lists van 2 items. (2D array dus.) (LED_COUNT + 1 omdat we altijd een backup willen maken van het laatste staart deel.)
			#Hoofd een positie geven
			self.body[0][0] = int(slen // 2)
			self.body[0][1] = int(slen // 2)
			#Eerste staart deel een positie juist boven het hoofd geven.
			self.body[1][0] = int(slen // 2)
			self.body[1][1] = int(slen // 2 + 1)
			#Het snoepje dat je moet pakken maken. [x, y] (1D array)
			self.candy = [slen // 2, 4]	#Als je niks aanraakt loop je hier vanzelf in.
			#In leven?
			self.alive = True

		def update(self):
			if not doAI:
				self.direction = button_direction	#richting updaten
			#Body verschuiven (van achter naar voor)
			for i in range(self.score, 0, -1):		#-1 omdat we aftellen, 0 (en niet -1) omdat we het hoofd geen waarde geven, en score (ipv 'score + 1' omdat we beginnen bij het deel van de staart dat verdwijnt, maar we houden het bij in de array.)
				self.body[i][0] = self.body[i - 1][0]
				self.body[i][1] = self.body[i - 1][1]
			#Hoofd verplaatsen
			if self.direction == LEFT:
				self.body[0][0] -= 1
			elif self.direction == RIGHT:
				self.body[0][0] += 1
			elif self.direction == UP:
				self.body[0][1] += 1
			elif self.direction == DOWN:
				self.body[0][1] -= 1
			#Over de rand check. (Je teleporteerd naar de andere kant.)
			if self.body[0][0] < 0:
				self.body[0][0] = slen - 1
			elif self.body[0][0] >= slen:
				self.body[0][0] = 0
			elif self.body[0][1] < 0:
				self.body[0][1] = slen - 1
			elif self.body[0][1] >= slen:
				self.body[0][1] = 0
			#Death check
			for i in range(1, self.score):	#1 ipv 0 omdat body[0] altijd gelijk is aan zichzelf...
				if self.body[0][0] == self.body[i][0] and self.body[0][1] == self.body[i][1]:
					self.alive = False	#Dit zet de loop stop
					print("You died, score: " + str(self.score))
					#Laten zien waar je dood ging
					background()
					for i in range(1, self.score):	#Ik skip hier het hoofd
						strip.setPixelColor(convertPos(self.body[i][0], self.body[i][1]), Snake.color)
					strip.setPixelColor(convertPos(self.candy[0], self.candy[1]), Snake.candyColor)
					strip.setPixelColor(convertPos(self.body[0][0], self.body[0][1]), Color(255, 0, 0))
					strip.show()
					time.sleep(1.5)
					return 0	#Zodat hij er niet nog met groen overtekent. (Dit sprint uit de functie.)
			#Candy check
			if self.body[0][0] == self.candy[0] and self.body[0][1] == self.candy[1]:
				self.score += 1
				#Candy een nieuwe plek geven die nog niet bezet is door snake (Of de vorige candy, maar die is op dit moment gelijk aan het hoofd van de snake.)
				clear = False
				while clear == False:	#Dit kan eventjes duren, zet eventueel in een andere thread.
					self.candy = [randint(0, slen - 1), randint(0, slen - 1)]
					clear = True
					for i in range(0, self.score):
						if self.candy[0] == self.body[i][0] and self.candy[1] == self.body[i][1]:
							clear = False
				#LCD score updaten
				lcd.clear()	#Lcd clearen
				lcd.cursor_pos = (0, 0)		#Naam erop zetten.
				lcd.write_string(wie)		#Naam erop zetten.
				lcd.cursor_pos = (1, 0)							#Score erop zetten.
				lcd.write_string("Score: " + str(self.score))	#Score erop zetten.
				lcd.cursor_pos = (1, 11)
				#lcd.write_string("HS:" + str(0))		#High score erop zetten
				# #Eerste candy clear check# while strip.getPixelColor(self.candy[1] * slen + self.candy[0] - 1) != background_color:		#led nr = y * slen + x - 1.	-1 omdat de strip bij 0 begint te tellen.
				# 	self.candy = [randint(0, slen), randint(0, slen)]
			#Tekenen (Regenboogkleur zodat je onderschijdingen kan maken als 2 lichaamsdelen naast elkaar liggen.)
			background()
			hue = 120	#0 - 360	(Beginnend bij groen op 120° en gaat via blauw naar rood, als je lang genoeg bent.)
			for i in range(0, self.score):
				r, g, b = hls_to_rgb(hue / 360, 0.5, 1)
				Snake.color = Color(int(r * 255), int(g * 255), int(b * 255))
				if hue >= 360:
					hue = 0
				else:
					hue += 1
				strip.setPixelColor(convertPos(self.body[i][0], self.body[i][1]), Snake.color)
			strip.setPixelColor(convertPos(self.candy[0], self.candy[1]), Snake.candyColor)

	#Tijd variablen initialiseren
	frameStart = 0.0
	frameStop = 0.0
	frameProcessDuration = 0.0
	frameDuration = 0.2
	#De rest
	player = Snake()
	if not doAI:
		thread.start_new_thread(inputs,())
	#Verwelkomen
	lcd.clear()
	lcd.cursor_pos = (0, 0)
	lcd.write_string("Hey " + wie + '!')
	lcd.cursor_pos = (1, 0)
	lcd.write_string("Snake")
	#De loop
	while player.alive:
		frameStart = time.time()
		player.update()
		strip.show()
		if doAI:
			#Richting van volgende stap vinden
			currentStep = findStep(player.body[0][0], player.body[0][1])
			candyStep = findStep(player.candy[0], player.candy[1])

			#distance berekenen
			# distance = candyStep - currentStep
			# if distance < 0:
			# 	distance += 256
			# print("distance: " + str(distance))

			print("cStep: ", currentStep)
			# print("Dir: " + str(cycle[currentStep][2]))
			# print("")
			player.direction = cycle[currentStep][2]
		framestop = time.time()
		frameProcessDuration = framestop - frameStart
		if frameProcessDuration > frameDuration:
			if player.alive:	#Als player dood wacht hij 2s dus dat mag hier niet bijgeteld worden.
				print("Ik kan niet volgen, ik loop " + str(frameProcessDuration - frameDuration) + "s achter.")
		else:
			time.sleep(frameDuration - frameProcessDuration)
	for i in range(0, LED_COUNT):	#(Scherm) Alles op nul zetten.
		strip.setPixelColor(i, 0)
	strip.show()

	wie = 0 #Temp

	game_duur = int(game_duur - time.time())
	cur.execute("INSERT INTO tblScores(SpelerId,Spel,Score,Tijd,Duur) VALUES (%s,%s,%s,%s,%s)",(wieId,"Snake",player.score,time.strftime("%H:%M:%S"),game_duur))
	print("Uploading -> Snake -> score:" + str(flappy.score) + " Tijd:" + time.strftime("%H:%M:%S") + " Duur:" + str(game_duur) + " SpelerId: " + str(wie))
	wie = "Speler"
	game_active = False
	del button_direction	#Niet meer nodig
	return player.score

def game_Stacker():
	global background_color
	global wie
	#De volgende twee variablen moeten eigenlijk niet global zijn maar anders kon ik er niet aan vanuit functies. Ik verwijder ze op het einde van de functie.
	global BUTTON
	global frameDuration
	game_active = True
	BUTTON = False
	background_color = Color(0, 50, 50)
	game_duur = time.time()

	class Stacker():
		def __init__(self):
			self.direction = 1				#1 is rechts, -1 is links.
			self.breedte = 4
			self.levend = [True, True, True, True]	#Voor elk deel, of het nog levend is, of al gevallen.
			self.alive = True		#Dit wordt false als alle delen van self.levend False worden, ik wist geen andere naamgevingen.
			self.x = int(slen // 2 - self.breedte // 2)	#De linker kant (Ookal is die al gevallen)
			self.y = 1
			self.red = 0
			self.green = 255
			self.color = Color(self.red, self.green, 0)	#Wordt roder en minder groen hoe hoger je komt.
			self.colorConst = int(255 // slen - 1)	#Hoeveel de kleur afneemt en stijgt (groen, rood) bij elke y-waarde, slen - 1 omdat de basis er al is.
			self.win = False				#Wordt True als hij gewonnen is.
			self.lcorrectie = 0				#Als de linker delen dood gaan stuitert hij te vroeg, omdat de onzichtbare delen al raken. Dit is de correctie daarvoor.
			#De basis zetten
			for i in range(6, 10):
				strip.setPixelColor(i, self.color)	#convertPos hoeft hier niet omdat het de onderste rij is.

		def update(self):
			global BUTTON
			global frameDuration
			if BUTTON:
				BUTTON = False
				#Kijken welke delen levend zijn
				for i in range(self.lcorrectie, self.breedte):	#vertrek van lcorrectie omdat alles links daarvan al dood is en er nu dus enkel nieuwe dode delen zullen gevonden worden, en dan kan ik rechtstreeks de functie zakken eronder zetten.
					if strip.getPixelColor(convertPos(self.x + i, self.y - 1)) == background_color:		#Kijken of de kleur onder pixel i de achtergrond kleur is.
						self.levend[i] = False
						thread.start_new_thread(zakken,(self.x + i, self.y, self.color))
				#Het het gedeelte dat nu achtergelaten wordt er juist in zetten voor self.y 1 hoger wordt.
				for i in range(0, slen):
					strip.setPixelColor(convertPos(i, self.y), background_color)
				for i in range(0, self.breedte):
					if self.levend[i]:
						strip.setPixelColor(convertPos(self.x + i, self.y), self.color)
				#Kijken of hij volledig dood is. ("not" maakt van True False, en "and" geeft True als alle waarden True zijn.)
				if True not in self.levend:		#Zelfde als: if not self.levend[0] and not self.levend[1] and not self.levend[2] and not self.levend[3]:
					time.sleep(self.y * 0.2)	#Ervoor zorgen dat de laatste delen nog kunnen vallen.
					self.alive = False
				else:
					self.y += 1
					self.red += self.colorConst
					self.green -= self.colorConst
					self.color = Color(self.red, self.green, 0)
					if self.y % 4 == 0:		#Om de 4 keer. (Als de rest van die deling 0 is.)
						frameDuration = frameDuration / 2
				if self.y >= slen:
					self.win = True
				#Kijken of de breedte kleiner moet worden. (Als de rechtse delen dood zijn moet de breedte kleiner worden, anders stuitert hij te vroeg omdat de onzichtbare delen al raken.)
				while not self.levend[self.breedte - 1] and self.alive:	#Links van "and" kijk telkens of het rechtse deel nog levend is en rechts van "and" voorkom ik dat "self.breedte - 1" ooit kleiner dan 0 kan worden.
					self.breedte -= 1
				#Nu hetzelfde maar dan voor de linker kant, de breedte verminderen gaat niet meer, daarom maakte ik een variable die ik bij self.x optel bij de stuiter detectie om self.x negatief te kunnen laten worden.
				while not self.levend[self.lcorrectie] and self.alive:
					self.lcorrectie += 1
			self.x += self.direction
			if self.x + self.breedte > slen:
				self.direction = -1
				self.x = slen - self.breedte - 1
			elif self.x + self.lcorrectie < 0:
				self.direction = 1
				self.x = 1 - self.lcorrectie
			#Scherm updaten, maar aangezien het spel niet veel beweging heeft hoef ik niet heel het scherm opnieuw te tekenen elke frame.
			for i in range(0, slen):
				strip.setPixelColor(convertPos(i, self.y), background_color)
			for i in range(0, self.breedte):
				if self.levend[i]:
					strip.setPixelColor(convertPos(self.x + i, self.y), self.color)

		def winner(self):
			self.red = 0
			self.green = 255
			self.color = Color(self.red, self.green, 0)
			animation1(Color(0, 255, 0))
			for i in range(0, slen):
				for j in range(0, slen):
					strip.setPixelColor(convertPos(j, i), self.color)
				strip.show()
				self.red += self.colorConst
				self.green -= self.colorConst
				self.color = Color(self.red, self.green, 0)
				time.sleep(0.1)

	def inputs():
		global BUTTON
		while player.alive and not player.win:
			if GPIO.input(BUTTON_UP) or GPIO.input(BUTTON_MID):
				BUTTON = True
				# thread.start_new_thread(sound,(1,))
				while GPIO.input(BUTTON_UP) or GPIO.input(BUTTON_MID):
					time.sleep(0.05)
				time.sleep(frameDuration * 3)	#Bij stacker mag je niet direct opnieuw drukken na een druk.
			time.sleep(0.05)

	def zakken(x, y, color):
		strip.setPixelColor(convertPos(x, y), color)
		strip.show()
		time.sleep(0.2)
		while strip.getPixelColor(convertPos(x, y - 1)) == background_color and y > 0 and player.alive:
			strip.setPixelColor(convertPos(x, y), background_color)
			y -= 1
			print("x: " + str(x) + ", y: " + str(y))
			strip.setPixelColor(convertPos(x, y), color)
			strip.show()
			time.sleep(0.2)

	#Tijd variablen initialiseren
	frameStart = 0.0
	frameStop = 0.0
	frameProcessDuration = 0.0
	frameDuration = 0.2	#Wordt korter hoe hoger de player komt.
	#Voorbereiden
	background()	#Moet voor het initialiseren van stacker en mag niet meer gecalled worden.
	player = Stacker()
	thread.start_new_thread(inputs,())
	#Verwelkomen
	lcd.clear()
	lcd.cursor_pos = (0, 0)
	lcd.write_string("Hey " + wie + '!')
	lcd.cursor_pos = (1, 0)
	lcd.write_string("Stacker")
	while player.alive and not player.win:
		frameStart = time.time()
		player.update()
		strip.show()
		framestop = time.time()
		frameProcessDuration = framestop - frameStart
		if frameProcessDuration > frameDuration:
			if player.alive:	#Als player dood gaat is er extra sleep.
				print("Ik kan niet volgen, ik loop " + str(frameProcessDuration - frameDuration) + "s achter.")
		else:
			time.sleep(frameDuration - frameProcessDuration)
	if player.win:
		player.winner()
	else:
		animation1(Color(255, 0, 0))

	for i in range(0, LED_COUNT):	#(Scherm) Alles op nul zetten.
		strip.setPixelColor(i, 0)
	strip.show()

	game_duur = int(game_duur - time.time())
	cur.execute("INSERT INTO tblScores(SpelerId,Spel,Score,Tijd,Duur) VALUES (%s,%s,%s,%s,%s)",(wieId,"Stacker",player.y**2,time.strftime("%H:%M:%S"),game_duur))
	print("Uploading -> Stacker -> score:" + str(player.y**2) + " Tijd:" + time.strftime("%H:%M:%S") + " Duur:" + str(game_duur) + " SpelerId: " + str(wie))
	wie = "Speler"
	game_active = False
	del BUTTON			#Is global, wordt anders niet gedelete
	del frameDuration	#Is global, wordt anders niet gedelete
	return player.y**2

def animation1(color):
	x = slen // 2
	y = slen // 2
	b = 2	#Breedte
	h = 2	#Hooghte
	for i in range(0, slen // 2):
		for yi in range(y - 1, y + h - 1):
			for xi in range(x - 1, x + b - 1):
				strip.setPixelColor(convertPos(xi, yi), color)
		b += 2
		h += 2
		x -= 1
		y -= 1
		strip.show()
		time.sleep(0.1)

def animation2():	#1 kleur voor heel het scherm, maar de kleur verandert.
	hoek = 0	#Gaat van 0 tot 359, (360 = 0) door het kleurspectrum van HUE. (De eerste letter van HLS)
	kleur = hls_to_rgb(hoek, 0.5, 1)	#Neem de kleur van de hoek, in het midden tussen wit en zwart (0.5), en met 100% saturatie (1), en zet het om naar rgb.
	while True:
		for hoek in range(60):
			print("hoek: " + str(hoek / 360))
			r, g, b = hls_to_rgb(hoek / 60, 0.5, 1)
			print("r: " + str(r) + " g: " + str(b) + " b: " + str(b))
			kleur = Color(int(r * 255), int(g * 255), int(b * 255))
			for i in range(LED_COUNT):
				strip.setPixelColor(i, kleur)
			strip.show()
			time.sleep(0.1)

def animation3(snelheid):	#circel: 1 is van binnen naar buiten, -1 is van buiten naar binnen. Verder van 0 is sneller.
	hue = 0
	midden = slen / 2 - 0.5
	while True:
		for y in range(slen):
			for x in range(slen):
				afstand = math.sqrt((midden - x)**2 + (midden - y)**2)
				if hue + afstand > 60:
					afstand -= 60
				r, g, b = hls_to_rgb((hue + afstand * 6) / 60, 0.5, 1)
				strip.setPixelColor(convertPos(x, y), Color(int(r * 255), int(g * 255), int(b * 255)))
		strip.show()
		hue -= snelheid
		if hue >= 60:
			hue = 0
		time.sleep(0.1)

def game_animatieBesturen():
	global game_active
	global wie
	game_active = True
	hue = 0		#0-60	-->  eig 0-1 maar we delen het nog door 60 omdat for loops alleen met ints werken.
	lightness = [0.5]	#0-1	--> Ik maak er een list van omdat het dan een object is, objecten worden "passed by refference" als je ze meegeeft in een functie, wat betekent dat als ik ze in de functie aanpas, ze buiten de functie ook veranderen.
	saturation = 1	#0-1	-->  wss laat ge da best op 1
	snelheid = [1]	#nie echt limieten maar blijf maar best tussen, -10 en 10.. en niet 0. Ik maak hiervan ook een object zodat ik het kan aanpassen met de functie inputs.
	midden = [7.5, 7.5]	#Voor het midden van de animatie
	#midden = 0.5	#Voor de linker onderhoek
	#midden = 15.5	#Voor de rechter bovenhoek
	game_duur = time.time()

	#LCD
	def updateLCD():
		lcd.clear()
		lcd.cursor_pos = (0, 0)
		lcd.write_string("Helderheid: ")
		lcd.cursor_pos = (0, 12)
		lcd.write_string(str(round(lightness[0], 2)))
		print("Helderheid: ", lightness[0])
		lcd.cursor_pos = (1, 0)
		lcd.write_string("Snelheid: ")
		lcd.cursor_pos = (1, 10)
		lcd.write_string(str(snelheid[0]))
		print("Snelheid: ", snelheid[0])

	def inputs(lightness, snelheid):
		global button_direction
		global game_active
		while game_active:		#Wordt automatisch gestopt wanneer het programma wordt gestopt met een KeyBoardInterrupt (Ctrl + C)
			#De reden dat we direction eerst nog in een tussen variable zetten ipv direct in player.direction is zodat je niet 2 keer per frame kan veranderen van richting.
			if GPIO.input(BUTTON_UP):	#Je mag niet terug in jezelf gaan, dus je kan niet in de tegenovergestelde richting gaan.
				if lightness[0] < 1.1:	#Hij geraakt hier toch nog boven door een verlies van accuratie, maar dat maakt niet uit want de resultaten zijn interresant en leuk.
					lightness[0] += 0.1
				updateLCD()
				while GPIO.input(BUTTON_UP):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_DOWN):
				if lightness[0] > -1:
					lightness[0] -= 0.1
				updateLCD()
				while GPIO.input(BUTTON_DOWN):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_LEFT):
				if snelheid[0] > -10:
					snelheid[0] -= 1
				updateLCD()
				while GPIO.input(BUTTON_LEFT):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_RIGHT):
				if snelheid[0] < 10:
					snelheid[0] += 1
				updateLCD()
				while GPIO.input(BUTTON_RIGHT):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_MID):
				game_active = False
				while GPIO.input(BUTTON_MID):
					time.sleep(0.05)
			time.sleep(0.05)

	thread.start_new_thread(inputs,(lightness, snelheid))
	while game_active:
		joystick()	#Joystick inlezen.
		midden[0] = (1023 - Joystick[0]) / 63.938
		midden[1] = Joystick[1] / 63.938
		for y in range(slen):
			for x in range(slen):
				afstand = math.sqrt((midden[0] - x)**2 + (midden[1] - y)**2)
				if hue + afstand > 60:
					afstand -= 60
				r, g, b = hls_to_rgb((hue + afstand * 6) / 60, lightness[0], saturation)
				strip.setPixelColor(convertPos(x, y), Color(int(r * 255), int(g * 255), int(b * 255)))
		strip.show()
		hue -= snelheid[0]
		if hue >= 60:
			hue = 0
		time.sleep(0.1)
	for i in range(0, LED_COUNT):	#(Scherm) Alles op nul zetten.
		strip.setPixelColor(i, 0)
	strip.show()

	game_duur = int(game_duur - time.time())
	cur.execute("INSERT INTO tblScores(SpelerId,Spel,Score,Tijd,Duur) VALUES (%s,%s,%s,%s,%s)",(wieId,"animatieBesturen",0,time.strftime("%H:%M:%S"),game_duur))
	print("Uploading -> animatieBesturen -> score:" + str(0) + " Tijd:" + time.strftime("%H:%M:%S") + " Duur:" + str(game_duur) + " SpelerId: " + str(wie))
	wie = "Speler"
	game_active = False

def game_Tetris():
	global background_color
	global wie
	global button_direction
	global parts
	game_active = True
	background_color = Color(0, 0, 0)
	side_color = Color(3, 65, 174)
	game_duur = time.time()

	#Voor de gemakkelijkheid heb ik de richtingen namen gegeven.
	LEFT = 0
	RIGHT = 1
	UP = 2
	DOWN = 3
	MID = 4
	NIKS = 5
	button_direction = NIKS		#Voor te beginnen

	#Parts[partnr][rotatie][y][x]	#De parts moeten hun grootte blijfen behouden, voor de rest kan je ze aanpassen. Ook is de absolute max grootte 4, meer heb je toch niet nodig.
	parts = [
		[
			[
				[0, 0, 1, 0],
				[0, 0, 1, 0],
				[0, 0, 1, 0],
				[0, 0, 1, 0]
			],
			[
				[0, 0, 0, 0],
				[1, 1, 1, 1],
				[0, 0, 0, 0],
				[0, 0, 0, 0]
			]
		],
		[
			[
				[1, 1],
				[1, 1]
			]
		],
		[
			[
				[0, 1, 0],
				[0, 1, 0],
				[0, 1, 1]
			],
			[
				[0, 0, 0],
				[1, 1, 1],
				[1, 0, 0]
			],
			[
				[1, 1, 0],
				[0, 1, 0],
				[0, 1, 0]
			],
			[
				[0, 0, 1],
				[1, 1, 1],
				[0, 0, 0]
			]
		],
		[
			[
				[0, 1, 0],
				[0, 1, 1],
				[0, 1, 0]
			],
			[
				[0, 0, 0],
				[1, 1, 1],
				[0, 1, 0]
			],
			[
				[0, 1, 0],
				[1, 1, 0],
				[0, 1, 0]
			],
			[
				[0, 1, 0],
				[1, 1, 1],
				[0, 0, 0]
			]
		],
		[
			[
				[0, 1, 0],
				[0, 1, 0],
				[1, 1, 0]
			],
			[
				[1, 0, 0],
				[1, 1, 1],
				[0, 0, 0]
			],
			[
				[0, 1, 1],
				[0, 1, 0],
				[0, 1, 0]
			],
			[
				[0, 0, 0],
				[1, 1, 1],
				[0, 0, 1]
			]
			
		],
		[
			[
				[0, 1, 0],
				[1, 1, 0],
				[1, 0, 0]
			],
			[
				[1, 1, 0],
				[0, 1, 1],
				[0, 0, 0]
			]
		],
		[
			[
				[1, 0, 0],
				[1, 1, 0],
				[0, 1, 0]
			],
			[
				[0, 1, 1],
				[1, 1, 0],
				[0, 0, 0]
			]
		]
	]

	part_colors = [
		Color(29, 172, 214),
		Color(255, 50, 19),
		Color(255, 151, 28),
		Color(255, 213, 0),
		Color(121, 58, 198),
		Color(114, 203, 59),
		Color(255, 0, 127)
	]

	def inputs():
		while player.alive:	#Het idee is dat je zoveel keer als je wilt kan drukken, en er wordt een nieuwe frame gemaakt voor elke druk.
			global button_direction
			if GPIO.input(BUTTON_UP):
				button_direction = UP
				while GPIO.input(BUTTON_UP):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_DOWN):
				button_direction = DOWN
				while GPIO.input(BUTTON_DOWN):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_LEFT):
				button_direction = LEFT
				while GPIO.input(BUTTON_LEFT):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_RIGHT):
				button_direction = RIGHT
				while GPIO.input(BUTTON_RIGHT):
					time.sleep(0.05)
			elif GPIO.input(BUTTON_MID):
				button_direction = MID
				while GPIO.input(BUTTON_MID):
					time.sleep(0.05)
			time.sleep(0.05)

	class Tetris:	#0-2  1-1  5-2  6-2
		width = 10
		total_parts = 7
		side_line_color = 125

		def __init__(self):
			self.part = randint(0, Tetris.total_parts - 1)	#-1 want randint kan zowel het eerste als het laatste getal nog zijn.
			self.next_part = randint(0, Tetris.total_parts - 1)
			self.rotation = 0	#0, 1, 2, of 3
			self.dropping = True	#Vanaf dat het deeltje wordt tegengehouden wordt er een nieuw deeltje gemaakt.
			self.alive = True		#Bij game over wordt dit false.
			self.score = 0			#De score
			#sub (van subtract) & self.maxRotation zijn er zodat ik geen error krijg van list out of range.
			if self.part == 0:		#Speciaal geval
				self.sub = 0
				self.maxRotation = 1
			elif self.part == 1:	#Het andere speciaal geval
				self.sub = 2
				self.maxRotation = 0
			else:					#Anders normaal
				self.sub = 1
				self.maxRotation = 3
				if self.part > 4 or self.part == 0:
					self.maxRotation = 1
			self.x = int(5 - (4 - self.sub) / 2)				#Het veld is 4px kleiner dan het scherm.
			self.y = slen - 4 + self.sub
			#Side line
			for y in range(0, slen):
				strip.setPixelColor(convertPos(10, y), Tetris.side_line_color)	#Het veld is 10 breed, en we beginnen te tellen bij 0, dus 10 + 1 - 1 = 10.

		def part_wegdoen(self):
			for y in range(0, 4 - self.sub):
				for x in range(0, 4 - self.sub):
					# print("self.sub: " + str(self.sub))
					# print("self.part: " + str(self.part))
					# print("x: " + str(x) + ",y: " + str(y))
					if parts[self.part][self.rotation][y][x]:
						strip.setPixelColor(convertPos(self.x + x, self.y + y), 0)

		def part_terugdoen(self):
			for x in range(0, 4 - self.sub):	#4, want de max part breedte & hoogte zijn 4 (breedte is altijd gelijk aan hoogte met de figuren, voor makkelijk draaien.)
				for y in range(0, 4 - self.sub):
					if parts[self.part][self.rotation][y][x]:		#De inhoud is een 1 of een 0, 1 is True, 0 is False.
						strip.setPixelColor(convertPos(self.x + x,self.y + y), part_colors[self.part])

		def drop(self, full = False):
			eenKeer = True		#Begint met True, maar na 1 keer wordt hij False.
			#Eerst het deeltje wegdoen (elke gevulde pixel wisselen met niks.)
			self.part_wegdoen()
			while self.dropping and full or eenKeer:
				eenKeer = False		#Zodat als full niet True is, dit de enige keer is dat de while loop doorlopen wordt.
				#checken of er iets onder elke gevulde pixel staat van het deeltje. En tegelijkertijd kijken of er een gevulde pixel beneden is.
				for y in range(0, 4 - self.sub):
					for x in range(0, 4 - self.sub):
						if parts[self.part][self.rotation][y][x]:	#Kijken of deze pixel gevuld is.
							if self.y + y == 0:	#Kijken of ik al beneden ben
								self.dropping = False	#Als dat zo is, dan kunnen we niet meer verder.
							elif strip.getPixelColor(convertPos(self.x + x, self.y + y - 1)) != 0:	#Kijken of er iets onder staat. (zichzelf niet meegeteld, want het deeltje is tijdelijk weggedaan.)
								self.dropping = False	#Als dat zo is, dan moeten we stoppen met droppen.

				if self.dropping:	#Als alles in orde is, kunnen we eentje droppen.
					self.y -= 1

			#En ten slotte moeten we het deeltje nog terug zetten.
			self.part_terugdoen()

			if not self.dropping:	#Kan niet in de else boven deze regel, want na dit is de part mss verandert.
				self.newPart()

		def changeX(self, direction):	#Direction is -1 voor links, of 1 voor rechts.
			check = True	#Wordt False als we niet kunnen opschuiven.
			#Eerst het deeltje wegdoen (elke gevulde pixel wisselen met niks.)
			self.part_wegdoen()
			#Checken of het deeltje kan opschuiven. (Kijken of er iets in de weg staat, en of het al tegen een kant zit.)
			for y in range(0, 4 - self.sub):
				for x in range(0, 4 - self.sub):
					if parts[self.part][self.rotation][y][x]:	#Kijken of deze pixel gevuld is.
						if self.x + x + direction < 0 or self.x + x + direction > 9:	#Kijken de rand naast deze px is.
							check = False	#Als dat zo is, dan kunnen we niet meer verder.
						elif strip.getPixelColor(convertPos(self.x + x + direction, self.y + y)) != 0:	#Kijken of er iets naast staat. (zichzelf niet meegeteld, want het deeltje is tijdelijk weggedaan.)
							check = False	#Als dat zo is, dan moeten we stoppen met droppen.
			if check:	#Als check nog True is kunnen we X veranderen.
				self.x += direction
			#Nu moeten we het deeltje nog terugzetten
			self.part_terugdoen()


		def drawSide(self):
			"""Deze functie gaat alles dat niet met het veld te maken heeft tekenen"""

			#Next part
			#sub (van subtract) is zodat ik geen error krijg van list out of range.
			if self.next_part > 1:
				sub_next = 1
			elif self.next_part == 1:
				sub_next = 2
			else:
				sub_next = 0
			#background (Moet voor next_part want anders verft de background die weg.)
			for x in range(0, 4):
				for y in range(0, slen):
					strip.setPixelColor(convertPos(x + 12, y + 12), 0)
			#Vullen van die plek
			for x in range(0, 4 - sub_next):	#4, want de max part breedte & hoogte zijn 4 (breedte is altijd gelijk aan hoogte met de figuren, voor makkelijk draaien.)
				for y in range(0, 4 - sub_next):
					if parts[self.next_part][0][y][x]:		#De inhoud is een 1 of een 0, 1 is True, 0 is False. De nul is omdat een nieuw deeltje altijd rotatie 0 heeft.
						strip.setPixelColor(convertPos(x + 12 + sub_next, y + 12 + sub_next), part_colors[self.next_part])	#"+ 12 + sub" omdat ze mooi in de rechter boven hoek moeten komen ongeacht hun grootte.

		def newPart(self):
			"""Deze functie checkt of er een volledige lijn is, en maakt een nieuwe part aan."""
			aantRijen = 0
			EersteVolleRij = -1	#-1 (onmogelijk) om te kunnen zien of hij al aangepast is
			rij = -1
			for rij in range(0, slen):	#Hiermee maak ik alle volle rijen wit
				vol = True
				for x in range(0, 10):
					if strip.getPixelColor(convertPos(x, rij)) == 0:
						vol = False
				if vol:	#Als vol nog altijd True is is de hele rij gevult.
					aantRijen += 1
					if EersteVolleRij == -1:
						EersteVolleRij = rij
					#Wit laten worden
					for x in range(0, 10):
						strip.setPixelColor(convertPos(x, rij), Color(255, 255, 255))
			strip.show()
			time.sleep(0.3)
			#Nu moeten we de witte rijen wegdoen en alles laten zakken.
			#Eerst de witte pixels op 0 zetten.
			for y in range(EersteVolleRij, EersteVolleRij + aantRijen):
				for x in range(0, 10):
					strip.setPixelColor(convertPos(x, y), 0)
			#Dan alles het juiste aantal pixels laten zakken.
			for y in range(EersteVolleRij, slen - aantRijen):
				for x in range(0, 10):
					strip.setPixelColor(convertPos(x, y), strip.getPixelColor(convertPos(x, y + aantRijen)))
			#En als laatste de nieuwe lege rijen leeg maken
			for y in range(slen - aantRijen, slen):
				for x in range(0, 10):
					strip.setPixelColor(convertPos(x, y), 0)
			#Nu moeten we de score updaten.
			self.score += (2 * aantRijen) ** 2 * 100
			#En nu moeten we nog een nieuw deeltje maken
			self.part = self.next_part
			self.next_part = randint(0, Tetris.total_parts - 1)
			self.dropping = True	#Vanaf dat het deeltje wordt tegengehouden wordt er een nieuw deeltje gemaakt.
			self.rotation = 0	#0, 1, 2, of 3
			#sub (van subtract) & self.maxRotation zijn er zodat ik geen error krijg van list out of range.
			self.maxRotation = 3
			if self.part == 0:		#Speciaal geval
				self.sub = 0
				self.maxRotation = 1
			elif self.part == 1:	#Het andere speciaal geval
				self.sub = 2
				self.maxRotation = 0
			else:					#Anders normaal
				self.sub = 1
				self.maxRotation = 3
				if self.part > 4 or self.part == 0:
					self.maxRotation = 1
			self.x = int(5 - (4 - self.sub) / 2)				#Het veld is 4px kleiner dan het scherm.
			self.y = slen - 4 + self.sub
			#Kijken of het nieuw stukje past
			for y in range(0, 4 - self.sub):
				for x in range(0, 4 - self.sub):
					if parts[self.part][self.rotation][y][x] and strip.getPixelColor(convertPos(self.x + x, self.y + y)) != 0:	#Kijken of deze pixel gevuld is terwijl er al iets staat.
						self.alive = False	#Als dat zo is, dan is het game over.
			#Als laatste moeten we het nieuwe deeltje al tekenen, zodat je al kan zien of je dood bent of niet.
			for y in range(0, 4 - self.sub):
				for x in range(0, 4 - self.sub):
					if parts[self.part][self.rotation][y][x]:
						strip.setPixelColor(convertPos(self.x + x, self.y + y), part_colors[self.part])

		def rotatePiece(self):
			"""Deze mothod laat het gesecteerde deeltje 90 graden draaien als dat gaat. En als het nodig is laat hij het deeltje ook een px van de rand wegspringen."""
			past = True
			linkerRandCheck = True
			rechterRandCheck = True
			pxCheck = True

			def pastHet():
				past1 = True
				linkerRandCheck1 = True
				rechterRandCheck1 = True
				pxCheck1 = True
				for y in range(0, 4 - self.sub):
					for x in range(0, 4 - self.sub):
						if parts[self.part][self.rotation][y][x]:	#Kijken of deze pixel gevuld is.
							if self.x + x < 0:	#Kijken of deze px in de linker rand zit.
								past1 = False
								linkerRandCheck1 = False		#Kijken of deze px in de linker rand zit.
							elif self.x + x > 9:
								past = False
								rechterRandCheck1 = False
							elif strip.getPixelColor(convertPos(self.x + x, self.y + y)) != 0:	#Kijken of er al iets staat. (zichzelf niet meegeteld, want het deeltje is tijdelijk weggedaan.)
								past1 = False
								pxCheck1 = False
				return past1, linkerRandCheck1, rechterRandCheck1, pxCheck1

			#Het oude deeltje wegdoen.
			self.part_wegdoen()
			#Draaien
			self.rotation += 1
			if self.rotation > self.maxRotation:
				self.rotation = 0
			#Checken of het nieuwe deeltje past.
			past, linkerRandCheck, rechterRandCheck, pxCheck = pastHet()
			#Op basis daarvan verdergaan, en proberen het toch te laten passen als het tegen de rand zit.
			pogingen = 0
			if not linkerRandCheck:
				while not past and pogingen < 3:
					pogingen += 1
					self.x += 1
					past, linkerRandCheck, rechterRandCheck, pxCheck = pastHet()
			elif not rechterRandCheck:
				while not past and pogingen < 3:
					pogingen += 1
					self.x -= 1
					past, linkerRandCheck, rechterRandCheck, pxCheck = pastHet()
			elif not past:
				self.rotation -= 1
				if self.rotation < 0:
					self.rotation = self.maxRotation
			#Kijken of het nu wel past of niet.
			if not linkerRandCheck:
				print("Kon niet draaien, linkerRandCheck")
				self.x -= pogingen
				self.rotation -= 1
				if self.rotation < 0:
					self.rotation = self.maxRotation
			elif not rechterRandCheck:
				print("Kon niet draaien, rechterRandCheck")
				self.x += pogingen
				self.rotation -= 1
				if self.rotation < 0:
					self.rotation = self.maxRotation
			#Nu dat het deeltje uiteindelijk wel of niet gedraaid is kunnen we het terug zetten.
			self.part_terugdoen()
			strip.show()	#Voor snelle reactie moet het gedraaide deeltje direct getekend worden.

		# """Dit was de oude rotate functie maar hij was ingewikkeld er zaten nog bugs in, ik heb later besloten om de parts list een dimentie voor rotaties te geven. Dit kost meer geheugen maar is overzichtelijker en sneller."""
		# def rotatePieceOld(self):
		# 	"""Deze mothod laat het gesecteerde deeltje 90 graden draaien als dat gaat. En als het nodig is laat hij het deeltje ook een px van de rand wegspringen."""
		# 	global parts
		# 	past = True
		# 	linkerRandCheck = True
		# 	rechterRandCheck = True
		# 	pxCheck = True
		# 	def pastHet():
		# 		print("checken of het past.")
		# 		for y in range(0, 4 - self.sub):
		# 			for x in range(0, 4 - self.sub):
		# 				if self.x + x < 0:	#Kijken of deze px in de linker rand zit.
		# 					past = False
		# 					linkerRandCheck = False		#Kijken of deze px in de linker rand zit.
		# 				elif self.x + x > 9:
		# 					past = False
		# 					linkerRandCheck = False
		# 				elif strip.getPixelColor(convertPos(self.x + x, self.y + y)) != 0:	#Kijken of er iets naast staat. (zichzelf niet meegeteld, want het deeltje is tijdelijk weggedaan.)
		# 					past = False
		# 					pxCheck = False
		# 	def terugDraaien():
		# 		global parts
		# 		#De rotatie updaten zodat we uiteindelijk het stukje terug juist kunnen zetten.
		# 		self.rotation -= 1
		# 		if self.rotation < 0:
		# 			self.rotation = 3
		# 		if self.sub == 0:	#(3x3 clockwise)
		# 			hulp = parts[self.part]
		# 			parts[self.part] = rotated_long
		# 			rotated_long = hulp
		# 		elif self.sub == 1:
		# 			hulp = parts[self.part][0][0]
		# 			parts[self.part][0][0] = parts[self.part][0][2]
		# 			parts[self.part][0][2] = parts[self.part][2][2]
		# 			parts[self.part][2][2] = parts[self.part][2][0]
		# 			parts[self.part][2][0] = hulp
		# 			hulp = parts[self.part][0][1]
		# 			parts[self.part][0][1] = parts[self.part][1][2]
		# 			parts[self.part][1][2] = parts[self.part][2][1]
		# 			parts[self.part][2][1] = parts[self.part][1][0]
		# 			parts[self.part][1][0] = hulp
		# 	#De rotatie updaten zodat we uiteindelijk het stukje terug juist kunnen zetten.
		# 	self.rotation += 1
		# 	if self.rotation % 3 == 0:
		# 		self.rotation = 0
		# 	#het deeltje wegdoen
		# 	self.part_wegdoen()
		# 	#het deeltje 90 graden counterclockwise draaien
		# 	if self.sub == 0:
		# 		hulp = parts[self.part]
		# 		parts[self.part] = rotated_long
		# 		rotated_long = hulp
		# 	elif (self.part == 5 or self.part == 6) and self.rotation != 0:
		# 		terugDraaien()
		# 	elif self.sub == 1:	#(3x3 counterclockwise)
		# 		hulp = parts[self.part][2][0]
		# 		parts[self.part][2][0] = parts[self.part][2][2]
		# 		parts[self.part][2][2] = parts[self.part][0][2]
		# 		parts[self.part][0][2] = parts[self.part][0][0]
		# 		parts[self.part][0][0] = hulp
		# 		hulp = parts[self.part][1][0]
		# 		parts[self.part][1][0] = parts[self.part][2][1]
		# 		parts[self.part][2][1] = parts[self.part][1][2]
		# 		parts[self.part][1][2] = parts[self.part][0][1]
		# 		parts[self.part][0][1] = hulp
		# 	#Kijken of het deeltje nu past.
		# 	pastHet()
		# 	#Nu gaan we proberen het deeltje terug te zetten
		# 	if not linkerRandCheck:
		# 		print("Linker")
		# 		if self.part == 0:	#Het enige deel waarbij we 2 px moeten opschuiven.
		# 			self.changeX(2)
		# 		else:
		# 			self.changeX(1)
		# 		past = True
		# 		pastHet()
		# 		if not past:	#Als het nu nog niet past dan draait het deeltje gewoon niet.
		# 			terugDraaien()
		# 			print("ging niet, links")
		# 	elif not rechterRandCheck:
		# 		print("Rechter")
		# 		if self.part == 0:	#Het enige deel waarbij we 2 px moeten opschuiven.
		# 			self.changeX(-2)
		# 		else:
		# 			self.changeX(-1)
		# 		past = True
		# 		pastHet()
		# 		if not past:	#Als het nu nog niet past dan draait het deeltje gewoon niet.
		# 			terugDraaien()
		# 			print("ging niet, rechts")
		# 	elif not pxCheck:
		# 		terugDraaien()
		# 		print("ging niet, px")
		# 	#Nu dat het deeltje gedraait of niet gedraait is moeten we het nog terug zetten.
		# 	self.part_terugdoen()
		# 	strip.show()

	#Tijd variablen initialiseren
	frameStart = 0.0
	frameDuration = 0.5	#Wordt korter hoe hoger de player komt.
	player = Tetris()
	thread.start_new_thread(inputs,())
	while player.alive:
		frameStart = time.time()
		player.drawSide()
		player.drop()
		strip.show()
		#player.next_part = randint(0, Tetris.total_parts - 1)
		strip.show()

		while time.time() - frameStart < frameDuration:
			if button_direction == UP:
				player.rotatePiece()
				strip.show()	#Voor de responsiveness tekenen we het verplaatste deeltje zo rap mogelijk
				button_direction = NIKS
			elif button_direction == LEFT:
				player.changeX(-1)
				strip.show()	#Voor de responsiveness tekenen we het verplaatste deeltje zo rap mogelijk
				button_direction = NIKS
			elif button_direction == RIGHT:
				player.changeX(1)
				strip.show()	#Voor de responsiveness tekenen we het verplaatste deeltje zo rap mogelijk
				button_direction = NIKS
			elif button_direction == MID:
				button_direction = NIKS
				break	#Door de while te skippen dropt het deeltje automatisch 1px.
			elif button_direction == DOWN:
				button_direction = NIKS
				player.drop(True)	#True betekent een full drop.
	print("Game Over.")
	#Deze hebben we nu niet meer nodig.
	del button_direction
	del parts
	time.sleep(1)
	background()

	game_duur = int(game_duur - time.time())
	cur.execute("INSERT INTO tblScores(SpelerId,Spel,Score,Tijd,Duur) VALUES (%s,%s,%s,%s,%s)",(wieId,"Tetris",player.score,time.strftime("%H:%M:%S"),game_duur))
	print("Uploading -> Tetris -> score:" + str(player.score) + " Tijd:" + time.strftime("%H:%M:%S") + " Duur:" + str(game_duur) + " SpelerId: " + str(wie))
	wie = "Speler"
	game_active = False
	return player.score






def main():
	while True:
		print("zet hier nog iets.")
		# game_Tetris()
		time.sleep(10)


#main programma in multithread
thread.start_new_thread(main,())

@app.route('/')
def index():
	#webpagina laden
	return render_template("gip.html")

@app.route('/playGame', methods=["POST"])	#De methods=["POST"] moet er staan bij deze functie.
def playGame():
	global wie
	game = request.form["game"]
	if not game_active:
		if game == "FlappyBird":
			score = game_Flappybird()
		elif game == "Snake":
			score = game_Snake()
		elif game == "Stacker":
			score = game_Stacker()
		elif game == "animatieBesturen":
			score = 10
			game_animatieBesturen()
		elif game == "Tetris":
			score = game_Tetris()
		else:
			score = 0
		wie = "Speler"
		wieId = 0
		return str(score)
	else:
		return "Error: Er is al een game bezig."

@app.route('/getName')
def getName():
	if not game_active:
		lcd.clear()	#Lcd clearen
		lcd.cursor_pos = (0, 0)
		lcd.write_string("Plaats je badge.")
		lezen()
		lcd.clear()	#Lcd clearen
		lcd.cursor_pos = (0, 0)
		lcd.write_string("Welkom ")
		lcd.cursor_pos = (0, 7)
		lcd.write_string(wie)
		lcd.cursor_pos = (1, 0)
		lcd.write_string("Je bent ingelogd")		#Naam erop zetten.
		return str(wie)
	return "Error: Er is een game bezig."

def stop():
	print(" stop() wordt doorlopen")
	for i in range(0, LED_COUNT):	#(Scherm) Alles op nul zetten.
		strip.setPixelColor(i, 0)
	cur.close()		#Van DB connectie
	conn.close()	#Van DB connectie
	lcd.clear()	#Het lcd clearen.
	lcd.close()	#De lcd uitzetten. (De pins terug vrijgeven.)
	strip.show()	#(Scherm) Update display.
	strip._cleanup()	#(Scherm) Memory gebruikt door library vrijstellen.
	GPIO.cleanup()		#GPIO pins vrijmaken.

if __name__ == '__main__':
	#de __name__ is alleen '__main__' als deze file uitgevoerd wordt, dus niet als hij met import (naam) toegevoegd werd.
	#host='0.0.0.0' ==> De webapp is nu bereikbaar via het ip van de raspberry pi. 
	#De webapp gaat luisteren op poort 5050
	atexit.register(stop)	#functie 'stop' doorlopen wanneer server stopt
	app.run(debug=True, host='0.0.0.0', port=5050, use_reloader=False)