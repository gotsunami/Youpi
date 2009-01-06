/*
 * Group: Skeleton Plugin
 *
 * JS code for Skeleton plugin.
 *
 * Functions in this file are required for every processing plugin to work. Feel free
 * to add any content in their bodies, but keep the declarations!
 *
 * Mandatory function prototypes:
 *
 * function - {{ plugin.id }}_addSelectionToCart()
 * function - {{ plugin.id }}_addToCart(resultsOutputDir)
 * function - {{ plugin.id }}_delSavedItem(trid, name)
 * function - {{ plugin.id }}_renderOutputDirStats(container_id)
 * function - {{ plugin.id }}_reprocessAllFailedProcessings(tasksList)
 * function - {{ plugin.id }}_resultsShowEntryDetails(container_id)
 * function - {{ plugin.id }}_run(trid, resultsOutputDir, silent)
 * function - {{ plugin.id }}_saveItemForLater(trid, itemId, resultsOutputDir)
 * function - {{ plugin.id }}_showSavedItems()
 *
 */

/*
 * Function: {{ plugin.id }}_addSelectionToCart
 *
 */
function {{ plugin.id }}_addSelectionToCart() {
	// Do your sanity checks here
	// FIXME: checks...

	// Custom output directory
	var output_data_path = '{{ processing_output }}{{ user.username }}/{{ plugin.id }}/';

	// Set mandatory structures
	p_data = {	plugin_name : '{{ plugin.id }}', 
				userData : {resultsOutputDir: output_data_path}
	};

	// Add entry into the shopping cart
	s_cart.addProcessing(	p_data,
							// Custom handler
							function() {
								alert(	'One Skeleton-related job has been added to the cart.Since this is\na DEMO plugin, ' +
										"it will do nothing but running five '/usr/bin/uptime'\njobs on the cluster.");
							}
	);
}

/*
 * Function: {{ plugin.id }}_run
 * Run processing
 *
 * Parameters:
 *	name - string: name part of ID 
 *  row - integer: for row number
 *
 */ 
function {{ plugin.id }}_run(trid, itemId, resultsOutputDir, silent) {
	var silent = silent == true ? true : false;
	var runopts = get_runtime_options(trid);
	var logdiv = document.getElementById('master_condor_log_div');

	var r = new HttpRequest(
			logdiv,
			null,	
			// Custom handler for results
			function(resp) {
				r = resp['result'];
				var success = update_condor_submission_log(resp, silent);
				if (!success) return;

				// Silently remove item from the cart
				removeItemFromCart(trid, true);
			}
	);

	var post = 	'Plugin={{ plugin.id }}' + 
				'&Method=process' +
				'&ResultsOutputDir=' + resultsOutputDir +
				// runtime options related
				'&' + runopts.clusterPolicy +	
				'&ItemId=' + runopts.itemPrefix + itemId + 
				'&ReprocessValid=' + (runopts.reprocessValid ?  1 : 0);
	r.send('/youpi/process/plugin/', post);
}

function {{ plugin.id }}_reprocessAllFailedProcessings(tasksList) {
	alert('TODO...');
}

function {{ plugin.id }}_renderOutputDirStats(container_id) {
	var container = document.getElementById(container_id);
	container.innerHTML = '';

	// global var defined in results.html
	var resp = output_dir_stats_data;
	var stats = resp['Stats'];

	var tab = document.createElement('table');
	tab.setAttribute('class', 'output_dir_stats');
	var tr,th,td;
	var tr = document.createElement('tr');
	// Header
	var header = ['Task success', 'Task failures', 'Total processings'];
	var cls = ['task_success', 'task_failure', 'task_total'];
	for (var k=0; k < header.length; k++) {
		th = document.createElement('th');
		th.setAttribute('class', cls[k]);
		th.setAttribute('colspan', '2');
		th.appendChild(document.createTextNode(header[k]));
		tr.appendChild(th);
	}
	tab.appendChild(tr);

	tr = document.createElement('tr');
	var val, percent, cls;
	for (var k=0; k < header.length; k++) {
		c_td = document.createElement('td');
		p_td = document.createElement('td');
		switch (k) {
			case 0:
				val = stats['TaskSuccessCount'][0];
				percent = stats['TaskSuccessCount'][1] + '%';
				cls = 'task_success';
				break;
			case 1:
				val = stats['TaskFailureCount'][0];
				percent = stats['TaskFailureCount'][1] + '%';
				cls = 'task_failure';
				break;
			case 2:
				val = stats['Total'];
				percent = '100%';
				cls = 'task_total';
				break;
			default:
				break;
		}
		c_td.appendChild(document.createTextNode(val));
		c_td.setAttribute('class', cls);
		p_td.appendChild(document.createTextNode(percent));
		p_td.setAttribute('class', cls);
		tr.appendChild(c_td);
		tr.appendChild(p_td);
	}
	tab.appendChild(tr);
	container.appendChild(tab);
}

