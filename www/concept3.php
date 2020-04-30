<!DOCTYPE HTML>
<html>
<head>
	<meta charset="UTF-8">
	<title>Zerotype Website Template</title>
	<link rel="stylesheet" href="css/style.css" type="text/css">
</head>
<body>
	 <div id="header">
		<div>
			<div class="logo">
				<a href="index.html">Zero Type</a>
			</div>
			<ul id="navigation">
				<li class="active">
					<a href="http://10.212.51.24/index.php">Home</a>
				</li>
				<li>
					<a href="http://10.212.51.24/concept/R_Insert.php">Insert</a>
				</li>
				<li>
					<a href="http://10.212.51.24/concept/R_Leerlingen.php">UpDel</a>
				</li>
				<li>
					<a href="http://10.212.51.24/concept/R_GPIO.php">GPIO</a>
				</li>
				<li>
					<a href="/">Airco</a>
				</li>				<li>
					<a href="http://10.212.51.24/concept/Login.php">Login</a>
				</li>
			</ul>
		</div>
	</div>
	<div id="container">
		

		<div id="Wknoppen">
			<!-- Bij het drukken op de knop wordt de js code doorlopen, in dit geval een functie. -->
			<button onclick="buttonvalue(1)">W+</button>

			<!-- Deze div tag ga ik besturen door met jquery te refereren naar zijn id. -->
			<div id="doeltemp">20</div>

			<!-- Bij het drukken op de knop wordt de js code doorlopen, in dit geval een functie. -->
			<button onclick="buttonvalue(-1)">W-</button>
		</div>

		<!-- tussen deze div tag komt het resultaat van de return uit python teller - aantal seconden led aan - -->
		<div id="dutycycle"></div>
	</div>

	<div id="footer">
		<div class="clearfix">
			<div id="connect">
				<a href="http://freewebsitetemplates.com/go/facebook/" target="_blank" class="facebook"></a><a href="http://freewebsitetemplates.com/go/googleplus/" target="_blank" class="googleplus"></a><a href="http://freewebsitetemplates.com/go/twitter/" target="_blank" class="twitter"></a><a href="http://www.freewebsitetemplates.com/misc/contact/" target="_blank" class="tumbler"></a>
			</div>
			<p>
				© 2023 Zerotype. All Rights Reserved.
			</p>
		</div>
	</div>

	<script src="https://code.jquery.com/jquery-1.10.2.js"></script>
	<script>
		//Deze functie krijgt een waarde van de drukknop hierboven en geeft deze waarde door aan de functie die via decorations zoekt naar /doeltemp in onze python server
		//inhoud wordt geplaatst in div tag #doeltemp, nummer is een js variable, getal kan je opvragen in python.
		function buttonvalue(nummer)
		{
			$( "#doeltemp" ).load("/doeltemp", { "getal": nummer });
		}
		//Deze functie krijgt een waarde van onze python server. (return value van "def temperatuur_sturen():")
		//inhoud wordt geplaatst in div tag dutycycle
		window.setInterval(function(){
			$( "#dutycycle" ).load("/tijd");
		}, 1000);
	</script>
</body>
</html>