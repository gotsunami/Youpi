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

// Global vars
var ims;
var advTable;
var ldac_table;
var ldac_table_active_selections = new Array();
var ldac_selection_last_idx;

// Used in checkForSelectionLDACData()
var {{ plugin.id }}_curSelectionIdx = 0;
var {{ plugin.id }}_LDAC_error = 0;


/*
 * Function: addSelectionToCart
 *
 */
function {{ plugin.id }}_addSelectionToCart() {
	// Global var
	{{ plugin.id }}_curSelectionIdx = 0;
	{{ plugin.id }}_LDAC_error = 0;

	var container = emptyContainer('menuitem_sub_5');
	var pre = document.createElement('pre');
	container.appendChild(pre);

	var log = new Logger(pre);

	// CHECK 1: list of selections check
	log.msg_status('Please note that these tests DO NOT CHECK that LDAC files are available on disks!');
	log.msg_status('Checking list of selections...');

	sels = ims.getListsOfSelections();
	if (!sels) {
		log.msg_error('No images selected. Nothing to add to cart !');
		return;
	}

	var total = ims.getImagesCount();
	log.msg_ok('Found ' + total + ' image' + (total > 1 ? 's' : '') + ' in selection.');

	// CHECK 2: get config file
	var cSel = document.getElementById('{{ plugin.id }}_config_name_select');
	var config = cSel.options[cSel.selectedIndex].text;
	log.msg_status("Using '" + config + "' as configuration file");

	// CHECK 3: custom output directory
	var output_data_path = {{ plugin.id }}_getOutputDataPath();
	log.msg_status("Using output data path '" + output_data_path + "'");

	// CHECK 4: do images in selection(s) have LDAC data?
	log.msg_status("Deeper selection(s) checks for LDAC data...");
	{{ plugin.id }}_checkForSelectionLDACData(pre);
}

function {{ plugin.id }}_getOutputDataPath() {
	var custom_dir = document.getElementById('output_path_input').value;
	var output_data_path = '{{ processing_output }}{{ user.username }}/{{ plugin.id }}/';

	if (custom_dir && custom_dir.replace(/\ /g, '').length) {
		custom_dir = custom_dir.replace(/\ /g, '');
		if (custom_dir.length) {
			output_data_path += custom_dir + '/';
		}
	}

	return output_data_path;
}

/*
 * Function: checkForSelectionLDACData
 * Check if every images in that selection has associated LDAC data
 *
 * Parameters:
 *
 * container - DOM element: DOM block container
 *
 */ 
function {{ plugin.id }}_checkForSelectionLDACData(container) {
	var div = document.createElement('div');
	var log = new Logger(div);
	var sels = ims.getListsOfSelections();
	var total = ims.getImagesCount();
	var selArr = eval(sels);
	var idList = selArr[{{ plugin.id }}_curSelectionIdx];

	div.setAttribute('style', 'color: brown; text-align: left;');
	container.appendChild(div);

	var r = new HttpRequest(
			div,
			null,	
			// Custom handler for results
			function(resp) {
				div.innerHTML = '';
				missing = resp['result']['missingLDACImages'];

				if (missing.length > 0) {
					log.msg_warning('Missing LDAC data for selection ' + ({{ plugin.id }}_curSelectionIdx+1) + 
						' (' + missing.length + ' image' + (missing.length > 1 ? 's' : '') + ' failed!)');
					{{ plugin.id }}_LDAC_error = 1;
				}	
				else {
					log.msg_ok('LDAC data for selection ' + ({{ plugin.id }}_curSelectionIdx+1) + 
						' (' + idList.length + ' image' + (idList.length > 1 ? 's' : '') + ') is OK');
				}

				{{ plugin.id }}_curSelectionIdx++;

				if ({{ plugin.id }}_curSelectionIdx < selArr.length) {
					{{ plugin.id }}_checkForSelectionLDACData(container);
				}
				else {
					if ({{ plugin.id }}_LDAC_error) {
						log.msg_error('Missing LDAC information. Selection(s) not added to cart!');
						return;
					}

					// Now LDAC fine-grain selection can take place
					var r = confirm('Do you want to manually refine LDAC selections? If not, the current\nselections will be added ' +
									'to the cart now for processing.');
					if (r) {
						log.msg_status('Please select the LDAC files you want to use for scamp processing');
						{{ plugin.id }}_manualLDACSelection(div);
						
						return;
					}

					{{ plugin.id }}_do_addSelectionToCart(sels);
				}
			}
	);

	var post = 	'Plugin={{ plugin.id }}&' + 
				'Method=checkForSelectionLDACData&' +
				'IdList=' + idList;
	// Send query
	r.setBusyMsg('Checking selection ' + ({{ plugin.id }}_curSelectionIdx+1) + ' (' + idList.length + ' images)');
	r.send('/youpi/process/plugin/', post);
}

