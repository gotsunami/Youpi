// Global variables
var tab;

function globstat()
	
{
	var xhr = new HttpRequest(
		null,
		null,
		function(resp)
		{
			
			var tab = resp['data']['survey'];
			var	tab1 = resp['data']['instrument'];

			var tdname = document.getElementById('survey_name');
			tdname.innerHTML = tab[0];

			var tdcomment = document.getElementById('survey_comment');
			tdcomment.innerHTML = tab[1];

			var tdurl = document.getElementById('survey_link');
			tdurl.setAttribute('href',tab[2]);
			tdurl.innerHTML = tab[2];

			var inst_number = document.getElementById('instrument_number');
			inst_number.setAttribute('align','center');
			inst_number.innerHTML = tab1.length+' Instruments';

			var tdinstrument = document.getElementById('instrument');
			tdinstrument.setAttribute('align','center');
			for (var i = 0 ; i < tab1.length ; i++)
			{
				instrument  = document.createElement('input');
				instrument.setAttribute('type','button');
				instrument.setAttribute('style','background:white;color:black;padding: 2px 5px;height: 30px;width: 100px;');
				instrument.setAttribute('value',tab1[i]);
				instrument.setAttribute('id',tab1[i]);
				instrument.setAttribute('onClick',"display1('" + tab1[i] + "');");
				tdinstrument.appendChild(instrument);
			}
		}
	);
	var post = 'globstat=toto';
	xhr.send('/spica2/newindex/',post);
}



function display1(name)
{
	var xhr = new HttpRequest(
        null,
        null,
        function(resp)
        {
			var tab = resp['data']['run'];
			var tab1 = resp['data']['instrument_field'];
			tab.sort()
		
			document.getElementById('disp').setAttribute('style','display:block');
			//traitement de l'allumage des boutons instrument correspondants	
			buttons = document.getElementsByTagName('input');
			for (var i = 0 ; i < buttons.length ; i++)
            {
				buttons[i].setAttribute('style','background:white;color:black;padding: 2px 5px;height: 30px;width: 100px;');
			}
	
			var button = document.getElementById(name);
			button.setAttribute('style','background:#CCCCFF;color:black;padding: 2px 5px;height: 30px;width: 100px;');

			//fin de traitement de l'allumage des boutons instrument correspondants	

			//traitement de l'affichage du nb de run corresponadant a la selection
			var run_number = document.getElementById('run_number');
			run_number.setAttribute('align','center');
  			run_number.innerHTML = tab.length + ((tab.length > 1)?' Runs for ':' Run for ') + name ;
			//fin traitement de l'affichage du nb de run corresponadant a la selection

			//affichage des boutons run
			var run = document.getElementById('div_run_list');	

			run.innerHTML = '';

			if(tab.length == 0)
			{
				run.innerHTML = 'No runs are related with the Instrument '+'<CENTER><B>'+name+'</CENTER></B>';
			} 

			for (var i = 0 ; i < tab.length ; i++)
			{
				input  = document.createElement('input');
				input.setAttribute('type','button');
				input.setAttribute('style','background:white;color:black;padding: 2px 5px;height: 30px;width: 100px;');
				input.setAttribute('id',tab[i]);
				input.setAttribute('value',tab[i]);
				input.setAttribute('onClick',"display2('" + tab[i] + "');");
				run.appendChild(input);
			}
			
			//affichage des infos instrument
			var display = document.getElementById('display_instrument_info');
            display.innerHTML = '';
			if(tab1.length == 0)
            {
                display.innerHTML = 'No INFO';
            }
			
			var table = document.createElement('table');	
            for (var i = 0 ; i < tab1.length ; i=i+2)

            {
               tr = document.createElement('tr');
				td1 = document.createElement('td');
				td1.setAttribute('bgcolor','#CCCCFF');
				td2 = document.createElement('td');
				td1.innerHTML = tab1[i];

				if (tab1[i+1] == '')
                {
                    td2.innerHTML = '<b> - </B>';
                }
				
				else if (tab1[i+1] == 'None')
                {
                    td2.innerHTML = '<b> - </B>';
                }
                else
                {
                    td2.innerHTML = '<b>'+tab1[i+1]+'</B>';
                }

				tr.appendChild(td1);
				tr.appendChild(td2);
				table.appendChild(tr);
				display.appendChild(table);
            }


		}
	);
	
	var post = 'Kind=' + name;
    xhr.send('/spica2/newindex/', post);
}

