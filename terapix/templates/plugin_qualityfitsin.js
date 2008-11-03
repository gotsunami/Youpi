
// JS code for qualityfits-in plugin

// Global vars
var {{ plugin.id }}_ims;
var {{ plugin.id }}_gNextPage = 1;

function {{ plugin.id }}_viewImageList(container_id, idList) {
//	idList = idList.split(',');

	var idList = eval(idList);
	var c = '';
	for (var k=0; k < idList.length; k++) {
		c += idList[k].toString();
		if (k < idList.length-1) c += ',';
	}
	idList = c.split(',');

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
}

/*
 * fitsinId allows to retreive config file by content (not by name) when reprocessing data
 *
 */
function {{ plugin.id }}_run(trid, idList, itemId, flat, mask, reg, config, resultsOutputDir, fitsinId, silent) {
	var silent = silent == true ? true : false;
	var fitsinId = fitsinId ? fitsinId : '';
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
			'{{ plugin.id}}_result',
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
				'&FlatPath=' + flat +
				'&MaskPath=' + mask + 
				'&RegPath=' + reg + 
				'&CondorHosts=' + condorHosts + 
				'&FitsinId=' + fitsinId + 
				'&ResultsOutputDir=' + resultsOutputDir + 
				'&Config=' + config;
	r.send('/youpi/process/plugin/', post);
}

var {{ plugin.id }}_itemIdx = 0;
function {{ plugin.id }}_sendAll(data) {
	var r = new HttpRequest(
			'{{ plugin.id}}_result',
			null,	
			// Custom handler for results
			function(resp) {
				// removeItemFromCart(data[p][0], true);
				{{ plugin.id }}_itemIdx++;
				if ({{ plugin.id }}_itemIdx < data.length) {
					{{ plugin.id }}_sendAll(data);
				}
				else {
					// Delete all items for that plugin
					s_cart.deleteAllPluginItems(
						'{{ plugin.id }}',
						// Custom handler called when all items are deleted
						function() {
							alert('All jobs sent to cluster');
							window.location.reload();
						}
					);
				}
			}
	);
	var post = 'Plugin={{ plugin.id }}&Method=process&IdList=' + 
				data[{{ plugin.id }}_itemIdx][1] + '&ItemID=' + data[{{ plugin.id }}_itemIdx][2];
	r.send('/youpi/process/plugin/', post);
}

function {{ plugin.id }}_runAll() {
	var prefix = document.getElementById('prefix').value.replace(/ /g, '');
	var txt = '';
	if (prefix.length == 0)
		txt = ' Also please note that no custom prefix name has been defined.';
	else 
		txt = " Please note that you have defined a custom '" + prefix + "' prefix that will be used when items get submitted.";

	var r = confirm('Are you sure you want to submit ALL items to the cluster?' + txt);
	if (!r) return;

	var trNode;
	var j=0;
	data = new Array();

	{% for data in plugin.getData %}
		trNode = document.getElementById('{{ plugin.id }}_' + (j+1));
		data[j] = [trNode, '{{ data.idList }}', prefix + '{{ plugin.itemPrefix }}{{ data.itemCounter }}'];
		j++;
	{% endfor %}

	{{ plugin.id }}_sendAll(data);
}

// Mandatory function
function {{ plugin.id }}_saveItemForLater(trid, idList, itemId, flat, mask, reg, resultsOutputDir, config, silent) {
	var prefix = document.getElementById('prefix').value.replace(/ /g, '');
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

	var post = 	'Plugin={{ plugin.id }}' + 
				'&Method=saveCartItem' + 
				'&IdList=' + idList + 
				'&ItemID=' + prefix + itemId + 
				'&FlatPath=' + flat +
				'&MaskPath=' + mask + 
				'&RegPath=' + reg + 
				'&ResultsOutputDir=' + resultsOutputDir + 
				'&Config=' + config;
	r.send('/youpi/process/plugin/', post);
}