function {{ plugin.id }}_do_addSelectionToCart(selIds) {
	var cSel = document.getElementById('{{ plugin.id }}_config_name_select');
	var config = cSel.options[cSel.selectedIndex].text;
	var output_data_path = {{ plugin.id }}_getOutputDataPath();

	if (!selIds) {
		// Manual selections, needs to buid an appropriate selection
		var sels = ims.getListsOfSelections();
		var selArr = eval(sels);
		selIds = '[';
		for (var k=0; k < selArr.length; k++) {
			if (ldac_table_active_selections[k] == '-1')
				// Selection untouched
				selIds += '[' + String(selArr[k]) + '],';
			else {
				// Selection manually changed
				var s = ldac_table_active_selections[k].split(',');
				selIds += '[';
				for (var j=0; j < s.length; j++) {
					selIds += s[j].substr(ldac_table.getRowIdPrefix().length, s[j].length) + ',';
				}
				selIds = selIds.substr(0, selIds.length-1) + '],';
			}
		}
		selIds = selIds.substr(0, selIds.length-1) + ']';
	}

	var tmp = eval(selIds);
	var totalSels = tmp.length;
	var totalImgs = 0;
	for (var k=0; k < totalSels; k++)
		totalImgs += tmp[k].length;

	// Finally, add to the shopping cart
	p_data = {	'plugin_name' 	: 	'{{ plugin.id }}', 
				'userData' 		: 	"{'config' : '" + config + 
									"', 'imgList' : '" + selIds + 
									"', 'resultsOutputDir' : '" + output_data_path +
									"'}" };

	// Add entry into the shopping cart
	s_cart.addProcessing(	p_data,
							// Custom handler
							function() {
								msg = totalSels + ' selection' + (totalSels > 1 ? 's' : '') + ' (' + totalImgs + 
									' image' + (totalImgs > 1 ? 's' : '') + ') ha' + (totalSels > 1 ? 've' : 's') + ' been\nadded to the cart.';
								alert(msg);
							}
	);
}

function {{ plugin.id }}_manualLDACSelection(container) {
	var sels = ims.getListsOfSelections();
	var selArr = eval(sels);
	ldac_selection_last_idx = 0;

	ldac_table = new AdvancedTable('ldac_table');
	ldac_table.setContainer('ldac_selection_div');
	ldac_table.setHeaders(['LDAC files to use']);
	ldac_table.setRowIdsFromColumn(0);
	ldac_table.attachEvent('onRowClicked', 
		function(checked) { 
			{{ plugin.id }}_LDACSaveCurrentSelection();
		}
	);

	var options = new Array();
	for (var k=0; k < selArr.length; k++) {
		options[k] = 'Selection ' + (k+1) + ' (' + selArr[k].length + ')';
		// Init
		ldac_table_active_selections[k] = -1;
	}
	var selNode = getSelect('ldac_current_select', options, 10);
	selNode.setAttribute('style', 'width: 100%;');

	var opt;
	for (var k=0; k < selArr.length; k++) {
		opt = selNode.childNodes[k];
		opt.setAttribute('onclick', "{{ plugin.id }}_renderLDACSelection(" + parseInt(k) + ")");
	}
	
	var ldac_tab = document.createElement('table');
	ldac_tab.setAttribute('style', 'width: 100%;');
	var tr, td;
	tr = document.createElement('tr');
	td = document.createElement('td');

	ldac_tab.appendChild(tr);
	tr.appendChild(td);
	container.appendChild(ldac_tab);

	var ldac_choice_div = document.createElement('div');
	ldac_choice_div.appendChild(selNode);
	td.appendChild(ldac_choice_div);

	var ldac_opt_div = document.createElement('div');
	ldac_opt_div.setAttribute('style', 'vertical-align: middle;');
	td.appendChild(ldac_opt_div);

	// Select all
	var sub = document.createElement('input');
	sub.setAttribute('style', 'float: left;');
	sub.setAttribute('type', 'button');
	sub.setAttribute('value', 'Select all');
	sub.setAttribute('onclick', 'ldac_table.selectAll(true); {{ plugin.id }}_LDACSaveCurrentSelection();');
	ldac_opt_div.appendChild(sub);
		
	// Unselect all
	sub = document.createElement('input');
	sub.setAttribute('style', 'float: left; margin-left: 10px;');
	sub.setAttribute('type', 'button');
	sub.setAttribute('value', 'Unselect all');
	sub.setAttribute('onclick', 'ldac_table.selectAll(false); {{ plugin.id }}_LDACSaveCurrentSelection();');
	ldac_opt_div.appendChild(sub);

	// Add to cart button
	var addc = document.createElement('img');
	addc.setAttribute('style', 'cursor: pointer; float: right;');
	addc.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/misc/add_to_cart.gif');
	addc.setAttribute('onclick', "{{ plugin.id }}_do_addSelectionToCart();");
	ldac_opt_div.appendChild(addc);
		
	td = document.createElement('td');
	var ldac_selection_div = document.createElement('div');
	ldac_selection_div.setAttribute('id', 'ldac_selection_div');
	td.appendChild(ldac_selection_div);
	tr.appendChild(td);
	
	{{ plugin.id }}_renderLDACSelection(0);
}

