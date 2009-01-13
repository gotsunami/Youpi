// JS code for Sextractor plugin

// Global vars
var {{ plugin.id }}_ims;
var {{ plugin.id }}_gNextPage = 1;
var {{ plugin.id }}_fm_file_browser;

var {{ plugin.id }} = {
	viewImageList: function(container_id, idList) {
		idList = idList.split(',');
		var div = document.getElementById(container_id);
		if (div.style.display == 'none') {
			removeAllChildrenNodes(div);
			var indiv = document.createElement('div');
			indiv.appendChild(document.createTextNode('View info for image: '));
			var select = document.createElement('select');
			var option;
			for (var k=0; k < idList.length; k++) {
				option = document.createElement('option');
				option.setAttribute('value', k);
				option.appendChild(document.createTextNode(idList[k]));
				select.appendChild(option);
			}
			indiv.appendChild(select);
			div.appendChild(indiv);
			div.style.display = 'block';
		}
		else
			div.style.display = 'none';
	},

	addSelectionToCart: function() {
		// CHECK 1: checks for images
		sels = {{ plugin.id }}_ims.getListsOfSelections();

		if (!sels) {
			alert('No images selected. Nothing to add to cart !');
			return;
		}

		console.warn('TODO...'); return;

		// CHECK 2: non-empty flag, weight and PSF data paths?

		// MANDATORY PATHS
		// WARNING in Sextractor none of those paths are mandatory

		/*
		var mandvars = {{ plugin.id }}_selector.getMandatoryPrefixes();
		alert(mandvars);
		var mandpaths = new Array();
		for (var k=0; k < mandvars.length; k++) {
			var selNode = document.getElementById('{{ plugin.id }}_' + mandvars[k] + '_select');
			var success = true;
			var path;
			if (!selNode)
				success = false;
			else {
				path = selNode.options[selNode.selectedIndex].text;
				if (path == {{ plugin.id }}_selector.getNoSelectionPattern()) {
					success = false;
				}
				mandpaths.push(path);
			}

			if (!success) {
				alert("No " + mandvars[k] + " path selected for images. Please make a selection in 'Select data paths' menu first.");
				return;
			}
		}
		*/

		// OPTIONAL
		var fSel = document.getElementById('{{plugin.id}}_flags_select');
		var flagPath = '';
		if (fSel) {
			var path = fSel.options[fSel.selectedIndex].text;
			if (path != {{ plugin.id }}_selector.getNoSelectionPattern())
				flagPath = path;
		}

		var wSel = document.getElementById('{{plugin.id}}_weights_select');
		var weightPath = '';
		if (wSel) {
			var path = wSel.options[wSel.selectedIndex].text;
			if (path != {{ plugin.id }}_selector.getNoSelectionPattern())
				weightPath = path;
		}


		var pSel = document.getElementById('{{plugin.id}}_psf_select');
		var psfPath = '';
		if (pSel) {
			var path = pSel.options[pSel.selectedIndex].text;
			if (path != {{ plugin.id }}_selector.getNoSelectionPattern())
				psfPath = path;
		}

		// CHECK 3: get config file
		var cSel = document.getElementById('{{ plugin.id }}_config_name_select');
		var config = cSel.options[cSel.selectedIndex].text;

		// CHECK 4: custom output directory
		var custom_dir = document.getElementById('{{ plugin.id }}_output_path_input').value;
		var output_data_path = '{{ processing_output }}{{ user.username }}/{{ plugin.id }}/';

		if (custom_dir && custom_dir.replace(/\ /g, '').length) {
			custom_dir = custom_dir.replace(/\ /g, '');
			if (custom_dir.length) {
				output_data_path += custom_dir + '/';
			}
		}

		// Finally, add to the shopping cart
		var p_data = {	plugin_name : '{{ plugin.id }}', 
						userData : {'config' : config, 
									'imgList' : sel, 
									'flagPath' : flagPath, 
									'weightPath' : weightPath,
									'psfPath' : psfPath,
									'resultsOutputDir' : output_data_path
						}
		};

		s_cart.addProcessing(	p_data,
								// Custom handler
								function() {
									alert('The current image selection (' + nb + ' ' + (nb > 1 ? 'images' : 'image') + 
										') has been\nadded to the cart.');
								}
		);

	},

	displayImageCount: function(imgList) {
		var c = imgList.split(',').length;
		document.write(c + ' image' + (c > 1 ? 's' : '') + ' to process');
	},

	run: function(trid, silent) {
		var silent = silent == true ? true : false;
		// REQUIRED
		var condorHosts = condorPanel.getSelectedHosts();

		var r = new HttpRequest(
				null,
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

		var post = 'Plugin={{ plugin.id }}&Method=process&CondorHosts=' + condorHosts;
		r.send('/youpi/process/plugin/', post);
	},

	saveItemForLater: function(trid, idList, itemId, flag, weight, psf, resultsOutputDir, config, silent) {
		var prefix = document.getElementById('prefix').value.replace(/ /g, '');
		var r = new HttpRequest(
				'{{ plugin.id}}_result',
				null,	
				// Custom handler for results
				function(resp) {
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
					// Global function (in shoppingcart.html)
					{{ plugin.id }}.showSavedItems();
				}
		);

		var post = 	'Plugin={{ plugin.id }}&Method=saveCartItem&IdList=' + idList + 
					'&ItemID=' + prefix + itemId + 
					'&FlagPath=' + flag +
					'&WeightPath=' + weight + 
					'&PsfPath=' + psf + 
					'&ResultsOutputDir=' + resultsOutputDir + 
					'&Config=' + config;
		r.send('/youpi/process/plugin/', post);
	},

	/*
	 * Displays custom result information. 'resp' contains 
	 * server-side info to display
	 *
	 */
	resultsShowEntryDetails: function(container_id) {
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
	},

	showSavedItems: function() {
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
					icon.setAttribute('style', 'vertical-align: middle; margin-right: 10px');

					tr = document.createElement('tr');
					th = document.createElement('th');
					th.setAttribute('colspan', '8');
					th.appendChild(icon);
					th.appendChild(document.createTextNode('{{ plugin.description }}: ' + resp['result'].length + ' saved item' + (resp['result'].length > 1 ? 's' : '')));
					tr.appendChild(th);
					table.appendChild(tr);

					tr = document.createElement('tr');
					var header = ['Date', 'User', 'Name', '# images', 'Config', 'Paths', 'Action'];
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
						tr.setAttribute('id',trid);

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
						td.appendChild(document.createTextNode(resp['result'][k]['idList'].length));
						tr.appendChild(td);

						// Config
						td = document.createElement('td');
						td.setAttribute('class', 'config');
						td.appendChild(document.createTextNode(resp['result'][k]['config']));
						tr.appendChild(td);

						// Flag, Weight, Psf
						td = document.createElement('td');
						tabi = document.createElement('table');
						tabi.setAttribute('class', 'info');

						// Flag
						tabitr = document.createElement('tr');
						tabitd = document.createElement('td');
						tabitd.appendChild(document.createTextNode('Flag: '));
						tabitd.setAttribute('class', 'label');
						tabitr.appendChild(tabitd);
						tabitd = document.createElement('td');
						tabitd.setAttribute('class', 'file');
						if (resp['result'][k]['flagPath'].length > 0)
							tabitd.appendChild(reduceString(resp['result'][k]['flagPath']));
						else
							tabitd.appendChild(document.createTextNode('Not specified'));
						tabitr.appendChild(tabitd);
						tabi.appendChild(tabitr);

						// Weight
						tabitr = document.createElement('tr');
						tabitd = document.createElement('td');
						tabitd.appendChild(document.createTextNode('Weight: '));
						tabitd.setAttribute('class', 'label');
						tabitr.appendChild(tabitd);
						tabitd = document.createElement('td');
						tabitd.setAttribute('class', 'file');
						if (resp['result'][k]['weightPath'].length > 0)
							tabitd.appendChild(reduceString(resp['result'][k]['weightPath']));
						else
							tabitd.appendChild(document.createTextNode('Not specified'));
						tabitr.appendChild(tabitd);
						tabi.appendChild(tabitr);

						// Psf
						tabitr = document.createElement('tr');
						tabitd = document.createElement('td');
						tabitd.appendChild(document.createTextNode('PSF: '));
						tabitd.setAttribute('class', 'label');
						tabitr.appendChild(tabitd);
						tabitd = document.createElement('td');
						tabitd.setAttribute('class', 'file');
						if (resp['result'][k]['psfPath'].length > 0)
							tabitd.appendChild(reduceString(resp['result'][k]['psfPath']));
						else
							tabitd.appendChild(document.createTextNode('Not specified'));
						tabitr.appendChild(tabitd);
						tabi.appendChild(tabitr);
						td.appendChild(tabi);
						tr.appendChild(td);

						// Delete
						td = document.createElement('td');
						delImg = document.createElement('img');
						delImg.setAttribute('style', 'margin-right: 5px');
						delImg.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/misc/delete.gif');
						delImg.setAttribute('onclick', "{{ plugin.id }}.delSavedItem('" + trid + "', '" + resp['result'][k]['name'] + "')");
						td.appendChild(delImg);
						delImg = document.createElement('img');
						delImg.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.gif');
						delImg.setAttribute('onclick', "{{ plugin.id }}.addToCart('" + 
								resp['result'][k]['idList'] + "','" + 
								resp['result'][k]['config'] + "','" + 
								resp['result'][k]['flagPath'] + "','" +
								resp['result'][k]['weightPath'] + "','" +
								resp['result'][k]['psfPath'] + "','" +
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
	},

	addToCart: function(idList, config, flagPath, weightPath, psfPath, resultsOutputDir) {
		var p_data = {	plugin_name : '{{ plugin.id }}', 
						userData :{	'config' : config,
									'imgList' : idList,
									'flagPath' : flagPath,
									'weightPath' : weightPath,
									'psfPath' : psfPath,
									'resultsOutputDir' : resultsOutputDir
						}
		};

		s_cart.addProcessing(p_data,
				// Custom hanlder
				function() {
					window.location.reload();
				}
		);
	},

	delSavedItem: function(trid, name) {
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
	},

	getTabId: function(ul_id) {
		// Looking for tab's id
		//var ul = document.getElementById('tabnav2');
		var ul = document.getElementById(ul_id);
		var lis = ul.getElementsByTagName('li');
		var i=0;
		for (i=0; i < lis.length; i++) {
			if (lis[i].getAttribute('class') == 'enabled') {
				break;
			}
		}

		return i;
	},

	selectImages: function() {
		var root = document.getElementById('menuitem_sub_0');
		root.setAttribute('align', 'center');
		// Container of the ImageSelector widget
		var div = document.createElement('div');
		div.setAttribute('id', '{{ plugin.id }}_results_div');
		div.setAttribute('align', 'center');
		div.setAttribute('style', 'padding-top: 20px; width: 80%');
		root.appendChild(div);

		{{ plugin.id }}_ims = new ImageSelector('{{ plugin.id }}_results_div');
		{{ plugin.id }}_advTab = new AdvancedTable();
		{{ plugin.id }}_ims.setTableWidget({{ plugin.id }}_advTab);

		// Sets a custom result handler in order to deselect all entries
		{{ plugin.id }}_ims.setResultHandler(
			function(idList, output) {
				{{ plugin.id }}_ims.getDefaultResultHandler()(idList, output, 
					function() {
						{{ plugin.id }}_ims.unselectAll();
					}
				);
			}
		);
	},

	// container_id is a td containing the cancel button
	cancelJob: function(container_id, clusterId, procId) {
		var r = new HttpRequest(
			'container_id',
			null,
			// Custom handler for results
			function(resp) {
				var container = document.getElementById(container_id);
				container.setAttribute('style', 'color: red');
				r = resp['result'];
				container.innerHTML = getLoadingHTML('Cancelling job');
			}
		);

		var post = 'Plugin={{ plugin.id }}&Method=cancelJob&ClusterId=' + clusterId + '&ProcId=' + procId;
		r.send('/youpi/process/plugin/', post);
	},

	doit: function() {
		{{ plugin.id }}.selectImages();
	}
};
