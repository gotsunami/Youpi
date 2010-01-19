/*****************************************************************************
 *
 * Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/


// JS code for qualityfits-in plugin

// Global vars
var {{ plugin.id }}_ims;
var {{ plugin.id }}_gNextPage = 1;
var {{ plugin.id }}_itemIdx = 0;
// File browser for flats, masks and reg paths
var {{ plugin.id }}_fm_file_browser;
var {{ plugin.id }}_advTab;

var uidfitsin = '{{ plugin.id }}';

var {{ plugin.id }} = {
	viewImageList: function(container_id, idList) {
		var idList = eval(idList);
		var c = '';
		for (var k=0; k < idList.length; k++) {
			c += idList[k].toString();
			if (k < idList.length-1) c += ',';
		}
		idList = c.split(',');
	
		var div = $(container_id);
		if (div.style.display == 'none') {
			removeAllChildrenNodes(div);
			var indiv = new Element('div');
			indiv.appendChild(document.createTextNode('View info for image: '));
			var select = new Element('select');
			var option;
			for (var k=0; k < idList.length; k++) {
				option = new Element('option');
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
	
	/*
	 * Function: run
	 * Run processing
	 *
	 * Parameters:
	 *  trid - string: for row number
	 *  opts - hash: options
	 *  silent - boolean: silently submit item to the cluster
	 *
	 */ 
	run: function(trid, opts, silent) {
		var silent = silent == true ? true : false;
		var txt = '';
		var runopts = get_runtime_options(trid);
		
		// Hide action controls
		var tds = $(trid).select('td');
		delImg = tds[0].select('img')[0].hide();
		runDiv = tds[1].select('div.submitItem')[0].hide();
		otherImgs = tds[1].select('img');
		otherImgs.invoke('hide');
	
		var logdiv = $('master_condor_log_div');
		var r = new HttpRequest(
				logdiv,
				null,	
				// Custom handler for results
				function(resp) {
					r = resp.result;
					var success = update_condor_submission_log(resp, silent);
					if (!success) {
						[delImg, runDiv].invoke('show');
						otherImgs.invoke('show');
						return;
					}
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
				}
		);
	
		// Adds various options
		opts = $H(opts);
		opts.set('Plugin', uidfitsin);
		opts.set('Method', 'process');
		opts.set('ReprocessValid', (runopts.reprocessValid ? 1 : 0));
		opts = opts.merge(runopts.clusterPolicy.toQueryParams());

		r.send('/youpi/process/plugin/', opts.toQueryString());
	},

	sendAll: function(data) {
		var r = new HttpRequest(
				'{{ plugin.id}}_result',
				null,	
				// Custom handler for results
				function(resp) {
					// removeItemFromCart(data[p][0], true);
					{{ plugin.id }}_itemIdx++;
					if ({{ plugin.id }}_itemIdx < data.length) {
						{{ plugin.id }}.sendAll(data);
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
	},

	runAll: function() {
		var prefix = $('prefix').value.replace(/ /g, '');
		var txt = '';
	
		var r = confirm('Are you sure you want to submit ALL items to the cluster?' + txt);
		if (!r) return;
	
		var trNode;
		var j=0;
		data = new Array();
	
		{% for data in plugin.getData %}
			trNode = $('{{ plugin.id }}_' + (j+1));
			data[j] = [trNode, '{{ data.idList }}', prefix + '{{ plugin.itemPrefix }}{{ data.itemCounter }}'];
			j++;
		{% endfor %}
	
		{{ plugin.id }}.sendAll(data);
	},

	saveItemForLater: function(trid, opts, silent) {
		opts = $H(opts);
		opts.set('Plugin', uidfitsin);
		opts.set('Method', 'saveCartItem');

		var runopts = get_runtime_options(trid);
		var r = new HttpRequest(
				uidswarp + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					document.fire('notifier:notify', 'QualityFITS item saved successfully');
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
				}
		);
	
		r.send('/youpi/process/plugin/', opts.toQueryString());
	},

	// Mandatory function
	showSavedItems: function() {
		var cdiv = $('plugin_menuitem_sub_{{ plugin.id }}');
		cdiv.innerHTML = '';
		var div = new Element('div');
		div.setAttribute('class', 'savedItems');
		div.setAttribute('id', '{{ plugin.id }}_saved_items_div');
		cdiv.appendChild(div);
	
		var r = new HttpRequest(
				div.id,
				null,	
				// Custom handler for results
				function(resp) {
					div.update();
	
					var total = resp.result.length;
					if (total == 0) {
        	            div.update('No saved item');
						return;
					}
					var table = new Element('table');
					table.setAttribute('class', 'savedItems');
					var tr, th;
					tr = new Element('tr');
					var header = ['Date', 'Permissions', 'Name', '# images', 'Config', 'Paths', 'Action'];
					for (var k=0; k < header.length; k++) {
						th = new Element('th');
						th.appendChild(document.createTextNode(header[k]));
						tr.appendChild(th);
					}
					table.appendChild(tr);
	
					var delImg, addImg, trid;
					var tabi, tabitr, tabitd;
					var idList, txt;
					for (var k=0; k < resp['result'].length; k++) {
						idList = eval(resp['result'][k]['idList']);
						tr = new Element('tr');
						trid = '{{ plugin.id }}_saved_item_' + k + '_tr';
						tr.setAttribute('id', trid);
						delImg = new Element('img', {id: uidfitsin + '_del_saved_item_' + k}).hide();
	
						// Date
						td = new Element('td');
						td.insert(resp['result'][k]['date']);
						tr.appendChild(td);
	
						// Permissions
						td = new Element('td', {'class': 'config'}).update(get_permissions('cartitem', resp['result'][k]['itemId'], function(r, imgId) {
							// imgId is the misc parameter passed to get_permissions()
							var img = $(imgId);
							r.currentUser.write ? img.show() : img.hide();
						}, delImg.readAttribute('id') /* Misc data */));
						tr.insert(td);
	
						// Name
						td = new Element('td');
						td.setAttribute('class', 'name');
						td.appendChild(document.createTextNode(resp['result'][k]['name']));
						tr.appendChild(td);

						// Images count
						td = new Element('td');
						td.setAttribute('class', 'imgCount');
						idList.length > 1 ? txt = 'Batch' : txt = 'Single';
						var sp = new Element('span');
						sp.setAttribute('style', 'font-weight: bold; text-decoration: underline;');
						sp.appendChild(document.createTextNode(txt));
						td.appendChild(sp);
						td.appendChild(new Element('br'));
	
						for (var j=0; j < idList.length; j++) {
							td.appendChild(document.createTextNode(idList[j].length));
							td.appendChild(new Element('br'));
						}
						tr.appendChild(td);
	
						// Config
						td = new Element('td');
						td.setAttribute('class', 'config');
						td.appendChild(document.createTextNode(resp['result'][k]['config']));
						tr.appendChild(td);

						// Flat, Mask, Reg
						td = new Element('td');
						tabi = new Element('table');
						tabi.setAttribute('class', 'info');
	
						// Flat
						tabitr = new Element('tr');
						tabitd = new Element('td');
						tabitd.appendChild(document.createTextNode('Flat: '));
						tabitd.setAttribute('class', 'label');
						tabitr.appendChild(tabitd);
						tabitd = new Element('td');
						tabitd.setAttribute('class', 'file');
						tabitd.appendChild(reduceString(resp['result'][k]['flatPath']));
						tabitr.appendChild(tabitd);
						tabi.appendChild(tabitr);
	
						// Mask
						tabitr = new Element('tr');
						tabitd = new Element('td');
						tabitd.appendChild(document.createTextNode('Mask: '));
						tabitd.setAttribute('class', 'label');
						tabitr.appendChild(tabitd);
						tabitd = new Element('td');
						tabitd.setAttribute('class', 'file');
						tabitd.appendChild(reduceString(resp['result'][k]['maskPath']));
						tabitr.appendChild(tabitd);
						tabi.appendChild(tabitr);
	
						// Reg
						tabitr = new Element('tr');
						tabitd = new Element('td');
						tabitd.appendChild(document.createTextNode('Region: '));
						tabitd.setAttribute('class', 'label');
						tabitr.appendChild(tabitd);
						tabitd = new Element('td');
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
						td = new Element('td');
						delImg.setAttribute('style', 'margin-right: 5px');
						delImg.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/misc/delete.png');
						delImg.setAttribute('onclick', "{{ plugin.id }}.delSavedItem('" + trid + "', '" + resp['result'][k]['name'] + "')");
						td.insert(delImg.hide());

						var addImg = new Element('img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.png'});
						addImg.c_data = $H(resp.result[k]);
						addImg.observe('click', function() {
							{{ plugin.id }}.addToCart(this.c_data);
						});
						td.insert(addImg);
						tr.insert(td);
		
						table.appendChild(tr);
					}
					div.insert(table);
				}
		);
	
		var post = 	'Plugin={{ plugin.id }}&Method=getSavedItems';
		r.send('/youpi/process/plugin/', post);
	},

	addToCart: function(data) {
		var p_data = {
			plugin_name: uidfitsin,
			userData: data
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
	
		var trNode = $(trid);
		var r = new HttpRequest(
				uidfitsin + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					var node = trNode;
					var last = false;
					if (trNode.up('table').select('tr[id]').length == 1) {
						last = true;
						node = trNode.parentNode;
					}
		
					trNode.highlight({
						afterFinish: function() {
							node.fade({
								afterFinish: function() {
									node.remove();
									if (last) eval(uidfitsin + '.showSavedItems()');

									// Notify user
									document.fire('notifier:notify', "Item '" + name + "' successfully deleted");
								}
							});
						}
					});
				}
		);
	
		var post = {
			'Plugin': uidfitsin,
			'Method': 'deleteCartItem',
			'Name'	: name
		};

		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	},

	// Units are in data[z][2], if any
	getDynTable: function(data, numcols) {
		var itab = new Element('table');
		itab.setAttribute('style', 'width: 100%');
		var itr, itd;
		var icols = numcols;
		var irows = Math.floor(data.length/icols);
		var c = 1;
		itr = new Element('tr');
		itab.appendChild(itr);
		for (var z=0; z < data.length; z++) {
			itd = new Element('td');
			itd.setAttribute('nowrap', 'nowrap');
			var span = new Element('span');
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
				itr = new Element('tr');
				itab.appendChild(itr);
				c = 1;
			}
		}
	
		return itab;
	},
	
	/*
	 * Function: reprocessImage
	 * Schedule a QFits reprocessing
	 *
	 * Parameters:
	 *	taskId - string: DB task ID
	 *
	 */ 
	reprocessImage: function(taskId) {
		var r = new HttpRequest(
				null,
				null,	
				// Custom handler for results
				function(resp) {
					data = resp.result;
					p_data = {	plugin_name : '{{ plugin.id }}', 
								userData : { 	'config' : 'The one used for the last processing',
												'taskId' : taskId,
												'idList' : '[[' + data.ImageId + ']]',
												'flatPath' : data.Flat, 
												'maskPath' : data.Mask, 
												'regPath' : data.Reg,
												'resultsOutputDir' : data.ResultsOutputDir
								}
					};
	
					s_cart.addProcessing(
							p_data,
							// Custom handler
							function() {
								document.fire('notifier:notify', 'The current image has been scheduled for reprocessing. ' +
									'An item has been added to the processing cart.');
							}
					);
				}
		);

		var post = 'Plugin={{ plugin.id }}&Method=getReprocessingParams&TaskId=' + taskId;
		r.send('/youpi/process/plugin/', post);
	},
	
	/*
	 * Displays custom result information for qfits processing. 'resp' contains 
	 * server-side info to display
	 *
	 */
	resultsShowEntryDetails: function(container_id) {
		var tr, th, td;
		// See templates/results.html, function showDetails(...)
		// currentReturnedData: global variable
		var resp = currentReturnedData;
		var container = $(container_id);
		var d = new Element('div');
		d.setAttribute('class', 'entryResult');
		var tab = new Element('table');
		tab.setAttribute('class', 'fileBrowser');
		tab.setAttribute('style', 'width: 100%');
	
		tr = new Element('tr');
		th = new Element('th');
		th.appendChild(document.createTextNode(resp['Title']));
		tr.appendChild(th);
		tab.appendChild(tr);
	
		// Duration
		var tdiv = new Element('div');
		tdiv.setAttribute('class', 'duration');
		tdiv.appendChild(document.createTextNode(resp['Start']));
		tdiv.appendChild(new Element('br'));
		tdiv.appendChild(document.createTextNode(resp['End']));
		tdiv.appendChild(new Element('br'));
		var src;
		resp['Success'] ? src = 'success' : src = 'error';
		var img = new Element('img');
		img.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif');
		img.setAttribute('style', 'padding-right: 5px;');
		tdiv.appendChild(img);
		tdiv.appendChild(document.createTextNode(resp['Duration'] + ' on'));
		tdiv.appendChild(new Element('br'));
		tdiv.appendChild(document.createTextNode(resp['Hostname']));
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		td.appendChild(tdiv);
		tr.appendChild(td);
		tab.appendChild(tr);

		// User
		var udiv = new Element('div');
		udiv.setAttribute('class', 'user');
		udiv.appendChild(document.createTextNode('Job initiated by ' + resp['User']));
		udiv.appendChild(new Element('br'));
		udiv.appendChild(document.createTextNode('Exit status: '));
		udiv.appendChild(new Element('br'));
		var exit_s = new Element('span');
		var txt;
		resp['Success'] ? txt = 'success' : txt = 'failure';
		exit_s.setAttribute('class', 'exit_' + txt);
		exit_s.appendChild(document.createTextNode(txt));
		udiv.appendChild(exit_s);
		td.appendChild(udiv);
	
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('style', 'padding: 0px');
		var tab2 = new Element('table');
		tab2.setAttribute('class', 'qfits-result-entry-params');
		td.appendChild(tab2);
		tr.appendChild(td);
		tab.appendChild(tr);
	
		// Thumbnails when successful
		if (resp['Success']) {
			tr = new Element('tr');
			tr.setAttribute('class', 'qfits-result-entry-tn');
			td = new Element('td');
			td.setAttribute('onclick', "window.open('" + resp['WWW'] + "');");
			td.setAttribute('onmouseover', "this.setAttribute('class', 'qfits-result-entry-complete-on');");
			td.setAttribute('onmouseout', "this.setAttribute('class', 'qfits-result-entry-complete-off');");
			td.setAttribute('class', 'qfits-result-entry-complete-off');
			td.appendChild(document.createTextNode('See full QFits web page'));
			tr.appendChild(td);
	
			td = new Element('td');
			var tns = ['bkg_histo', 'bkg_m', 'ell', 'fwhm_histo', 'gal_histo', 'm', 'psf_m', 'rhmag_gal', 'rhmag_star', 'rhmag', 'star_histo', 'wmm'];
			var tn, a;
			for (var k=0; k < tns.length; k++) {
				a = Builder.node('a', {
					href: resp['WWW'] + resp['ImgName'] + '_' + tns[k] + '.png',
					rel: 'lightbox[qfitsin]'
				});
	
				tn = Builder.node('img', {
					src: resp['WWW'] + 'tn/' + resp['ImgName'] + '_' + tns[k] + '_tn.png',
					'class': 'qfits-result-entry-tn'
				}).hide();
				// Adds a cool fade-in effect
				$(tn).appear({duration: k/3});
	
				a.appendChild(tn);
				td.appendChild(a);
			}
			tr.appendChild(td);
			tab2.appendChild(tr);
		}
	
		// Permissions
		tr = new Element('tr');
		td = new Element('td', {colspan: 2}).setStyle({padding: '0px'});
		td.update(ResultsHelpers.getPermissionsEntry(resp.TaskId));
		tr.insert(td);
		tab2.insert(tr);
		
		// Image grading
		if (resp.Success) {
			tr = new Element('tr');
			td = new Element('td', {colspan: 2}).addClassName('qfits-result-header-title');
			td.insert('Image Grading');
			tr.insert(td);
			tab2.insert(tr);

			tr = new Element('tr');
			td = new Element('td');
		{% if not perms.youpi.can_grade %}
			var pgd = new Element('div').addClassName('perm_not_granted');
			td.insert(pgd.update("You don't have permission to grade qualityFITSed images."));
		{% endif %}
			var nowdiv = new Element('div', 'gradenow').addClassName('gradenow').setStyle({width: '-moz-fit-content'}).update('<u>G</u>rade it now!');
			nowdiv.insert(new Element('a', {href: '#', accesskey: 'g'}).setStyle({color: 'transparent'}));
			nowdiv.writeAttribute('title', 'Click to grade this image on a separate page');
			nowdiv.observe('click', function() {
		{% if perms.youpi.can_grade %}
			window.open("/youpi/grading/{{ plugin.id }}/" + resp.FitsinId + '/', '_blank');
		{% else %}
			alert("You don't have permission to grade images. Please contact an administrator.");
		{% endif %}
			});
			td.insert(nowdiv);
			tr.insert(td);

			td = new Element('td');
			var gdiv = new Element('div').setStyle({padding: '5px'});
			if (resp.GradingCount > 0)
				gdiv.addClassName('graded').update('Image graded ' + resp.GradingCount + ' time' + (resp.GradingCount > 1 ? 's' : ''));
			else 
				gdiv.addClassName('notgraded').update('Image not graded yet');

			td.insert(gdiv);
			tr.insert(td);
			tab2.insert(tr);
		}
	
		// Condor Job Logs
		tr = new Element('tr');
		td = new Element('td', {colspan: 2}).setStyle({padding: '0px'});
		td.update(ResultsHelpers.getCondorJobLogsEntry(resp.ClusterId, resp.TaskId));
		tr.insert(td);
		tab2.insert(tr);

		// QFits-in processing history
		// Header title
		var hist = resp['QFitsHistory'];
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.appendChild(document.createTextNode('QualityFITS-In processing history (' + hist.length + ')'));
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		htab = new Element('table');
		htab.setAttribute('class', 'qfits-result-history');
		td.appendChild(htab);
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		for (var k=0; k < hist.length; k++) {
			tr = new Element('tr');
			// Emphasis of current history entry
			if (resp['TaskId'] == hist[k]['TaskId']) {
				tr.setAttribute('class', 'history-current');
			}
	
			// Icon
			td = new Element('td');
			var src = hist[k]['Success'] ? 'success' : 'error';
			var img = new Element('img');
			img.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif');
			td.appendChild(img);
			tr.appendChild(td);
	
			// Grading count
			td = new Element('td');
			var gtxt = 'Not graded';
			if (hist[k]['GradingCount'] > 0) 
				gtxt = 'Graded (x' + hist[k]['GradingCount'] + ')';
			td.appendChild(document.createTextNode(gtxt));
			tr.appendChild(td);

			// Date-time, duration
			td = new Element('td');
			var a = new Element('a');
			a.setAttribute('href', '/youpi/results/{{ plugin.id }}/' + hist[k]['TaskId'] + '/');
			a.appendChild(document.createTextNode(hist[k]['Start'] + ' (' + hist[k]['Duration'] + ')'));
			td.appendChild(a);
			tr.appendChild(td);
	
			// Hostname
			td = new Element('td');
			td.appendChild(document.createTextNode(hist[k]['Hostname']));
			tr.appendChild(td);
	
			// User
			td = new Element('td');
			td.appendChild(document.createTextNode(hist[k]['User']));
			tr.appendChild(td);
	
			// Reprocess option
			td = new Element('td');
			td.setAttribute('class', 'reprocess');
			img = new Element('img');
			img.setAttribute('onclick', "{{ plugin.id }}.reprocessImage('" + hist[k]['TaskId'] + "');");
			img.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/misc/reprocess.gif');
			td.appendChild(img);
			tr.appendChild(td);
	
			htab.appendChild(tr);
		}
	
		// QualityFits run parameters
		// Image
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.appendChild(document.createTextNode('QualityFITS run parameters'));
		tr.appendChild(td);
		tab2.appendChild(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.appendChild(document.createTextNode('Image:'));
		tr.appendChild(td);
	
		td = new Element('td');
		td.appendChild(document.createTextNode(resp['ImgPath'] + resp['ImgName'] + '.fits'));
		tr.appendChild(td);
		tab2.appendChild(tr);

		// Exit if flat missing?
		tr = new Element('tr');
		tr.insert(new Element('td').update('Exit if flat missing:'));
		tr.insert(new Element('td').update(resp.ExitIfFlatMissing ? 'yes' : 'no'));
		tab2.insert(tr);
	
		// Flat
		tr = new Element('tr');
		td = new Element('td');
		td.appendChild(document.createTextNode('Flat:'));
		tr.appendChild(td);
	
		td = new Element('td');
		td.appendChild(document.createTextNode(resp['Flat']));
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		// Mask
		tr = new Element('tr');
		td = new Element('td');
		td.appendChild(document.createTextNode('Mask:'));
		tr.appendChild(td);
	
		td = new Element('td');
		td.appendChild(document.createTextNode(resp['Mask']));
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		// Region
		tr = new Element('tr');
		td = new Element('td');
		td.appendChild(document.createTextNode('Reg:'));
		tr.appendChild(td);

		var m = resp['Reg'].length > 0 ? resp['Reg'] : '--';
		td = new Element('td');
		td.appendChild(document.createTextNode(m));
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		// Output directory
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('nowrap', 'nowrap');
		td.appendChild(document.createTextNode('Results output dir:'));
		tr.appendChild(td);

		td = new Element('td');
		td.appendChild(document.createTextNode(resp['ResultsOutputDir']));
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		// QF Config file
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		if (resp['Success']) {
			td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		}
		var cdiv = new Element('div');
		cdiv.setAttribute('id', 'config-' + resp['TaskId']);
		cdiv.setAttribute('style', 'height: 300px; overflow: auto; background-color: black; padding-left: 5px; display: none; width: 550px;')
		var pre = new Element('pre');
		pre.appendChild(document.createTextNode(resp['Config']));
		cdiv.appendChild(pre);
		tr.appendChild(td);
		tab2.appendChild(tr);

		var confbox = new DropdownBox(td, 'Toggle QualityFITS config file view');
		$(confbox.getContentNode()).insert(cdiv);
		confbox.setOnClickHandler(function() {
			$('config-' + resp['TaskId']).toggle();
		});

		// Error log file when failure
		if (!resp['Success']) {
			tr = new Element('tr');
			td = new Element('td');
			td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
			td.setAttribute('colspan', '2');
			var cdiv = new Element('div');
			cdiv.setAttribute('id', 'log-' + resp['TaskId']);
			cdiv.setAttribute('style', 'height: 200px; overflow: auto; background-color: black; padding-left: 5px; display: none; width: 550px;')
			var pre = new Element('pre');
			pre.appendChild(document.createTextNode(resp['Log']));
			cdiv.appendChild(pre);
			tr.appendChild(td);
			tab2.appendChild(tr);

			var errorbox = new DropdownBox(td, 'Toggle error log file view');
			$(errorbox.getContentNode()).insert(cdiv);
			errorbox.setOnClickHandler(function() {
				$('log-' + resp['TaskId']).toggle();
			});
		}

		// Image information
		// Header title
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.appendChild(document.createTextNode('Image information'));
		tr.appendChild(td);
		tab2.appendChild(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		if (resp['Success']) {
			td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		}
		tr.appendChild(td);
		td.appendChild({{ plugin.id }}.getDynTable(resp['ImgInfo'], 3));
		tab2.appendChild(tr);

		// QFits information
		// Header title
		if (resp['Success']) {
			tr = new Element('tr');
			td = new Element('td');
			td.setAttribute('colspan', '2');
			td.setAttribute('class', 'qfits-result-header-title');
			td.appendChild(document.createTextNode('QualityFits information'));
			tr.appendChild(td);
			tab2.appendChild(tr);

			tr = new Element('tr');
			td = new Element('td');
			td.setAttribute('colspan', '2');
			tr.appendChild(td);
			td.appendChild({{ plugin.id }}.getDynTable(resp['QFitsInfo'], 4));
			tab2.appendChild(tr);
		}

		// QFits results ingestion log, if any (only when QF was successful)
		if (resp['ResultsLog']) {
			tr = new Element('tr');
			td = new Element('td');
			td.setAttribute('colspan', '2');
			var cdiv = new Element('div');
			cdiv.setAttribute('id', 'qflog-' + resp['TaskId']);
			cdiv.setAttribute('style', 'height: 200px; overflow: auto; background-color: black; padding-left: 5px; display: none')
			var pre = new Element('pre');
			pre.appendChild(document.createTextNode(resp['ResultsLog']));
			cdiv.appendChild(pre);
			tr.appendChild(td);
			tab2.appendChild(tr);

			var resultbox = new DropdownBox(td, 'Toggle QFits results ingestion log view');
			$(resultbox.getContentNode()).insert(cdiv);
			resultbox.setOnClickHandler(function() {
				$('qflog-' + resp['TaskId']).toggle();
			});
		}

		d.appendChild(tab);
		container.insert(d);

		if (resp.Success) {
			if (resp.GradingCount > 0) {
				// Add available grades
				var graddiv, gtr, gtd;
				var gradwid;
				var gtab = new Element('table').addClassName('qfits-result-entry-grades').setStyle({marginTop: '10px'});
				gdiv.insert(gtab);
				for (var p=0; p < resp.Grades.length; p++) {
					gtr = new Element('tr');
					gtd = new Element('td');
					gtd.appendChild(document.createTextNode(resp['Grades'][p][1]));
					gtr.appendChild(gtd);

					gtd = new Element('td');
					graddiv = new Element('div');
					graddiv.setAttribute('align', 'right');
					graddiv.setAttribute('id', 'grade_div_' + p);
					gtd.appendChild(graddiv);
					gtr.appendChild(gtd);
					gtab.appendChild(gtr);
					// Variable name does not matter (as 2nd argument) because the widget 
					// is turned into a read-only widget with setActive(false)
					gradwid = new GradingWidget('grade_div_' + p);
					gradwid.setLegendEnabled(false);
					gradwid.setActive(false);
					gradwid.setCharGrade(resp.Grades[p][1]);

					gtd = new Element('td');
					gtd.insert(resp.Grades[p][0]);
					gtr.appendChild(gtd);
					gtab.appendChild(gtr);
				}
			}
		}
	},

	/*
	 * Function: addProcessingResultsCustomOptions
	 * Add custom qfitsin options to the processing results page
	 *
	 * Parameters:
	 *	container - string: container ID
	 *
	 * Note:
	 * 	_name_ attribute is mandatory: will be used to generate POST data later
	 *
	 */ 
	addProcessingResultsCustomOptions: function(container) {
		var d = $(container);
		var lab = new Element('label').update('Show ');
		var gr = getSelect(uidfitsin + '_grading_select', ['all', 'graded', 'not graded']);
		gr.writeAttribute('name', 'GradingFilter');
		d.update(lab).insert(gr).insert(new Element('label').update(' images'));
	},

	getTabId: function(ul_id) {
		// Looking for tab's id
		//var ul = $('tabnav2');
		var ul = $(ul_id);
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
		var root = $('menuitem_sub_0');
		root.writeAttribute('align', 'center');
		// Container of the ImageSelector widget
		var div = new Element('div', {id: '{{ plugin.id }}_results_div', align: 'center'}).setStyle({width: '90%'});
		root.insert(div);

		{{ plugin.id }}_ims = new ImageSelector('{{ plugin.id }}_results_div');
		{{ plugin.id }}_advTab = new AdvancedTable();
		{{ plugin.id }}_ims.setTableWidget({{ plugin.id }}_advTab);
	},

	// container_id is a td containing the cancel button
	cancelJob: function(container_id, clusterId, procId) {
		var r = new HttpRequest(
			'container_id',
			null,
			// Custom handler for results
			function(resp) {
				var container = $(container_id);
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
	},

	/*
	 * Add to cart step involves several checks:
	 * 1. At least one image has been selected
	 * 2. Flats and masks paths have been selected
	 * 3. A configuration file has been selected (always the case since 'default' is selected)
	 * 
	 */
	addSelectionToCart: function() {
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
			var selNode = $('{{ plugin.id }}_' + mandvars[k] + '_select');
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
		var rSel = $('{{ plugin.id }}_regs_select');
		var regPath = '';
		if (rSel) {
			var path = rSel.options[rSel.selectedIndex].text;
			if (path != selector.getNoSelectionPattern())
				regPath = path;
		}

		// CHECK 3: get config file
		var cSel = $('{{ plugin.id }}_config_name_select');
		var config = cSel.options[cSel.selectedIndex].text;

		// CHECK 4: custom output directory
		var custom_dir = $('output_path_input').value;
		var output_data_path = '{{ processing_output }}{{ user.username }}/{{ plugin.id }}/';

		if (custom_dir && custom_dir.replace(/\ /g, '').length) {
			custom_dir = custom_dir.replace(/\ /g, '');
			if (custom_dir.length) {
				output_data_path += custom_dir + '/';
			}
		}

		// Finally, add to the processing cart
		var total = {{ plugin.id }}_ims.getImagesCount();

		p_data = {	plugin_name: uidfitsin,
					userData: {	
						config: config,
						idList: sels, 
						flatPath: mandpaths[0], 
						maskPath: mandpaths[1], 
						regPath: regPath,
						resultsOutputDir: output_data_path,
						exitIfFlatMissing: $(uidfitsin + '_exit_flat_option').checked ? 1:0,
					}
		};

		s_cart.addProcessing(p_data, function() {
			document.fire('notifier:notify', 'The current image selection (' + total + ' ' + 
				(total > 1 ? 'images' : 'image') + ') has been\nadded to the cart.');
		});
	},

	/*
	 * Function displayImageCount
	 * Renders list of images to be processed as a summary (used in the processing cart plugin rendering)
	 *
	 * Parameters:
	 *
	 * idList - array of arrays of idLists
	 *
	 */
	displayImageCount: function(idList, container_id) {
		var container = $(container_id);
		var idList = eval(idList);
		var c = 0;
		var txt;
		idList.length > 1 ? txt = 'Batch' : txt = 'Single';
		var selDiv = new Element('div', {'class': 'selectionModeTitle'}).update(txt + ' selection mode:');
		container.insert(selDiv);

		selDiv = new Element('div', {'class': 'listsOfSelections'});

		for (var k=0; k < idList.length; k++) {
			c = idList[k].toString().split(',').length;
			if (idList.length > 1)
				txt = 'Selection ' + (k+1) + ': ' + c + ' image' + (c > 1 ? 's' : '');
			else
				txt = c + ' image' + (c > 1 ? 's' : '');

			selDiv.update(txt);
			selDiv.insert(new Element('br'));
		}
		container.insert(selDiv);
	},

	/*
	 * This function will add an item to the processing cart for reprocessing all failed processings
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
	reprocessAllFailedProcessings: function(tasksList) {
		var container = $('{{ plugin.id }}_stats_info_div');
		var r = new HttpRequest(
			container.id,
			null,
			// Custom handler for results
			function(resp) {
				var r = resp['result'];
				var proc = r['Processings'];

				for (var k=0; k < proc.length; k++) {
					p_data = {	plugin_name: uidfitsin, 
								userData: {
									config: 'The one used for the last processing',
									fitsinId: proc[k]['FitsinId'],
									idList: proc[k]['IdList'],
									flatPath: proc[k]['Flat'],
									maskPath: proc[k]['Mask'],
									regPath: proc[k]['Reg'],
									taskId: proc[k]['TaskId'],
									resultsOutputDir: proc[k]['ResultsOutputDir'],
									exitIfFlatMissing: proc[k]['ExitIfFlatMissing']
								}
					};
		
					s_cart.addProcessing(	p_data,
											// Custom handler
											function() {
												container.innerHTML = "<img src=\"/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon-yes.gif\"/> Done. A cart item for reprocessing all " + 
													tasksList.split(',').length + " images at once has been<br/>added to your <a href=\"/youpi/cart/\">processing cart</a>.";
											}
					);
				}
			}
		);

		var post = 'Plugin={{ plugin.id }}&Method=reprocessAllFailedProcessings&TasksList=' + tasksList;
		r.setBusyMsg('Adding new cart item for reprocessing ' + tasksList.split(',').length + ' images');
		r.send('/youpi/process/plugin/', post);
	},

	renderOutputDirStats: function(container_id) {
		var container = $(container_id);
		container.innerHTML = '';

		// global var defined in results.html
		var resp = output_dir_stats_data;
		var stats = resp['Stats'];
		var reprocess_len = stats['ReprocessTaskList'].length;

		var tab = new Element('table');
		tab.setAttribute('class', 'output_dir_stats');
		var tr,th,td;
		var tr = new Element('tr');
		// Header
		var header = ['Image success', 'Image failures', 'Images processed', 'Task success', 'Task failures', 'Total processings'];
		var cls = ['image_success', 'image_failure', 'image_total', 'task_success', 'task_failure', 'task_total'];
		for (var k=0; k < header.length; k++) {
			th = new Element('th');
			th.setAttribute('class', cls[k]);
			th.setAttribute('colspan', '2');
			th.appendChild(document.createTextNode(header[k]));
			if (k == 1 && reprocess_len) {
				th.appendChild(new Element('br'));
				var rimg = new Element('img');
				rimg.setAttribute('onclick', resp['PluginId'] + ".reprocessAllFailedProcessings('" + stats['ReprocessTaskList'] + "');");
				rimg.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/misc/reprocess.gif');
				rimg.setAttribute('style', 'cursor: pointer;');
				th.appendChild(rimg);
			}
			tr.appendChild(th);
		}
		tab.appendChild(tr);

		tr = new Element('tr');
		var val, percent, cls;
		for (var k=0; k < header.length; k++) {
			c_td = new Element('td');
			p_td = new Element('td');
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

		var idiv = new Element('div');
		idiv.setAttribute('id', '{{ plugin.id }}_stats_info_div');
		idiv.setAttribute('style', 'margin-top: 20px;');
		container.appendChild(idiv);

		if (!reprocess_len) return;

		var ldiv = new Element('div');
		ldiv.setAttribute('style', 'margin-top: 20px;');

		var tdiv = new Element('div');
		tdiv.setAttribute('class', 'stats_error_log_title');
		tdiv.appendChild(document.createTextNode('Error logs for failed images'));
		ldiv.appendChild(tdiv);

		var bdiv = new Element('div');
		bdiv.setAttribute('style', 'margin-top: 20px; width: 70%;');

		var imgdiv = new Element('div');
		imgdiv.setAttribute('style', 'float: left;');

		var imgSel = new Element('select');
		imgSel.setAttribute('id', '{{ plugin.id }}_stats_img_sel_select');
		imgSel.setAttribute('size', 15);
		var opt;
		for (var k=0; k < stats['ImagesTasks'].length; k++) {
			opt = new Element('option');
			opt.setAttribute('value', stats['ImagesTasks'][k][0]);	
			opt.appendChild(document.createTextNode(stats['ImagesTasks'][k][1]));	
			imgSel.appendChild(opt);
		}

		imgdiv.appendChild(imgSel);
		bdiv.appendChild(imgdiv);

		var logdiv = new Element('div');
		logdiv.setAttribute('id', '{{ plugin.id }}_stats_log_div');
		logdiv.setAttribute('style', 'width: 700px; height: 300px; text-align: left; overflow: auto; background-color: black; color: white; padding-left: 5px;')
		bdiv.appendChild(logdiv);

		imgSel.options[0].selected = true;
		imgSel.setAttribute('onclick', "{{ plugin.id }}.getTaskLog('" + logdiv.id + "', this.options[this.selectedIndex].value);");

		ldiv.appendChild(bdiv);
		container.appendChild(ldiv);

		{{ plugin.id }}.getTaskLog(logdiv.id, imgSel.options[0].value);
	},

	getTaskLog: function(container_id, taskId) {
		var container = $(container_id);
		var r = new HttpRequest(
				container_id,
				null,	
				// Custom handler for results
				function(resp) {
					container.innerHTML = '<pre>' + 'Error log for image ' + resp['result']['ImgName'] + ':\n\n' + 
						resp['result']['Log'] + '</pre>';
				}
		);

		var post = 'Plugin={{ plugin.id }}&Method=getTaskLog&TaskId=' + taskId; 
		r.setBusyMsg('Please wait while loading error log file content');
		r.send('/youpi/process/plugin/', post);
	}
};