function {{ plugin.id }}_LDACSaveCurrentSelection() {
	var idSel = ldac_table.getSelectedRows();
	if (idSel) {
		idSel = idSel.split(',');
		for (var k=0; k < idSel.length; k++) {
			idSel[k] = ldac_table.getRowIdPrefix() + idSel[k];
		}
		ldac_table_active_selections[ldac_selection_last_idx] = String(idSel);
	}
	else
		ldac_table_active_selections[ldac_selection_last_idx] = '';
}

function {{ plugin.id }}_renderLDACSelection(idx) {
	var sels = ims.getListsOfSelections();
	var selArr = eval(sels);

	if (typeof idx != 'number') {
		alert('renderLDACSelection: idx must be an integer!');
		return;
	}

	// Save current selection status (thus it can be restaured later)
	if (ldac_table.rowCount())
		{{ plugin.id }}_LDACSaveCurrentSelection();

	ldac_selection_last_idx = idx;

	var container = ldac_table.getContainer();
	var xhr = new HttpRequest(
			container,
			null,	
			// Custom handler for results
			function(resp) {
				var d = resp['result'];

				container.innerHTML = '';
				ldac_table.empty();

				for (var k=0; k < d.length; k++) {
					ldac_table.appendRow([d[k][0], String(d[k][1])]);
				}

				ldac_table.render();

				// Restore selected rows?
				var cur_sel = ldac_table_active_selections[idx];
				if (cur_sel == -1)
					ldac_table.selectAll(true);
				else if (typeof cur_sel == 'string')
					ldac_table.setSelectedRows(cur_sel);
			}
	);

	var post = 'Plugin={{ plugin.id }}&Method=getLDACPathsFromImageSelection&IdList=' + selArr[idx];
	xhr.send('/youpi/process/plugin/', post);
}

/*
 * scampId allows to retreive config file by content (not by name) when reprocessing data
 *
 */