// Mandatory function
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
				icon.setAttribute('style', 'vertical-align: middle; margin-right: 10px;');

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
				var idList, txt;
				for (var k=0; k < resp['result'].length; k++) {
					idList = eval(resp['result'][k]['idList']);
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

					// Flat, Mask, Reg
					td = document.createElement('td');
					tabi = document.createElement('table');
					tabi.setAttribute('class', 'info');

					// Flat
					tabitr = document.createElement('tr');
					tabitd = document.createElement('td');
					tabitd.appendChild(document.createTextNode('Flat: '));
					tabitd.setAttribute('class', 'label');
					tabitr.appendChild(tabitd);
					tabitd = document.createElement('td');
					tabitd.setAttribute('class', 'file');
					tabitd.appendChild(reduceString(resp['result'][k]['flatPath']));
					tabitr.appendChild(tabitd);
					tabi.appendChild(tabitr);

					// Mask
					tabitr = document.createElement('tr');
					tabitd = document.createElement('td');
					tabitd.appendChild(document.createTextNode('Mask: '));
					tabitd.setAttribute('class', 'label');
					tabitr.appendChild(tabitd);
					tabitd = document.createElement('td');
					tabitd.setAttribute('class', 'file');
					tabitd.appendChild(reduceString(resp['result'][k]['maskPath']));
					tabitr.appendChild(tabitd);
					tabi.appendChild(tabitr);

					// Reg
					tabitr = document.createElement('tr');
					tabitd = document.createElement('td');
					tabitd.appendChild(document.createTextNode('Region: '));
					tabitd.setAttribute('class', 'label');
					tabitr.appendChild(tabitd);
					tabitd = document.createElement('td');
					tabitd.setAttribute('class', 'file');
					if (resp['result'][k]['regPath'].length > 0)
						tabitd.appendChild(reduceString(resp['result'][k]['regPath']));
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
					delImg.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/misc/delete.gif');
					delImg.setAttribute('onclick', "{{ plugin.id }}_delSavedItem('" + trid + "', '" + resp['result'][k]['name'] + "')");
					td.appendChild(delImg);
					delImg = document.createElement('img');
					delImg.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.gif');
					delImg.setAttribute('onclick', "{{ plugin.id }}_addToCart('" + 
							resp['result'][k]['idList'] + "','" + 
							resp['result'][k]['config'] + "','" + 
							resp['result'][k]['flatPath'] + "','" +
							resp['result'][k]['maskPath'] + "','" +
							resp['result'][k]['regPath'] + "','" +
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

function {{ plugin.id }}_addToCart(idList, config, flatPath, maskPath, regPath, resultsOutputDir) {
	s_cart.addProcessing({	'plugin_name' : '{{ plugin.id }}', 
							'userData' :"{'config' : '" + config + 
										"', 'imgList' : '" + idList + 
										"', 'flatPath' : '" + flatPath + 
										"', 'maskPath' : '" + maskPath + 
										"', 'regPath' : '" + regPath +
										"', 'resultsOutputDir' : '" + resultsOutputDir + "'}"},
			// Custom hanlder
			function() {
				window.location.reload();
			}
	);
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

// Units are in data[z][2], if any
function {{ plugin.id }}_getDynTable(data, numcols) {
	var itab = document.createElement('table');
	itab.setAttribute('style', 'width: 100%');
	var itr, itd;
	var icols = numcols;
	var irows = Math.floor(data.length/icols);
	var c = 1;
	itr = document.createElement('tr');
	itab.appendChild(itr);
	for (var z=0; z < data.length; z++) {
		itd = document.createElement('td');
		itd.setAttribute('nowrap', 'nowrap');
		var span = document.createElement('span');
		span.setAttribute('style', 'color: brown');
		var cap  = data[z][0] + ': ';
		span.appendChild(document.createTextNode(cap));
		itd.appendChild(span);
		cap = data[z][1];
		if (data[z][2] && cap != 'None') cap += ' ' + data[z][2];
		if (cap == 'None') cap = '-';
		itd.appendChild(document.createTextNode(cap));
		itr.appendChild(itd);
		c++;
		if (c > icols) {
			itr = document.createElement('tr');
			itab.appendChild(itr);
			c = 1;
		}
	}

	return itab;
}


/*
 * Schedule an image reprocessing by adding a new item in the shopping cart.
 *
 */
function {{ plugin.id }}_reprocess_image(fitsinId) {
	var r = new HttpRequest(
			null,
			null,	
			// Custom handler for results
			function(resp) {
				data = resp['result'];
				p_data = {	'plugin_name' : '{{ plugin.id }}', 
							'userData' : "{'config' : 'The one used for the last processing" +
							"', 'fitsinId' : '" + fitsinId + 
							"', 'imgList' : '" + data['ImageId'] + 
							"', 'flatPath' : '" + data['Flat'] + 
							"', 'maskPath' : '" + data['Mask'] + 
							"', 'regPath' : '" + data['Reg'] +
							"', 'resultsOutputDir' : '" + data['ResultsOutputDir'] +
							"'}" };

				s_cart.addProcessing(
						p_data,
						// Custom handler
						function() {
							alert('The current image has been scheduled for reprocessing. \nAn item has been added to the shopping cart.');
						}
				);
			}
	);

	var post = 'Plugin={{ plugin.id }}&Method=getReprocessingParams&FitsinId=' + fitsinId;
	r.send('/youpi/process/plugin/', post);
}

/*
 * Displays custom result information for qfits processing. 'resp' contains 
 * server-side info to display
 *
 */
function {{ plugin.id }}_resultsShowEntryDetails(container_id) {
	var tr, th, td;
	// See templates/results.html, function showDetails(...)
	// currentReturnedData: global variable
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

	// Grading
	if (resp['Success']) {
		var gdiv = document.createElement('div');
		var a = document.createElement('a');
		if (resp['GradingCount'] > 0) {
			gdiv.setAttribute('class', 'notgraded');
			a.setAttribute('href', "/youpi/grading/{{ plugin.id }}/" + resp['FitsinId'] + '/');
			a.appendChild(document.createTextNode('Image graded ' + resp['GradingCount'] + ' time' + (resp['GradingCount'] > 1 ? 's' : '')));
			gdiv.appendChild(a);
		}
		else {
			gdiv.setAttribute('class', 'notgraded');
			gdiv.appendChild(document.createTextNode('Image not graded yet'));
			gdiv.appendChild(document.createElement('br'));
			a.setAttribute('href', "/youpi/grading/{{ plugin.id }}/" + resp['FitsinId'] + '/');
			a.appendChild(document.createTextNode('Grade it now !'));
			gdiv.appendChild(a);
		}
		td.appendChild(gdiv);
	}

	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('style', 'padding: 0px');
	var tab2 = document.createElement('table');
	tab2.setAttribute('class', 'qfits-result-entry-params');
	td.appendChild(tab2);
	tr.appendChild(td);
	tab.appendChild(tr);

	// Thumbnails when successful
	if (resp['Success']) {
		tr = document.createElement('tr');
		tr.setAttribute('class', 'qfits-result-entry-tn');
		td = document.createElement('td');
		td.setAttribute('onclick', "window.open('" + resp['WWW'] + "');");
		td.setAttribute('onmouseover', "this.setAttribute('class', 'qfits-result-entry-complete-on');");
		td.setAttribute('onmouseout', "this.setAttribute('class', 'qfits-result-entry-complete-off');");
		td.setAttribute('class', 'qfits-result-entry-complete-off');
		td.appendChild(document.createTextNode('See full QFits web page'));
		tr.appendChild(td);

		td = document.createElement('td');
		var tns = ['bkg_histo', 'bkg_m', 'ell', 'fwhm_histo', 'gal_histo', 'm', 'psf_m', 'rhmag_gal', 'rhmag_star', 'rhmag', 'star_histo', 'wmm'];
		var tn;
		for (var k=0; k < tns.length; k++) {
			tn = document.createElement('img');
			tn.setAttribute('src', resp['WWW'] + 'tn/' + resp['ImgName'] + '_' + tns[k] + '_tn.png');
			tn.setAttribute('onclick', "window.open('" + resp['WWW'] + resp['ImgName'] + '_' + tns[k] + ".png');");
			tn.setAttribute('class', 'qfits-result-entry-tn');
			td.appendChild(tn);
		}
		tr.appendChild(td);
		tab2.appendChild(tr);
	}

	// QFits-in processing history
	// Header title
	var hist = resp['QFitsHistory'];
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	td.setAttribute('class', 'qfits-result-header-title');
	td.appendChild(document.createTextNode('QualityFITS-In processing history (' + hist.length + ')'));
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

		// Grading count
		td = document.createElement('td');
		var gtxt = 'Not graded';
		if (hist[k]['GradingCount'] > 0) 
			gtxt = 'Graded (x' + hist[k]['GradingCount'] + ')';
		td.appendChild(document.createTextNode(gtxt));
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

	// QualityFits run parameters
	// Image
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	td.setAttribute('class', 'qfits-result-header-title');
	td.appendChild(document.createTextNode('QualityFITS run parameters'));
	tr.appendChild(td);
	tab2.appendChild(tr);

	tr = document.createElement('tr');
	td = document.createElement('td');
	td.appendChild(document.createTextNode('Image:'));
	tr.appendChild(td);

	td = document.createElement('td');
	td.appendChild(document.createTextNode(resp['ImgPath'] + resp['ImgName'] + '.fits'));
	tr.appendChild(td);
	tab2.appendChild(tr);

	// Flat
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.appendChild(document.createTextNode('Flat:'));
	tr.appendChild(td);

	td = document.createElement('td');
	td.appendChild(document.createTextNode(resp['Flat']));
	tr.appendChild(td);
	tab2.appendChild(tr);

	// Mask
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.appendChild(document.createTextNode('Mask:'));
	tr.appendChild(td);

	td = document.createElement('td');
	td.appendChild(document.createTextNode(resp['Mask']));
	tr.appendChild(td);
	tab2.appendChild(tr);

	// Region
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.appendChild(document.createTextNode('Reg:'));
	tr.appendChild(td);

	var m = resp['Reg'].length > 0 ? reps['Reg'] : '--';
	td = document.createElement('td');
	td.appendChild(document.createTextNode(m));
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

	// QF Config file
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	if (resp['Success']) {
		td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
	}
	var but = document.createElement('input');
	but.setAttribute('type', 'button');
	but.setAttribute('value', 'Toggle QualityFITS config file view');
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
		cdiv.setAttribute('style', 'height: 200px; overflow: auto; background-color: black; padding-left: 5px; display: none; width: 550px;')
		var pre = document.createElement('pre');
		pre.appendChild(document.createTextNode(resp['Log']));
		cdiv.appendChild(pre);
		td.appendChild(cdiv);
		tr.appendChild(td);
		tab2.appendChild(tr);
	}

	// Image information
	// Header title
	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	td.setAttribute('class', 'qfits-result-header-title');
	td.appendChild(document.createTextNode('Image information'));
	tr.appendChild(td);
	tab2.appendChild(tr);

	tr = document.createElement('tr');
	td = document.createElement('td');
	td.setAttribute('colspan', '2');
	if (resp['Success']) {
		td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
	}
	tr.appendChild(td);
	td.appendChild({{ plugin.id }}_getDynTable(resp['ImgInfo'], 3));
	tab2.appendChild(tr);

	// QFits information
	// Header title
	if (resp['Success']) {
		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.appendChild(document.createTextNode('QualityFits information'));
		tr.appendChild(td);
		tab2.appendChild(tr);

		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('colspan', '2');
		tr.appendChild(td);
		td.appendChild({{ plugin.id }}_getDynTable(resp['QFitsInfo'], 4));
		tab2.appendChild(tr);
	}

	// QFits results ingestion log, if any (only when QF was successful)
	if (resp['ResultsLog']) {
		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('colspan', '2');
		var but = document.createElement('input');
		but.setAttribute('type', 'button');
		but.setAttribute('value', 'Toggle QFits results ingestion log view');
		but.setAttribute('onclick', "toggleDisplay('qflog-" + resp['TaskId'] + "');");
		td.appendChild(but);
		var cdiv = document.createElement('div');
		cdiv.setAttribute('id', 'qflog-' + resp['TaskId']);
		cdiv.setAttribute('style', 'height: 200px; overflow: auto; background-color: black; padding-left: 5px; display: none')
		var pre = document.createElement('pre');
		pre.appendChild(document.createTextNode(resp['ResultsLog']));
		cdiv.appendChild(pre);
		td.appendChild(cdiv);
		tr.appendChild(td);
		tab2.appendChild(tr);
	}

	d.appendChild(tab);
	container.appendChild(d);

	if (resp['Success']) {
		if (resp['GradingCount'] > 0) {
			var graddiv;
			var gradwid;
			var gtab = document.createElement('table');
			gtab.setAttribute('class', 'qfits-result-entry-grades');
			gdiv.appendChild(gtab);
			for (var g=0; g < resp['Grades'].length; g++) {
				tr = document.createElement('tr');
				td = document.createElement('td');
				td.appendChild(document.createTextNode(resp['Grades'][g][1]));
				tr.appendChild(td);
				gtab.appendChild(tr);

				td = document.createElement('td');
				graddiv = document.createElement('div');
				graddiv.setAttribute('align', 'right');
				graddiv.setAttribute('id', 'grade_div_' + g);
				td.appendChild(graddiv);
				tr.appendChild(td);
				gtab.appendChild(tr);
				// Variable name does not matter (as 2nd argument) because the widget 
				// is turned into a read-only widget with setActive(false)
				gradwid = new GradingWidget('grade_div_' + g, 'gradwid');
				gradwid.setLegendEnabled(false);
				gradwid.setActive(false);
				gradwid.setCharGrade(resp['Grades'][g][1]);

				td = document.createElement('td');
				td.appendChild(document.createTextNode(resp['Grades'][g][0]));
				tr.appendChild(td);
			}
		}
	}
}

// File browser for flats, masks and reg paths
var {{ plugin.id }}_fm_file_browser;

function {{ plugin.id }}_getTabId(ul_id) {
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
}

function selectImages() {
	var root = document.getElementById('menuitem_sub_0');
	root.setAttribute('align', 'center');

	// Help message
	/*
	var msg = getMessageNode("Please make a custom image selection using the form below then click on the 'Add selection to processing queue' button " + 
					" on the resulting left-side control panel to queue a new QualityFITS-in process with the current image selection. This selection will be added to the" + 
					" cart which must be VALIDATED to effectively send the processes to the cluster.");
	root.appendChild(msg);
	*/

	// Container of the ImageSelector widget
	var div = document.createElement('div');
	div.setAttribute('id', '{{ plugin.id }}_results_div');
	div.setAttribute('align', 'center');
	div.setAttribute('style', 'padding-top: 20px; width: 80%');
	root.appendChild(div);

	{{ plugin.id }}_ims = new ImageSelector('{{ plugin.id }}_results_div', '{{ plugin.id }}_ims');
	{{ plugin.id }}_advTab = new AdvancedTable('{{ plugin.id }}_advTab');
	{{ plugin.id }}_ims.setTableWidget({{ plugin.id }}_advTab);
}

// container_id is a td containing the cancel button
function {{ plugin.id }}_cancelJob(container_id, clusterId, procId) {
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
}

/*
 * Condor job monitoring
 *
 */
function monitorJobs() {
	var container = document.getElementById('menuitem_sub_3');

	/*
	 * Stop monitoring jobs when current selected tab is not related to 'Job monitoring'
	 * thus tries to save bandwidth: ajax calls are only made when the 'Job monitoring' tab
	 * is activated.
	 *
	 */
	var nav = document.getElementById('menu');
	var current = {{ plugin.id }}_getTabId('menu');
	var curNode = nav.getElementsByTagName('a')[current];
	if (curNode.firstChild.nodeValue != 'QualityFITS job monitoring') {
		return;
	}

	var r = new HttpRequest(
		null,
		null,
		// Custom handler for results
		function(resp) {
			r = resp['result'][0];
			var div = document.createElement('div');
			div.setAttribute('align', 'center');

			if (r.length == 0) {
				var n = getMessageNode('Nothing to monitor. No QualityFits job is actually running or queued on the cluster.', 'warning');
				div.appendChild(n);
				removeAllChildrenNodes(container);
				container.appendChild(div);

				setTimeout("monitorJobs('" + container.id + "')", 2000);
				return;
			}

			var table = document.createElement('table');
			table.setAttribute('class', 'jobMonitor');
			var tr, th, td, cls;

			// Page info
			if (resp['result'][2] > 1) {
				{{ plugin.id }}_gNextPage = resp['result'][3];
				var pdiv = document.createElement('div');
				pdiv.appendChild(document.createTextNode('Show page: '));
				var a;
				for (var p=0; p < resp['result'][2]; p++) {
					if ({{ plugin.id }}_gNextPage == p+1) {
						pdiv.appendChild(document.createTextNode(' ' + (p+1) + ' '));
						continue;
					}

					a = document.createElement('a');
					a.setAttribute('href', '#');
					a.setAttribute('onclick', '{{ plugin.id }}_gNextPage=' + (p+1) + "; document.getElementById('{{ plugin.id }}_current_page_div').innerHTML = getLoadingHTML('Loading page " + (p+1) + "');");
					a.appendChild(document.createTextNode(' ' + (p+1) + ' '));
					pdiv.appendChild(a);
				}
				div.appendChild(pdiv);
				pdiv = document.createElement('div');
				pdiv.setAttribute('id', '{{ plugin.id }}_current_page_div');
				pdiv.setAttribute('class', 'currentPage');
				pdiv.appendChild(document.createTextNode('Page ' + {{ plugin.id }}_gNextPage + ' / ' + resp['result'][2]));
				div.appendChild(pdiv);
			}

			// Table header
			tr = document.createElement('tr');
			tr.setAttribute('class', 'jobHeader');
			var header = ['Item ID', 'Job ID', 'Info', 'Remote host', 'Run time', 'Status', 'Action'];
			for (var j=0; j < header.length; j++) {
				th = document.createElement('th');
				th.appendChild(document.createTextNode(header[j]));
				tr.appendChild(th);
			}
			table.appendChild(tr);

			// Various divs
			var tabi, tabitr, tabitd;
			for (var j=0; j < r.length; j++) {
				tr = document.createElement('tr');

				td = document.createElement('td');
				td.setAttribute('class', 'jobId');
				td.appendChild(document.createTextNode(r[j]['UserData']['ItemID']));
				tr.appendChild(td);

				td = document.createElement('td');
				td.setAttribute('class', 'jobId');
				td.appendChild(document.createTextNode(r[j]['ClusterId'] + '.' + r[j]['ProcId']));
				tr.appendChild(td);

				td = document.createElement('td');
				td.setAttribute('class', 'info');
				tabi = document.createElement('table');
				tabi.setAttribute('class', 'info');

				tabitr = document.createElement('tr');
				tabitd = document.createElement('td');
				tabitd.appendChild(document.createTextNode('File'));
				tabitd.setAttribute('class', 'label');
				tabitr.appendChild(tabitd);
				tabitd = document.createElement('td');
				tabitd.setAttribute('class', 'file');
				tabitd.appendChild(document.createTextNode(r[j]['FitsFile']));
				tabitr.appendChild(tabitd);
				tabi.appendChild(tabitr);

				tabitr = document.createElement('tr');
				tabitd = document.createElement('td');
				tabitd.appendChild(document.createTextNode('CSF'));
				tabitd.setAttribute('class', 'label');
				tabitr.appendChild(tabitd);
				tabitd = document.createElement('td');
				tabitd.setAttribute('class', 'file');
				tabitd.appendChild(document.createTextNode(r[j]['UserData']['SubmissionFile']));
				tabitr.appendChild(tabitd);
				tabi.appendChild(tabitr);

				tabitr = document.createElement('tr');
				tabitd = document.createElement('td');
				tabitd.appendChild(document.createTextNode('QF'));
				tabitd.setAttribute('class', 'label');
				tabitr.appendChild(tabitd);
				tabitd = document.createElement('td');
				tabitd.setAttribute('class', 'file');
				tabitd.appendChild(document.createTextNode(r[j]['UserData']['ConfigFile']));
				tabitr.appendChild(tabitd);
				tabi.appendChild(tabitr);

				try {
					warns = r[j]['UserData']['Warnings'][r[j]['FitsFile']];
					for (var k=0; k < warns.length; k++) {
						tabitr = document.createElement('tr');
						tabitd = document.createElement('td');
						tabitd.appendChild(document.createTextNode('Warn'));
						tabitd.setAttribute('class', 'label');
						tabitr.appendChild(tabitd);
						tabitd = document.createElement('td');
						tabitd.setAttribute('class', 'warning');
						tabitd.appendChild(document.createTextNode(warns[k]));
						tabitr.appendChild(tabitd);
						tabi.appendChild(tabitr);
					}
				} catch(e) {}

				td.appendChild(tabi);
				tr.appendChild(td);

				td = document.createElement('td');
				td.setAttribute('class', 'jobRemoteHost');
				td.appendChild(document.createTextNode(r[j]['RemoteHost'] ? r[j]['RemoteHost'] : '-'));
				tr.appendChild(td);

				td = document.createElement('td');
				td.setAttribute('class', 'jobDuration');
				td.appendChild(document.createTextNode(r[j]['JobDuration'] ? r[j]['JobDuration'] : '-'));
				tr.appendChild(td);

				td = document.createElement('td');
				td.setAttribute('class', 'jobCurrentStatus');

				var st = r[j]['JobStatus'];
				var status;
				switch (st) {
					case '2':
						status = 'Running';
						cls = 'jobRunning';
						break;
					case '5':
						status = 'Hold';
						cls = 'jobHold';
						break;
					default:
						status = 'Idle';
						cls = 'jobIdle';
						break;
				}
				tr.setAttribute('class', cls);

				//td.appendChild(document.createTextNode(r[j]['JobStatus'] == '2' ? 'Running' : 'Idle'));
				td.appendChild(document.createTextNode(status));
				tr.appendChild(td);

				// Actions
				td = document.createElement('td');
				var tdid = '{{ plugin.internal_name }}_cancel_' + j;
				td.setAttribute('class', 'jobActions');
				td.setAttribute('id', tdid);
				/*
				but = document.createElement('input');
				but.setAttribute('type', 'button');
				but.setAttribute('value', 'Cancel');
				*/

				img = document.createElement('img');
				td.appendChild(img);
				img.setAttribute('style', 'cursor: pointer');
				img.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/16x16/cancel.png');
				img.setAttribute('onclick', "{{ plugin.id }}_cancelJob('" + tdid + "'," + r[j]['ClusterId'] + "," + r[j]['ProcId'] + ");");
				tr.appendChild(td);

				table.appendChild(tr);
			}
			div.appendChild(table);
			removeAllChildrenNodes(container);
			container.appendChild(div);

			setTimeout("monitorJobs('" + container.id + "')", 2000);
		}
	);

	var post = 'Plugin={{ plugin.id }}&Method=jobStatus&NextPage=' + {{ plugin.id }}_gNextPage;
	r.send('/youpi/process/plugin/', post);
}

function doit() {
	selectImages();
	monitorJobs();
}

/*
 * Add to cart step involves several checks:
 * 1. At least one image has been selected
 * 2. Flats and masks paths have been selected
 * 3. A configuration file has been selected (always the case since 'default' is selected)
 * 
 */
function {{ plugin.id }}_addSelectionToCart() {
	sels = {{ plugin.id }}_ims.getListsOfSelections();

	if (!sels) {
		alert('No images selected. Nothing to add to cart !');
		return;
	}

	// CHECK 2: non-empty flat, mask and reg paths?

	// MANDATORY PATHS
	var mandvars = selector.getMandatoryPrefixes();
	var mandpaths = new Array();
	for (var k=0; k < mandvars.length; k++) {
		var selNode = document.getElementById('{{ plugin.id }}_' + mandvars[k] + '_select');
		var success = true;
		var path;
		if (!selNode)
			success = false;
		else {
			path = selNode.options[selNode.selectedIndex].text;
			if (path == selector.getNoSelectionPattern()) {
				success = false;
			}
			mandpaths.push(path);
		}

		if (!success) {
			alert("No " + mandvars[k] + " path selected for images. Please make a selection in 'Select data paths' menu first.");
			return;
		}
	}

	// OPTIONAL
	var rSel = document.getElementById('{{plugin.id}}_regs_select');
	var regPath = '';
	if (rSel) {
		var path = rSel.options[rSel.selectedIndex].text;
		if (path != selector.getNoSelectionPattern())
			regPath = path;
	}

	// CHECK 3: get config file
	var cSel = document.getElementById('{{ plugin.id }}_config_name_select');
	var config = cSel.options[cSel.selectedIndex].text;

	// CHECK 4: custom output directory
	var custom_dir = document.getElementById('output_path_input').value;
	var output_data_path = '{{ processing_output }}{{ user.username }}/{{ plugin.id }}/';

	if (custom_dir && custom_dir.replace(/\ /g, '').length) {
		custom_dir = custom_dir.replace(/\ /g, '');
		if (custom_dir.length) {
			output_data_path += custom_dir + '/';
		}
	}

	// Finally, add to the shopping cart
	p_data = {	'plugin_name' 	: '{{ plugin.id }}', 
				'userData' 		:	"{'config' : '" + config + 
									"', 'imgList' : '" + sels + 
									"', 'flatPath' : '" + mandpaths[0] + 
									"', 'maskPath' : '" + mandpaths[1] + 
									"', 'regPath' : '" + regPath +
									"', 'resultsOutputDir' : '" + output_data_path +
									"'}" };

	var total = {{ plugin.id }}_ims.getImagesCount();
	s_cart.addProcessing(	p_data,
							// Custom handler
							function() {
								alert('The current image selection (' + total + ' ' + (total > 1 ? 'images' : 'image') + ') has been\nadded to the cart.');
							}
	);

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

/*
 * This function will add an item to the shopping cart for reprocessing all failed processings
 * currently selected at a time. 
 *
 * Note that its behaviour is specific for qualityFits data processing:
 *
 * ONLY failed processings that have *never succeeded* will be scheduled for reprocessing.
 * Those failed processings that have been already been successfuly reprocessed (at least one time) 
 * but appears in the current selection of failed processings WILL NOT BE SCHEDULED for reprocessing.
 *
 * Other processing plugins may use other rules or policies for data reprocessing.
 *
 */
function {{ plugin.id }}_reprocessAllFailedProcessings(tasksList) {
	var container = document.getElementById('{{ plugin.id }}_stats_info_div');
	var r = new HttpRequest(
		container.id,
		null,
		// Custom handler for results
		function(resp) {
			var r = resp['result'];
			var proc = r['Processings'];

			for (var k=0; k < proc.length; k++) {
				p_data = {	'plugin_name' : '{{ plugin.id }}', 
							'userData' : "{'config' : 'The one used for the last processing" +
							"', 'fitsinId' : '" + proc[k]['FitsinId'] + 
							"', 'imgList' : '" + proc[k]['ImgList'] + 
							"', 'flatPath' : '" + proc[k]['Flat'] + 
							"', 'maskPath' : '" + proc[k]['Mask'] + 
							"', 'regPath' : '" + proc[k]['Reg'] +
							"', 'resultsOutputDir' : '" + proc[k]['ResultsOutputDir'] +
							"'}" };
	
				s_cart.addProcessing(	p_data,
										// Custom handler
										function() {
											container.innerHTML = "<img src=\"/media/{{ user.get_profile.guistyle }}/img/admin/icon-yes.gif\"/> Done. A cart item for reprocessing all " + 
												tasksList.split(',').length + " images at once has been<br/>added to your <a href=\"/youpi/cart/\">shopping cart</a>.";
										}
				);
			}
		}
	);

	var post = 'Plugin={{ plugin.id }}&Method=reprocessAllFailedProcessings&TasksList=' + tasksList;
	r.setBusyMsg('Adding new cart item for reprocessing ' + tasksList.split(',').length + ' images');
	r.send('/youpi/process/plugin/', post);
}

function {{ plugin.id }}_renderOutputDirStats(container_id) {
	var container = document.getElementById(container_id);
	container.innerHTML = '';

	// global var defined in results.html
	var resp = output_dir_stats_data;
	var stats = resp['Stats'];
	var reprocess_len = stats['ReprocessTaskList'].length;

	var tab = document.createElement('table');
	tab.setAttribute('class', 'output_dir_stats');
	var tr,th,td;
	var tr = document.createElement('tr');
	// Header
	var header = ['Image success', 'Image failures', 'Images processed', 'Task success', 'Task failures', 'Total processings'];
	var cls = ['image_success', 'image_failure', 'image_total', 'task_success', 'task_failure', 'task_total'];
	for (var k=0; k < header.length; k++) {
		th = document.createElement('th');
		th.setAttribute('class', cls[k]);
		th.setAttribute('colspan', '2');
		th.appendChild(document.createTextNode(header[k]));
		if (k == 1 && reprocess_len) {
			th.appendChild(document.createElement('br'));
			var rimg = document.createElement('img');
			rimg.setAttribute('onclick', resp['PluginId'] + "_reprocessAllFailedProcessings('" + stats['ReprocessTaskList'] + "');");
			rimg.setAttribute('src', '/media/{{ user.get_profile.guistyle }}/img/misc/reprocess.gif');
			rimg.setAttribute('style', 'cursor: pointer;');
			th.appendChild(rimg);
		}
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
				val = stats['ImageSuccessCount'][0];
				percent = stats['ImageSuccessCount'][1] + '%';
				cls = 'image_success';
				break;
			case 1:
				val = stats['ImageFailureCount'][0];
				percent = stats['ImageFailureCount'][1] + '%';
				cls = 'image_failure';
				break;
			case 2:
				val = stats['Distinct'];
				percent = '100%';
				cls = 'image_total';
				break;
			case 3:
				val = stats['TaskSuccessCount'][0];
				percent = stats['TaskSuccessCount'][1] + '%';
				cls = 'task_success';
				break;
			case 4:
				val = stats['TaskFailureCount'][0];
				percent = stats['TaskFailureCount'][1] + '%';
				cls = 'task_failure';
				break;
			case 5:
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

	var idiv = document.createElement('div');
	idiv.setAttribute('id', '{{ plugin.id }}_stats_info_div');
	idiv.setAttribute('style', 'margin-top: 20px;');
	container.appendChild(idiv);

	if (!reprocess_len) return;

	var ldiv = document.createElement('div');
	ldiv.setAttribute('style', 'margin-top: 20px;');

	var tdiv = document.createElement('div');
	tdiv.setAttribute('class', 'stats_error_log_title');
	tdiv.appendChild(document.createTextNode('Error logs for failed images'));
	ldiv.appendChild(tdiv);

	var bdiv = document.createElement('div');
	bdiv.setAttribute('style', 'margin-top: 20px; width: 70%;');

	var imgdiv = document.createElement('div');
	imgdiv.setAttribute('style', 'float: left;');

	var imgSel = document.createElement('select');
	imgSel.setAttribute('id', '{{ plugin.id }}_stats_img_sel_select');
	imgSel.setAttribute('size', 15);
	var opt;
	for (var k=0; k < stats['ImagesTasks'].length; k++) {
		opt = document.createElement('option');
		opt.setAttribute('value', stats['ImagesTasks'][k][0]);	
		opt.appendChild(document.createTextNode(stats['ImagesTasks'][k][1]));	
		imgSel.appendChild(opt);
	}

	imgdiv.appendChild(imgSel);
	bdiv.appendChild(imgdiv);

	var logdiv = document.createElement('div');
	logdiv.setAttribute('id', '{{ plugin.id }}_stats_log_div');
	logdiv.setAttribute('style', 'height: 300px; text-align: left; overflow: auto; background-color: black; color: white; padding-left: 5px;')
	bdiv.appendChild(logdiv);

	imgSel.options[0].selected = true;
	imgSel.setAttribute('onclick', "{{ plugin.id }}_getTaskLog('" + logdiv.id + "', this.options[this.selectedIndex].value);");

	ldiv.appendChild(bdiv);
	container.appendChild(ldiv);

	{{ plugin.id }}_getTaskLog(logdiv.id, imgSel.options[0].value);
}

function {{ plugin.id }}_getTaskLog(container_id, taskId) {
	var container = document.getElementById(container_id);
	var r = new HttpRequest(
			container_id,
			null,	
			// Custom handler for results
			function(resp) {
				container.innerHTML = '<pre>' + 'Error log for image ' + resp['result']['ImgName'] + ':\n\n' + resp['result']['Log'] + '</pre>';
			}
	);

	var post = 'Plugin={{ plugin.id }}&Method=getTaskLog&TaskId=' + taskId; 
	r.setBusyMsg('Please wait while loading error log file content');
	r.send('/youpi/process/plugin/', post);
}