function display2(info)
{
    var xhr = new HttpRequest(
        null,
        null,
        function(resp)
        {
			//setTimeout(display2,7000);
			//all fields from run table
            var tab = resp['data']['run_field'];

			//image count by channel
            var tab1 = resp['data']['image_count_channel'];

			//image count by channel from fitstable
            var tab2 = resp['data']['image_count_fits'];

			tab1.sort();
			tab2.sort();
			
			//display run informations from run table
			document.getElementById('display_run').setAttribute('style','display:block');

			buttons = document.getElementsByTagName('input');
            for (var i = 0 ; i < buttons.length ; i++)
            {
                buttons[i].setAttribute('style','background:white;color:black;padding: 2px 5px;height: 30px;width: 100px;');
            }

			var button = document.getElementById(info);
			button.setAttribute('style','background:#CCCCFF;color:black;padding: 2px 5px;height: 30px;width: 100px;');

            var display1 = document.getElementById('display_run_info');

            display1.innerHTML = '';

            if(tab.length == 0)
            {
                display1.innerHTML = 'No INFO';
            }

			var table = document.createElement('table');
            for (var i = 0 ; i < tab.length ; i=i+2)

            {
               tr = document.createElement('tr');
                td1 = document.createElement('td');
                td1.setAttribute('bgcolor','#CCCCFF');
                td2 = document.createElement('td');
                td1.innerHTML = tab[i];

				if (tab[i+1] == 'None')
                {
                    td2.innerHTML = '<b> - </B>';
                }
				else if (tab[i+1] == '')
				{
					td2.innerHTML = '<b> - </B>';
				}
				else
				{
                	td2.innerHTML = '<b>'+tab[i+1]+'</B>';
				}
                tr.appendChild(td1);
                tr.appendChild(td2);
                table.appendChild(tr);
                display1.appendChild(table);
            }
			//End of the run's display


			
			//Display images count by channels from table image
			document.getElementById('display_image').setAttribute('style','display:block');
            var display_image_count = document.getElementById('display_image_info');

            display_image_count.innerHTML = '';
			var table = document.createElement('table');
			table.setAttribute('style','align:center');
			var tr = document.createElement('tr');
			var tdgauche = document.createElement('td');
			tdgauche.setAttribute('width','80px');
			tdgauche.innerHTML = '<center>Fitstables</center>';
			var tdmid = document.createElement('td');
			tdmid.setAttribute('width','70px');
			tdmid.innerHTML = '<center>Ingestion</center>';
			var tddroit = document.createElement('td');
			tddroit.setAttribute('width','70px');
			tddroit.innerHTML = '<center>Matching</center>';
			var tdinfo = document.createElement('td');
			tdinfo.setAttribute('width','190px');
			tdinfo.innerHTML = '<center>Info</center>';
			var tdstatus = document.createElement('td');
			tdstatus.innerHTML = '<center>Status</center>';
			tr.appendChild(tdgauche);
			tr.appendChild(tdmid);
			tr.appendChild(tddroit);
			tr.appendChild(tdinfo);
			tr.appendChild(tdstatus);
			table.appendChild(tr);
			display_image_count.appendChild(table);
			
			var count_fits = 0;
			for(var i = 0 ; i < tab2.length ; i++)
			{
				var tr = document.createElement('tr');
				var tdg = document.createElement('td');
				var tdm = document.createElement('td');
				var tdd = document.createElement('td');
				var tdi = document.createElement('td');
				var tds = document.createElement('td');
				tdg.innerHTML ='<center>'+ tab2[i][0]+' : <b>'+tab2[i][1]+' </b></center>';
				tr.appendChild(tdg);

				count_fits += parseInt(tab2[i][1]); 

				var count_channel = 0;
				for(var j = 0 ; j < tab1.length ; j++)
				{	
					count_channel += parseInt(tab1[j][1]); 

					if(tab2[i][0] == tab1[j][0])
					{
						tdm.innerHTML = '<center><b>'+tab1[j][1]+' </b></center>';
						tr.appendChild(tdm);
						var val = Math.round(((parseInt(tab1[j][1])*100)/parseInt(tab2[i][1]))*100)/100;

						if (val <= 50)
						{
							tdd.innerHTML = '<center><b><font color=#FF0000>'+val+' %</font></b></center>';
							tr.appendChild(tdd);
							tdi.innerHTML = '<center><font color=#FF0000>Should continue ingestion</font></center>';
							tr.appendChild(tdi);
							tds.innerHTML = '<center><img src=/media/' + guistyle + '/img/admin/icon-no.gif></img></center>';
							tr.appendChild(tds);
						}

						else if ((val < 100) && (val > 50))
						{
							tdd.innerHTML = '<center><b><font color=#FF9900>'+val+' %</font></b></center>';
							tr.appendChild(tdd);
							if((tab2[i][1] - tab1[j][1]) <= 5)
							{
								tdi.innerHTML = '<center><font color=#FF9900>Maybe some images are corrupted</font></center><font color=#339900>(try to run ingestion by unchecking options)';
                    			tr.appendChild(tdi);
								tds.innerHTML = '<center><img src=/media/' + guistyle + '/img/34x34/warning.png width=20px></img></center>';
								tr.appendChild(tds);
							}
							else
							{
                                tdi.innerHTML = '<center><font color=#FF9900>Should continue ingestion</font></center><font color=#FF9900>(try to run ingestion by unchecking options)';
                                tr.appendChild(tdi);
								tds.innerHTML = '<center><img src=/media/' + guistyle + '/img/34x34/warning.png width=20px></img></center>';
				                tr.appendChild(tds);
                            }
						}

						else if ((val == 100) || (val > 100))
						{
							tdd.innerHTML = '<center><b><font color=#339900>'+val+' %</font></b></center>';
                            tr.appendChild(tdd);
							if((tab1[j][1]%tab2[i][1]) == 0)
							{
								tdi.innerHTML = '<center><font color=#339900>All images are ingested</font></center>';
			                    tr.appendChild(tdi);
								tds.innerHTML = '<center><img src=/media/' + guistyle + '/img/admin/icon-yes.gif></img></center>';
								tr.appendChild(tds);
							}

						}
					break;
					}
				}
				if (j == tab1.length)
				{
					tdm.innerHTML = '<center><b>0</b></center>';
                    tr.appendChild(tdm);
                    tdd.innerHTML = '<center><b><font color=#0000FF>0%</font></b></center>';
                    tr.appendChild(tdd);
					tdi.innerHTML = '<center><b><font color=#0000FF>Have to be ingested</font></b></center>';
                    tr.appendChild(tdi);
					tds.innerHTML = '<center><img src=/media/' + guistyle + '/img/admin/ingest.gif></img></center>';
                    tr.appendChild(tds);
				}

				
				table.appendChild(tr);
				display_image_count.appendChild(table);
			}

			//

        }
    );
    var post = 'Kind2=' + info;
    xhr.send('/spica2/newindex/', post);	
}