function {{ plugin.id }}_run(trid, idList, itemId, config, resultsOutputDir, scampId, silent) {
	var silent = silent == true ? true : false;
	var scampId = scampId ? scampId : '';
	var condorHosts = condorPanel.getSelectedHosts();
	var prefix = document.getElementById('prefix').value.replace(/ /g, '');
	var txt = '';

	if (condorHosts.length == 0) {
		alert('Please select at least a node on the cluster in the Condor panel on the left.');
		return;
	}

	if (prefix.length == 0)
		txt = ' Also please note that no custom prefix name has been defined.';
	else 
		txt = " Please note that you have defined a custom '" + prefix + "' prefix that will be used when items get submitted.";

	if (!silent) {
		var r = confirm('Are you sure you want to submit this item to the cluster?' + txt);
		if (!r) return;
	}

	var r = new HttpRequest(
			'{{ plugin.id }}_result',
			null,	
			// Custom handler for results
			function(resp) {
				if (resp['result']['count'] == -1) {
					alert('An error occured. Unable to submit jobs to Condor.');
					return;
				}
				if (!silent)
					alert('Done. Sent to cluster: ' + resp['result']['clusterId']);

				// Silently remove item from the cart
				removeItemFromCart(trid, true);
			}
	);

	var post = 	'Plugin={{ plugin.id }}&Method=process&IdList=' + idList + 
				'&ItemId=' + prefix + itemId + 
				'&CondorHosts=' + condorHosts + 
				'&ScampId=' + scampId + 
				'&ResultsOutputDir=' + resultsOutputDir + 
				'&Config=' + config;
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

function {{ plugin.id }}_saveItemForLater(trid, idList, itemId, resultsOutputDir, config) {
	var prefix = document.getElementById('prefix').value.replace(/ /g, '');
	var r = new HttpRequest(
			'result',
			null,	
			// Custom handler for results
			function(resp) {
				// Silently remove item from the cart
				removeItemFromCart(trid, true);
				// Global function (in shoppingcart.html)
				showSavedItems();
			}
	);

	var post = 	'Plugin={{ plugin.id }}' + 
				'&Method=saveCartItem' +
				'&IdList=' + idList + 
				'&ItemID=' + prefix + itemId + 
				'&ResultsOutputDir=' + resultsOutputDir + 
				'&Config=' + config;
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
	// Global variable
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
	d.appendChild(tab);
	container.appendChild(d);

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
	img.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif');
	img.setAttribute('style', 'padding-right: 5px;');
	tdiv.appendChild(img);
	tdiv.appendChild(document.createTextNode(resp['Duration'] + ' on'));
	tdiv.appendChild(document.createElement('br'));
	tdiv.appendChild(document.createTextNode(resp['Hostname']));
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
	tab2.setAttribute('class', 'scamp-result-entry-params');
	td.appendChild(tab2);
	tr.appendChild(td);
	tab.appendChild(tr);

	// Thumbnails when successful
	if (resp['Success']) {
		tr = document.createElement('tr');
		tr.setAttribute('class', 'scamp-result-entry-tn');
		td = document.createElement('td');
		td.setAttribute('onclick', "window.open('" + resp['WWW'] + "/scamp.xml');");
		td.setAttribute('onmouseover', "this.setAttribute('class', 'scamp-result-entry-complete-on');");
		td.setAttribute('onmouseout', "this.setAttribute('class', 'scamp-result-entry-complete-off');");
		td.setAttribute('class', 'scamp-result-entry-complete-off');
		td.appendChild(document.createTextNode('See Scamp XML file'));
		tr.appendChild(td);

		td = document.createElement('td');
		var tns = resp['Previews'];
		var tn, imgpath;
		for (var k=0; k < tns.length; k++) {
			imgpath = resp['WWW'] + tns[k];
			tn = document.createElement('img');
			tn.setAttribute('src', imgpath);
			if (!resp['HasThumbnails']) {
				tn.setAttribute('width', '60px');
				tn.setAttribute('onclick', "window.open('" + imgpath + "');");
			}
			else
				tn.setAttribute('onclick', "window.open('" + imgpath.replace(/tn_/, '') + "');");
			tn.setAttribute('class', 'scamp-result-entry-tn');
			td.appendChild(tn);
		}
		tr.appendChild(td);
		tab2.appendChild(tr);
	}

	// Scamp processing history
	// Header title
	var hist = resp['History'];
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	td.setAttribute('class', 'qfits-result-header-title');
	td.appendChild(document.createTextNode('Scamp processing history (' + hist.length + ')'));
	tr.appendChild(td);
	tab2.appendChild(tr);

	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	htab = document.createElement('table');
	htab.setAttribute('class', 'qfits-result-history');
	td.appendChild(htab);
	tr.appendChild(td);
	tab2.appendChild(tr);

	for (var k=0; k < hist.length; k++) {
		tr = document.createElement('tr');
		// Emphasis of current history entry
		if (resp['TaskId'] == hist[k]['TaskId']) {
			tr.setAttribute('class', 'history-current');
		}

		// Icon
		td = document.createElement('td');
		var src = hist[k]['Success'] ? 'success' : 'error';
		var img = document.createElement('img');
		img.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif');
		td.appendChild(img);
		tr.appendChild(td);

		// Date-time, duration
		td = document.createElement('td');
		var a = document.createElement('a');
		a.setAttribute('href', '/youpi/results/{{ plugin.id }}/' + hist[k]['TaskId'] + '/');
		a.appendChild(document.createTextNode(hist[k]['Start'] + ' (' + hist[k]['Duration'] + ')'));
		td.appendChild(a);
		tr.appendChild(td);

		// Hostname
		td = document.createElement('td');
		td.appendChild(document.createTextNode(hist[k]['Hostname']));
		tr.appendChild(td);

		// User
		td = document.createElement('td');
		td.appendChild(document.createTextNode(hist[k]['User']));
		tr.appendChild(td);

		// Reprocess option
		td = document.createElement('td');
		td.setAttribute('class', 'reprocess');
		img = document.createElement('img');
		img.setAttribute('onclick', "{{ plugin.id }}_reprocess_image('" + hist[k]['FitsinId'] + "');");
		img.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/misc/reprocess.gif');
		td.appendChild(img);
		tr.appendChild(td);

		htab.appendChild(tr);
	}

	// Scamp run parameters
	// Image
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	td.setAttribute('class', 'qfits-result-header-title');
	td.appendChild(document.createTextNode('Scamp run parameters'));
	tr.appendChild(td);
	tab2.appendChild(tr);

	tr = document.createElement('tr');
	td = document.createElement('td');
	td.appendChild(document.createTextNode('Input LDAC files (' + resp['LDACFiles'].length + '):'));
	tr.appendChild(td);

	td = document.createElement('td');
	var ldac_div = document.createElement('div');
	ldac_div.setAttribute('style', 'height: 100px; overflow: auto; width: 500px;');
	td.appendChild(ldac_div);
	for (var k=0; k < resp['LDACFiles'].length; k++) {
		ldac_div.appendChild(document.createTextNode(resp['LDACFiles'][k]));
		ldac_div.appendChild(document.createElement('br'));
	}
	tr.appendChild(td);
	tab2.appendChild(tr);

	// Output directory
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('nowrap', 'nowrap');
	td.appendChild(document.createTextNode('Results output dir:'));
	tr.appendChild(td);

	td = document.createElement('td');
	td.appendChild(document.createTextNode(resp['ResultsOutputDir']));
	tr.appendChild(td);
	tab2.appendChild(tr);

	// Scamp Config file
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	if (resp['Success']) {
		td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
	}
	var but = document.createElement('input');
	but.setAttribute('type', 'button');
	but.setAttribute('value', 'Toggle Scamp config file view');
	but.setAttribute('onclick', "toggleDisplay('config-" + resp['TaskId'] + "');");
	td.appendChild(but);
	var cdiv = document.createElement('div');
	cdiv.setAttribute('id', 'config-' + resp['TaskId']);
	cdiv.setAttribute('style', 'height: 300px; overflow: auto; background-color: black; padding-left: 5px; display: none; width: 550px;')
	var pre = document.createElement('pre');
	pre.appendChild(document.createTextNode(resp['Config']));
	cdiv.appendChild(pre);
	td.appendChild(cdiv);
	tr.appendChild(td);
	tab2.appendChild(tr);

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
}

function {{ plugin.id }}_showSavedItems() {
	var cdiv = document.getElementById('saved_items_div');
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
				var table = document.createElement('table');
				table.setAttribute('class', 'savedItems');
				var tr, th;
				var icon = document.createElement('img');
				icon.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/32x32/{{ plugin.id }}' + '.png');
				icon.setAttribute('style', 'vertical-align:middle; margin-right: 10px;');

				tr = document.createElement('tr');
				th = document.createElement('th');
				th.setAttribute('colspan', '8');
				th.appendChild(icon);
				th.appendChild(document.createTextNode('{{ plugin.description }}: ' + resp['result'].length + ' saved item' + (resp['result'].length > 1 ? 's' : '')));
				tr.appendChild(th);
				table.appendChild(tr);

				tr = document.createElement('tr');
				var header = ['Date', 'User', 'Name', '# images', 'Config', 'Action'];
				for (var k=0; k < header.length; k++) {
					th = document.createElement('th');
					th.appendChild(document.createTextNode(header[k]));
					tr.appendChild(th);
				}
				table.appendChild(tr);

				var delImg, trid;
				var tabi, tabitr, tabitd;
				var idList, txt;
				for (var k=0; k < resp['result'].length; k++) {
					idList = eval(resp['result'][k]['idList']);
					tr = document.createElement('tr');
					trid = 'saved_item_' + k + '_tr';
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

					// Images count
					td = document.createElement('td');
					td.setAttribute('class', 'imgCount');
					idList.length > 1 ? txt = 'Batch' : txt = 'Single';
					var sp = document.createElement('span');
					sp.setAttribute('style', 'font-weight: bold; text-decoration: underline;');
					sp.appendChild(document.createTextNode(txt));
					td.appendChild(sp);
					td.appendChild(document.createElement('br'));

					for (var j=0; j < idList.length; j++) {
						td.appendChild(document.createTextNode(idList[j].length));
						td.appendChild(document.createElement('br'));
					}
					tr.appendChild(td);

					// Config
					td = document.createElement('td');
					td.setAttribute('class', 'config');
					td.appendChild(document.createTextNode(resp['result'][k]['config']));
					tr.appendChild(td);

					// Delete
					td = document.createElement('td');
					delImg = document.createElement('img');
					delImg.setAttribute('style', 'margin-right: 5px');
					delImg.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/misc/delete.gif');
					delImg.setAttribute('onclick', "{{ plugin.id }}_delSavedItem('" + trid + "', '" + resp['result'][k]['name'] + "')");
					td.appendChild(delImg);
					delImg = document.createElement('img');
					delImg.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.gif');
					delImg.setAttribute('onclick', "{{ plugin.id }}_addToCart('" + 
							resp['result'][k]['idList'] + "','" + 
							resp['result'][k]['config'] + "','" + 
							resp['result'][k]['resultsOutputDir'] + "')");
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
			'result',
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

function {{ plugin.id }}_addToCart(idList, config, resultsOutputDir) {
	s_cart.addProcessing({	'plugin_name' : '{{ plugin.id }}', 
							'userData' :"{'config' : '" + config + 
										"', 'imgList' : '" + idList + 
										"', 'resultsOutputDir' : '" + resultsOutputDir + "'}"},
			// Custom hanlder
			function() {
				window.location.reload();
			}
	);
}

function selectImages() {
	var root = document.getElementById('menuitem_sub_0');
	root.setAttribute('align', 'center');

	// Container of the ImageSelector widget
	var div = document.createElement('div');
	div.setAttribute('id', 'results_div');
	div.setAttribute('align', 'center');
	div.setAttribute('style', 'padding-top: 20px; width: 80%');
	root.appendChild(div);

	ims = new ImageSelector('results_div', 'ims');
	advTab = new AdvancedTable('advTab');
	ims.setTableWidget(advTab);
}

/*
 * Function {{ plugin.id }}_displayImageCount
 * Renders list of images to be processed as a summary (used in the shopping cart plugin rendering)
 *
 * Parameters:
 *
 * imgList - array of arrays of idLists
 *
 */
function {{ plugin.id }}_displayImageCount(imgList, container_id) {
	var container = document.getElementById(container_id);
	var imgList = eval(imgList);
	var c = 0;
	var txt;
	imgList.length > 1 ? txt = 'Batch' : txt = 'Single';
	var selDiv = document.createElement('div');
	selDiv.setAttribute('class', 'selectionModeTitle');
	selDiv.appendChild(document.createTextNode(txt + ' selection mode:'));
	container.appendChild(selDiv);

	selDiv = document.createElement('div');
	selDiv.setAttribute('class', 'listsOfSelections');

	for (var k=0; k < imgList.length; k++) {
		c = imgList[k].toString().split(',').length;
		if (imgList.length > 1)
			selDiv.appendChild(document.createTextNode('Selection ' + (k+1) + ': ' + c + ' image' + (c > 1 ? 's' : '')));
		else
			selDiv.appendChild(document.createTextNode(c + ' image' + (c > 1 ? 's' : '')));
		selDiv.appendChild(document.createElement('br'));
	}
	container.appendChild(selDiv);
}