function {{ plugin.id }}_saveItemForLater(trid, itemId, resultsOutputDir) {
	var runopts = get_runtime_options(trid);
	var r = new HttpRequest(
			'{{ plugin.id}}_result',
			null,	
			// Custom handler for results
			function(resp) {
				// Silently remove item from the cart
				removeItemFromCart(trid, true);
				// Global function (in shoppingcart.html)
				showSavedItems();
			}
	);

	var post = 	'Plugin={{ plugin.id }}&Method=saveCartItem' + 
				'&ItemID=' + runopts.itemPrefix + itemId +
				'&ResultsOutputDir=' + resultsOutputDir;
	r.send('/youpi/process/plugin/', post);
}

/*
 * Displays custom result information. 'resp' contains 
 * server-side info to display
 *
 */
function {{ plugin.id }}_resultsShowEntryDetails(container_id) {
	var tr, th, td;
	// See templates/results.html, function showDetails(...)
	var resp = currentReturnedData;
	var container = document.getElementById(container_id);
	var d = document.createElement('div');
	d.setAttribute('class', 'entryResult');
	var tab = document.createElement('table');
	tab.setAttribute('class', 'fileBrowser');
	tab.setAttribute('style', 'width: 100%');

	tr = document.createElement('tr');
	th = document.createElement('th');
	th.appendChild(document.createTextNode(resp['Title']));
	tr.appendChild(th);
	tab.appendChild(tr);

	// Duration
	var tdiv = document.createElement('div');
	tdiv.setAttribute('class', 'duration');
	tdiv.appendChild(document.createTextNode(resp['Start']));
	tdiv.appendChild(document.createElement('br'));
	tdiv.appendChild(document.createTextNode(resp['End']));
	tdiv.appendChild(document.createElement('br'));
	var src;
	resp['Success'] ? src = 'success' : src = 'error';
	var img = document.createElement('img');
	img.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif');
	img.setAttribute('style', 'padding-right: 5px;');
	tdiv.appendChild(img);
	tdiv.appendChild(document.createTextNode(resp['Duration']));
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
	td.appendChild(tdiv);
	tr.appendChild(td);
	tab.appendChild(tr);

	// User
	var udiv = document.createElement('div');
	udiv.setAttribute('class', 'user');
	udiv.appendChild(document.createTextNode('Job initiated by ' + resp['User']));
	udiv.appendChild(document.createElement('br'));
	udiv.appendChild(document.createTextNode('Exit status: '));
	udiv.appendChild(document.createElement('br'));
	var exit_s = document.createElement('span');
	var txt;
	resp['Success'] ? txt = 'success' : txt = 'failure';
	exit_s.setAttribute('class', 'exit_' + txt);
	exit_s.appendChild(document.createTextNode(txt));
	udiv.appendChild(exit_s);
	td.appendChild(udiv);

	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('style', 'padding: 0px');
	var tab2 = document.createElement('table');
	tab2.setAttribute('class', 'qfits-result-entry-params');
	td.appendChild(tab2);
	tr.appendChild(td);
	tab.appendChild(tr);

	// Error log file when failure
	if (!resp['Success']) {
		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		td.setAttribute('colspan', '2');
		var but = document.createElement('input');
		but.setAttribute('type', 'button');
		but.setAttribute('value', 'Toggle error log file view');
		but.setAttribute('onclick', "toggleDisplay('log-" + resp['TaskId'] + "');");
		td.appendChild(but);
		var cdiv = document.createElement('div');
		cdiv.setAttribute('id', 'log-' + resp['TaskId']);
		cdiv.setAttribute('style', 'height: 200px; overflow: auto; background-color: black; padding-left: 5px; display: none')
		var pre = document.createElement('pre');
		pre.appendChild(document.createTextNode(resp['Log']));
		cdiv.appendChild(pre);
		td.appendChild(cdiv);
		tr.appendChild(td);
		tab2.appendChild(tr);
	}

	d.appendChild(tab);
	container.appendChild(d);
}