function display_user()
{
	var xhr = new HttpRequest(
	null,
	null,
	function(resp) 
	{
        var tab = resp['data']['current_user'];
		var div = document.getElementById('user_count');
		div.innerHTML = tab.length+' Current Users';

		var divbis = document.getElementById('div_user_list');
		divbis.innerHTML = '';
		var table = document.createElement('table');
		table.setAttribute('align','center');
		var tr = document.createElement('tr');
		var td_email = document.createElement('td');
		var td_lastlogin = document.createElement('td');
		td_email.setAttribute('align','center');
		td_lastlogin.setAttribute('align','center');
		td_email.appendChild(document.createTextNode('em@il'));
		td_lastlogin.appendChild(document.createTextNode('Last login'));
		tr.appendChild(td_email);
		tr.appendChild(td_lastlogin);
		table.appendChild(tr);

		for(var i = 0 ; i < tab.length ; i++)
		{
		
			var tr = document.createElement('tr');

			if(i%2 == 0)
			{
				tr.setAttribute('bgcolor','lightgrey');
			}

			for (var j = 0 ; j < tab[i].length ; j++)
			{
				td = document.createElement('td');
				td.setAttribute('align','center');
				if(tab[i][j] == '')
                {
                    td.innerHTML =' - ';
					tr.appendChild(td);
                }
				else 
				{
					td.innerHTML =  tab[i][j];
					tr.appendChild(td);
				}
			}
			table.appendChild(tr);
			divbis.appendChild(table);
		}
		

	}
	);
	var post = 'Kind3=titi'; 
	xhr.send('/spica2/newindex/',post);
}


function display3()
{
    var xhr = new HttpRequest(
    null,
    null,
    function(resp)
    {
    }
    );
    var post = 'ingstat=titi';
    xhr.send('/spica2/newindex/',post);
}

function display4()
{
    var xhr = new HttpRequest(
    null,
    null,
    function(resp)
    {
    }
    );
    var post = 'ingstat=titi';
    xhr.send('/spica2/newindex/',post);
}