function {{ plugin.id }}_showSavedItems() {
	var cdiv = document.getElementById('plugin_menuitem_sub_{{ plugin.id }}');
	cdiv.innerHTML = '';
	var div = document.createElement('div');
	div.setAttribute('class', 'savedItems');
	div.setAttribute('id', '{{ plugin.id }}_saved_items_div');
	cdiv.appendChild(div);

	var r = new HttpRequest(
			div.id,
			null,	
			// Custom handler for results
			function(resp) {
				// Silently remove item from the cart
				removeAllChildrenNodes(div);
				removeAllChildrenNodes(div);

				var total = resp['result'].length;
				var countNode = document.getElementById('plugin_{{ plugin.id }}_saved_count');
				countNode.innerHTML = '';
				var txt;
				if (total > 0)
					txt = total + ' item' + (total > 1 ? 's' : '');
				else
					txt = 'No item';
				countNode.appendChild(document.createTextNode(txt));

				var table = document.createElement('table');
				table.setAttribute('class', 'savedItems');
				var tr, th;
				var icon = document.createElement('img');
				icon.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/32x32/{{ plugin.id }}' + '.png');
				icon.setAttribute('style', 'vertical-align:middle; margin-right: 10px;');

				tr = document.createElement('tr');
				th = document.createElement('th');
				th.setAttribute('colspan', '8');
				th.appendChild(icon);
				th.appendChild(document.createTextNode('{{ plugin.description }}: ' + resp['result'].length + ' saved item' + (resp['result'].length > 1 ? 's' : '')));
				tr.appendChild(th);
				table.appendChild(tr);

				tr = document.createElement('tr');
				var header = ['Date', 'User', 'Name', 'Description', 'Action'];
				for (var k=0; k < header.length; k++) {
					th = document.createElement('th');
					th.appendChild(document.createTextNode(header[k]));
					tr.appendChild(th);
				}
				table.appendChild(tr);

				var delImg, trid;
				var tabi, tabitr, tabitd;
				for (var k=0; k < resp['result'].length; k++) {
					tr = document.createElement('tr');
					trid = '{{ plugin.id }}_saved_item_' + k + '_tr';
					tr.setAttribute('id', trid);

					// Date
					td = document.createElement('td');
					td.appendChild(document.createTextNode(resp['result'][k]['date']));
					tr.appendChild(td);

					// User
					td = document.createElement('td');
					td.setAttribute('class', 'config');
					td.appendChild(document.createTextNode(resp['result'][k]['username']));
					tr.appendChild(td);

					// Name
					td = document.createElement('td');
					td.setAttribute('class', 'name');
					td.appendChild(document.createTextNode(resp['result'][k]['name']));
					tr.appendChild(td);

					// Description
					td = document.createElement('td');
					td.appendChild(document.createTextNode(resp['result'][k]['descr']));
					tr.appendChild(td);
					
					// Delete
					td = document.createElement('td');
					delImg = document.createElement('img');
					delImg.setAttribute('style', 'margin-right: 5px');
					delImg.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/16x16/delete.gif');
					delImg.setAttribute('onclick', "{{ plugin.id }}_delSavedItem('" + trid + "', '" + resp['result'][k]['name'] + "')");
					td.appendChild(delImg);
					delImg = document.createElement('img');
					delImg.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.gif');
					delImg.setAttribute('onclick', "{{ plugin.id }}_addToCart('" + resp['result'][k]['resultsOutputDir'] + "')");
					td.appendChild(delImg);
					tr.appendChild(td);
	
					table.appendChild(tr);
				}

				if (resp['result'].length) {
					div.appendChild(table);
				}
				else {
                    div.appendChild(icon);
                    div.appendChild(document.createTextNode('  : no saved item'));
				}
			}
	);

	var post = 	'Plugin={{ plugin.id }}&Method=getSavedItems';
	r.send('/youpi/process/plugin/', post);
}

function {{ plugin.id }}_delSavedItem(trid, name) {
	var r = confirm("Are you sure you want to delete saved item '" + name + "'?");
	if (!r) return;

	var trNode = document.getElementById(trid);
	var reload = false;

	var r = new HttpRequest(
			'{{ plugin.id}}_result',
			null,	
			// Custom handler for results
			function(resp) {
				// 3 = 2 rows of header + 1 row of data
				if (trNode.parentNode.childNodes.length == 3)
					reload = true;
	
				if (reload) 
					window.location.reload();
				else
					trNode.parentNode.removeChild(trNode);
			}
	);

	var post = 	'Plugin={{ plugin.id }}&Method=deleteCartItem&Name=' + name;
	r.send('/youpi/process/plugin/', post);
}

function {{ plugin.id }}_addToCart(resultsOutputDir) {
	var p_data = {	plugin_name : '{{ plugin.id }}', 
					userData : {'resultsOutputDir' : resultsOutputDir}
	};

	s_cart.addProcessing(p_data,
			// Custom hanlder
			function() {
				window.location.reload();
			}
	);
}
