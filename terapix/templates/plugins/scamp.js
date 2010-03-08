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

// Global vars
var ims;
var advTable;
var ldac_table;
var ldac_table_active_selections = new Array();
var ldac_selection_last_idx;
var xmlParser;

// Used in checkForSelectionLDACData()
var {{ plugin.id }}_curSelectionIdx = 0;
var uidscamp = '{{ plugin.id }}';

var {{ plugin.id }} = {
	/*
	 * Variable: aheadPath
	 * Data path to .ahead files
	 *
	 */
	aheadPath: null,
	/*
	 * Variable: LdacError
	 * Not null if any LDAC check error
	 *
	 */
	LdacError: 0,
	/*
	 * Function: reprocessCalibration
	 * Schedule a Swarp reprocessing
	 *
	 * Parameters:
	 *	taskId - string: DB task ID
	 *
	 */ 
	reprocessCalibration: function(taskId) {
		var r = new HttpRequest(
				null,
				null,	
				// Custom handler for results
				function(resp) {
					data = resp.result;
					var total = eval(data.idList)[0].length;

					var userData = $H(data);
					userData.set('config', 'The one used for this Scamp processing');
					userData.set('taskId', taskId);

					// Add to the processing cart
					var p_data = {	plugin_name	: uidscamp,
									userData 	: userData,
					};
				
					s_cart.addProcessing(p_data, function() {
						document.fire('notifier:notify', 'Scamp scheduled for reprocessing (' + total + ' ' + (total > 1 ? 'images' : 'image') + 
							') and added to the processing cart.');
					});
				}
		);

		var post = { Plugin: '{{ plugin.id }}',
					 Method: 'getReprocessingParams',
					 TaskId: taskId
		};
		r.send('/youpi/process/plugin/', getQueryString(post));
	},

	/*
	 * Function: addSelectionToCart
	 *
	 */
	addSelectionToCart: function() {
		// Global var
		{{ plugin.id }}_curSelectionIdx = 0;
		{{ plugin.id }}.LdacError = 0;
	
		var container = emptyContainer('menuitem_sub_4');
		var pre = new Element('pre');
		container.insert(pre);
	
		var log = new Logger(pre);
	
		// CHECK 1: list of selections check
		log.msg_status('Please note that these tests DO NOT CHECK that LDAC files are available on disks!');
		log.msg_status('Checking list of selections...');
	
		sels = ims.getListsOfSelections();
		if (!sels) {
			log.msg_error('No images selected. Nothing to add to cart !', true);
			return;
		}
	
		var total = ims.getImagesCount();
		log.msg_ok('Found ' + total + ' image' + (total > 1 ? 's' : '') + ' in selection.');
	
		// CHECK 2: get config file
		var cSel = $('{{ plugin.id }}_config_name_select');
		var config = cSel.options[cSel.selectedIndex].text;
		log.msg_status("Using '" + config + "' as configuration file");

		// CHECK 3: check for mandatory .ahead data path
		// MANDATORY PATHS
		var mandvars = selector.getMandatoryPrefixes();
		var mandpaths = new Array();
		for (var k=0; k < mandvars.length; k++) {
			var selNode = $(uidscamp + '_' + mandvars[k] + '_select');
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
				log.msg_error("No " + mandvars[k] + " data path selected (mandatory). Please <a href=\"#\" onclick=\"menu.activate(1);\">select a data path first</a>.");
				return;
			}
		}
		{{ plugin.id }}.aheadPath = mandpaths[0];
	
		// CHECK 4: custom output directory
		var output_data_path = {{ plugin.id }}.getOutputDataPath();
		log.msg_status("Using output data path '" + output_data_path + "'");
	
		// CHECK 5: checks for LDAC/AHEAD data
		log.msg_status("Deeper selection(s) checks for LDAC/AHEAD data...");
		{{ plugin.id }}.checkForSelectionLdacAheadData(pre);
	},

	getOutputDataPath: function() {
		var custom_dir = $('output_path_input').value;
		var output_data_path = '{{ processing_output }}{{ user.username }}/{{ plugin.id }}/';
	
		if (custom_dir && custom_dir.replace(/\ /g, '').length) {
			custom_dir = custom_dir.replace(/\ /g, '');
			if (custom_dir.length) {
				output_data_path += custom_dir + '/';
			}
		}
	
		return output_data_path;
	},

	/*
	 * Function: checkForSelectionLdacAheadData
	 * Check if every images in that selection has associated LDAC data
	 *
	 * Parameters:
	 *  container - DOM element: DOM block container
	 *
	 */ 
	checkForSelectionLdacAheadData: function(container) {
		var div = new Element('div');
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
					div.update();
					missing = resp.result.missing;
	
					if (missing.length > 0) {
						log.msg_warning('Missing LDAC/AHEAD data for selection ' + ({{ plugin.id }}_curSelectionIdx+1) + 
							' (' + missing.length + ' image' + (missing.length > 1 ? 's' : '') + ' failed!)');
						{{ plugin.id }}.LdacError = 1;

						var mdiv = new Element('div').setStyle({
							marginLeft: '20px', 
							maxHeight: '100px', 
							overflow: 'auto',
							width: '50%'
						}).addClassName('warning');
						log.insert(mdiv);
						missing.each(function(image) {
							// Missing files list
							image[1].each(function(file) {
								var fspan = new Element('span').addClassName('file').update({{ plugin.id }}.aheadPath + file);
								mdiv.insert('Missing file ').insert(fspan).insert(new Element('br'));
							});
						});
					}	
					else {
						log.msg_ok('LDAC/AHEAD data for selection ' + ({{ plugin.id }}_curSelectionIdx+1) + 
							' (' + idList.length + ' image' + (idList.length > 1 ? 's' : '') + ') is OK');
					}
	
					{{ plugin.id }}_curSelectionIdx++;
	
					if ({{ plugin.id }}_curSelectionIdx < selArr.length) {
						{{ plugin.id }}.checkForSelectionLDACData(container);
					}
					else {
						if ({{ plugin.id }}.LdacError) {
							log.msg_error('Missing LDAC/AHEAD information. Selection(s) not added to cart!', true);
							return;
						}
	
						// Now LDAC fine-grain selection can take place
						var r = confirm('Do you want to manually refine LDAC selections? If not, the current\nselections will be added ' +
										'to the cart now for processing.');
						if (r) {
							log.msg_status('Please select the LDAC files you want to use for scamp processing');
							{{ plugin.id }}.manualLDACSelection(div);
							
							return;
						}
	
						{{ plugin.id }}.do_addSelectionToCart(sels);
					}
				}
		);
	
		var post = {
			Plugin: uidscamp,
			Method: 'checkForSelectionLdacAheadData',
			IdList: idList.toString(),
			AheadPath: {{ plugin.id }}.aheadPath
		};
		// Send query
		r.setBusyMsg('Checking selection ' + ({{ plugin.id }}_curSelectionIdx+1) + ' (' + idList.length + ' images)');
		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	},

	do_addSelectionToCart: function(selIds) {
		var cSel = $('{{ plugin.id }}_config_name_select');
		var config = cSel.options[cSel.selectedIndex].text;
		var output_data_path = {{ plugin.id }}.getOutputDataPath();

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
	
		var data = 	{
			config: config,
			idList: selIds,
			resultsOutputDir: output_data_path,
			aheadPath: {{ plugin.id }}.aheadPath
		};

		// Finally, add to the processing cart
		p_data = {	plugin_name	: uidscamp,
					userData 	: data
		};
	
		// Add entry into the processing cart
		s_cart.addProcessing(	p_data,
								// Custom handler
								function() {
									msg = totalSels + ' selection' + (totalSels > 1 ? 's' : '') + ' (' + totalImgs + 
										' image' + (totalImgs > 1 ? 's' : '') + ') ha' + (totalSels > 1 ? 've' : 's') + 
										' been\nadded to the cart.';
									document.fire('notifier:notify', msg);
								}
		);
	},

	manualLDACSelection: function(container) {
		var sels = ims.getListsOfSelections();
		var selArr = eval(sels);
		ldac_selection_last_idx = 0;
	
		ldac_table = new AdvancedTable();
		ldac_table.setContainer('ldac_selection_div');
		ldac_table.setHeaders(['LDAC files to use']);
		ldac_table.setRowIdsFromColumn(0);
		ldac_table.attachEvent('onRowClicked', 
			function(checked) { 
				{{ plugin.id }}.LDACSaveCurrentSelection();
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
			opt.setAttribute('onclick', "{{ plugin.id }}.renderLDACSelection(" + parseInt(k) + ")");
		}
		
		var ldac_tab = new Element('table');
		ldac_tab.setAttribute('style', 'width: 100%;');
		var tr, td;
		tr = new Element('tr');
		td = new Element('td');
	
		ldac_tab.appendChild(tr);
		tr.appendChild(td);
		container.appendChild(ldac_tab);
	
		var ldac_choice_div = new Element('div');
		ldac_choice_div.appendChild(selNode);
		td.appendChild(ldac_choice_div);
	
		var ldac_opt_div = new Element('div');
		ldac_opt_div.setAttribute('style', 'vertical-align: middle;');
		td.appendChild(ldac_opt_div);
	
		// Select all
		var sub = new Element('input');
		sub.setAttribute('style', 'float: left;');
		sub.setAttribute('type', 'button');
		sub.setAttribute('value', 'Select all');
		sub.setAttribute('onclick', 'ldac_table.selectAll(true); {{ plugin.id }}.LDACSaveCurrentSelection();');
		ldac_opt_div.appendChild(sub);
			
		// Unselect all
		sub = new Element('input');
		sub.setAttribute('style', 'float: left; margin-left: 10px;');
		sub.setAttribute('type', 'button');
		sub.setAttribute('value', 'Unselect all');
		sub.setAttribute('onclick', 'ldac_table.selectAll(false); {{ plugin.id }}.LDACSaveCurrentSelection();');
		ldac_opt_div.appendChild(sub);
	
		// Add to cart button
		var addc = new Element('img');
		addc.setAttribute('style', 'cursor: pointer; float: right;');
		addc.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/misc/add_to_cart.png');
		addc.setAttribute('onclick', "{{ plugin.id }}.do_addSelectionToCart();");
		ldac_opt_div.appendChild(addc);
			
		td = new Element('td');
		var ldac_selection_div = new Element('div');
		ldac_selection_div.setAttribute('id', 'ldac_selection_div');
		td.appendChild(ldac_selection_div);
		tr.appendChild(td);
		
		{{ plugin.id }}.renderLDACSelection(0);
	},

	LDACSaveCurrentSelection: function() {
		var idSel = ldac_table.getSelectedColsValues();
		if (idSel) {
			idSel = idSel.split(',');
			for (var k=0; k < idSel.length; k++) {
				idSel[k] = ldac_table.getRowIdPrefix() + idSel[k];
			}
			ldac_table_active_selections[ldac_selection_last_idx] = String(idSel);
		}
		else
			ldac_table_active_selections[ldac_selection_last_idx] = '';
	},

	renderLDACSelection: function(idx) {
		var sels = ims.getListsOfSelections();
		var selArr = eval(sels);
	
		if (typeof idx != 'number') {
			alert('renderLDACSelection: idx must be an integer!');
			return;
		}
	
		// Save current selection status (thus it can be restaured later)
		if (ldac_table.rowCount())
			{{ plugin.id }}.LDACSaveCurrentSelection();
	
		ldac_selection_last_idx = idx;
	
		var container = $(ldac_table.getContainer());
		var xhr = new HttpRequest(
				container,
				null,	
				// Custom handler for results
				function(resp) {
					var d = resp['result'];
	
					container.update();
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
	
		var post = {
			Plugin: uidscamp,
			Method: 'getLDACPathsFromImageSelection',
			IdList: selArr[idx].toString(),
			AheadPath: {{ plugin.id }}.aheadPath
		};

		xhr.send('/youpi/process/plugin/', $H(post).toQueryString());
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
		var silent = typeof silent == 'boolean' ? silent : false;
		var txt = '';
		var runopts = get_runtime_options(trid);
		var logdiv = $('master_condor_log_div');
		
		// Hide action controls
		var tds = $(trid).select('td');
		delImg = tds[0].select('img')[0].hide();
		runDiv = tds[1].select('div.submitItem')[0].hide();
		otherImgs = tds[1].select('img');
		otherImgs.invoke('hide');
	
		var r = new HttpRequest(
				logdiv,
				null,	
				// Custom handler for results
				function(resp) {
					r = resp['result'];
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
		opts.set('Plugin', uidscamp);
		opts.set('Method', 'process');
		opts.set('ReprocessValid', (runopts.reprocessValid ? 1 : 0));
		opts = opts.merge(runopts.clusterPolicy.toQueryParams());
	
		r.send('/youpi/process/plugin/', opts.toQueryString());
	},

	reprocessAllFailedProcessings: function(tasksList) {
		alert('TODO...');
	},

	renderOutputDirStats: function(container_id) {
		var container = $(container_id);
		container.innerHTML = '';
	
		// global var defined in results.html
		var resp = output_dir_stats_data;
		var stats = resp['Stats'];
	
		var tab = new Element('table');
		tab.setAttribute('class', 'output_dir_stats');
		var tr,th,td;
		var tr = new Element('tr');
		// Header
		var header = ['Task success', 'Task failures', 'Total processings'];
		var cls = ['task_success', 'task_failure', 'task_total'];
		for (var k=0; k < header.length; k++) {
			th = new Element('th');
			th.setAttribute('class', cls[k]);
			th.setAttribute('colspan', '2');
			th.appendChild(document.createTextNode(header[k]));
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
	},

	saveItemForLater: function(trid, opts, silent) {
		opts = $H(opts);
		opts.set('Plugin', uidscamp);
		opts.set('Method', 'saveCartItem');

		var r = new HttpRequest(
				'result',
				null,	
				// Custom handler for results
				function(resp) {
					document.fire('notifier:notify', 'Scamp item saved successfully');
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
				}
		);
	
		r.send('/youpi/process/plugin/', opts.toQueryString());
	},

	/*
	 * Displays custom result information. 'resp' contains 
	 * server-side info to display
	 *
	 */
	resultsShowEntryDetails: function(container_id) {
		var tr, th, td;
		// See templates/results.html, function showDetails(...)
		// Global variable
		var resp = currentReturnedData;
		if (!resp) return;
	
		var container = $(container_id);
		var d = new Element('div');
		if (resp.Error) {
			container.addClassName('perm_not_granted');
			container.update(resp.Error);
			return;
		}
		container.removeClassName('perm_not_granted');

		d.setAttribute('class', 'entryResult');
		var tab = new Element('table');
		tab.setAttribute('class', 'fileBrowser');
		tab.setAttribute('style', 'width: 100%');
	
		tr = new Element('tr');
		th = new Element('th');
		th.appendChild(document.createTextNode(resp['Title']));
		tr.appendChild(th);
		tab.appendChild(tr);
		d.appendChild(tab);
		container.appendChild(d);
	
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
		tab2.setAttribute('class', 'scamp-result-entry-params');
		td.appendChild(tab2);
		tr.appendChild(td);
		tab.appendChild(tr);
	
		// Thumbnails when successful
		if (resp['Success']) {
			tr = new Element('tr');
			tr.setAttribute('class', 'scamp-result-entry-tn');
			td = new Element('td');
			td.setAttribute('onclick', "window.open('" + resp.WWW + resp.Index + "');");
			td.setAttribute('onmouseover', "this.setAttribute('class', 'scamp-result-entry-complete-on');");
			td.setAttribute('onmouseout', "this.setAttribute('class', 'scamp-result-entry-complete-off');");
			td.setAttribute('class', 'scamp-result-entry-complete-off');
			td.appendChild(document.createTextNode('See Scamp XML file'));
			tr.appendChild(td);
	
			td = new Element('td');
			var tns = resp['Previews'];
			var tn, imgpath, a;
			for (var k=0; k < tns.length; k++) {
				imgpath = resp['WWW'] + tns[k];
				a = Builder.node('a', {
					href: imgpath.replace(/tn_/, ''),
					rel: 'lightbox[scamp]'
				});

				tn = Builder.node('img', {
					src: resp['HasThumbnails'] ? imgpath : imgpath.replace(/tn_/, ''),
					'class' : 'scamp-result-entry-tn'
				}).hide();
				// Adds a cool fade-in effect
				$(tn).appear({duration: k/3});
	
				if (!resp['HasThumbnails'])
					tn.setAttribute('width', '60px');
	
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

		// Condor Job Logs
		tr = new Element('tr');
		td = new Element('td', {colspan: 2}).setStyle({padding: '0px'});
		td.update(ResultsHelpers.getCondorJobLogsEntry(resp.ClusterId, resp.TaskId));
		tr.insert(td);
		tab2.insert(tr);

		// Scamp processing history
		// Header title
		var hists = resp.History;
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.appendChild(document.createTextNode('Scamp processing history (' + hists.length + ')'));
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
	

		hists.each(function(hist) {
			tr = new Element('tr');
			// Emphasis of current history entry
			if (resp.TaskId == hist.TaskId) {
				tr.setAttribute('class', 'history-current');
			}
	
			// Icon
			td = new Element('td');
			var src = hist.Success ? 'success' : 'error';
			var img = new Element('img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif'});
			td.insert(img);
			tr.insert(td);
	
			// Date-time, duration
			td = new Element('td');
			var a = new Element('a', {href: '/youpi/results/{{ plugin.id }}/' + hist.TaskId + '/'});
			a.insert(hist.Start + ' (' + hist.Duration + ')');
			td.insert(a);
			tr.insert(td);
	
			// Hostname
			td = new Element('td');
			td.insert(hist.Hostname);
			tr.insert(td);
	
			// User
			td = new Element('td');
			td.insert(hist.User);
			tr.insert(td);
	
			// Reprocess option
			td = new Element('td', {'class': 'reprocess'});
			img = new Element('img', { src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/reprocess.gif'});
			img.taskId = hist.TaskId;
			img.observe('click', function() {
				{{ plugin.id }}.reprocessCalibration(this.taskId);
			});
			td.insert(img);
			tr.insert(td);
	
			htab.insert(tr);
		});
	
		// Scamp run parameters
		// Image
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.appendChild(document.createTextNode('Scamp run parameters'));
		tr.appendChild(td);
		tab2.appendChild(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.appendChild(document.createTextNode('Input LDAC files (' + resp['LDACFiles'].length + '):'));
		tr.appendChild(td);
	
		td = new Element('td');
		var ldac_div = new Element('div');
		ldac_div.setAttribute('class', 'min_size');
		td.appendChild(ldac_div);
		for (var k=0; k < resp['LDACFiles'].length; k++) {
			ldac_div.appendChild(document.createTextNode(resp['LDACFiles'][k]));
			ldac_div.appendChild(new Element('br'));
		}
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		// Path to .ahead files
		tr = new Element('tr');
		td = new Element('td', {nowrap: 'nowrap'});
		td.insert('Ahead path:');
		tr.appendChild(td);
	
		td = new Element('td');
		td.insert(resp.AheadPath);
		tr.insert(td);
		tab2.insert(tr);

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
	
		// Scamp Config file
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		if (resp['Success']) {
			td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		}
		var cdiv = new Element('div');
		cdiv.setAttribute('id', 'config-' + resp['TaskId']);
		cdiv.setAttribute('class', 'config_file');
		var pre = new Element('pre');
		pre.appendChild(document.createTextNode(resp['Config']));
		cdiv.appendChild(pre);
		tr.appendChild(td);
		tab2.appendChild(tr);

		var confbox = new DropdownBox(td, 'Toggle Scamp config file view');
		$(confbox.getContentNode()).insert(cdiv);
	
		// Error log file when failure
		if (!resp['Success']) {
			tr = new Element('tr');
			td = new Element('td');
			td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
			td.setAttribute('colspan', '2');
			var but = new Element('input');
			but.setAttribute('type', 'button');
			but.setAttribute('value', 'Toggle error log file view');
			but.setAttribute('onclick', "toggleDisplay('log-" + resp['TaskId'] + "');");
			td.appendChild(but);
			var cdiv = new Element('div');
			cdiv.setAttribute('id', 'log-' + resp['TaskId']);
			cdiv.setAttribute('style', 'height: 200px; overflow: auto; background-color: black; padding-left: 5px; display: none')
			var pre = new Element('pre');
			pre.appendChild(document.createTextNode(resp['Log']));
			cdiv.appendChild(pre);
			td.appendChild(cdiv);
			tr.appendChild(td);
			tab2.appendChild(tr);
	
			return;
		}
	
		// XML Filtering 
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.appendChild(document.createTextNode('XML Filtering'));
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		var d = new Element('div');
		d.setAttribute('style', 'padding: 10px;');
		d.setAttribute('id', '{{ plugin.id }}_xml_div');
		td.appendChild(d);
		tr.appendChild(td);
		tab2.appendChild(tr);
	
		xmlParser = new ScampXMLParser(resp['TaskId'], d, 'xmlParser');
	},

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
					var total = resp['result'].length;
					if (total == 0) {
        	            div.update('No saved item');
						return;
					}
					var table = new Element('table');
					table.setAttribute('class', 'savedItems');
					var tr, th;
					tr = new Element('tr');
					var header = ['Date', 'Permissions', 'Name', '# images', 'Config', 'Action'];
					for (var k=0; k < header.length; k++) {
						th = new Element('th');
						th.appendChild(document.createTextNode(header[k]));
						tr.appendChild(th);
					}
					table.appendChild(tr);
	
					var delImg, trid;
					var tabi, tabitr, tabitd;
					var idList, txt;
					resp.result.each(function(res, k) {
						idLists = res.idList.evalJSON();
						trid = uidscamp + '_saved_item_' + k + '_tr';
						tr = new Element('tr', {id: trid});

						delImg = new Element('img', {	id: uidscamp + '_del_saved_item_' + k,
														'style': 'margin-right: 5px', 
														src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/delete.png'
						}).hide();
	
						// Date
						td = new Element('td').update(res.date);
						tr.insert(td);

						// Permissions
						td = new Element('td', {'class': 'config'}).update(get_permissions('cartitem', res.itemId, function(r, imgId) {
							// imgId is the misc parameter passed to get_permissions()
							var img = $(imgId);
							r.currentUser.write ? img.show() : img.hide();
						}, delImg.readAttribute('id') /* Misc data */));
						tr.insert(td);
	
						// Name
						td = new Element('td', {'class': 'name'}).update(res.name);
						tr.insert(td);
	
						// Images count
						td = new Element('td', {'class': 'imgCount'});
						var sp = new Element('span', {'style': 'font-weight: bold; text-decoration: underline;'});
						sp.update(idLists.length > 1 ? 'Batch' : 'Single');
						td.insert(sp).insert(new Element('br'));

						idLists.each(function(idList) {
							td.insert(idList.length).insert(new Element('br'));
						});
						tr.insert(td);
	
						// Config
						td = new Element('td', {'class': 'config'}).update(res.config);
						tr.insert(td);
	
						// Delete
						td = new Element('td');
						delImg.c_data = {trid: trid, name: res.name};
						delImg.observe('click', function() {
							var trid = this.c_data.trid;
							var name = this.c_data.name;
							boxes.confirm("Are you sure you want to delete saved item '" + name + "'?", function() {
								{{ plugin.id }}.delSavedItem(trid, name);
							});
						});
						td.insert(delImg);

						var addImg = new Element('img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.png'});
						addImg.c_data = $H(res);
						addImg.observe('click', function() {
							{{ plugin.id }}.addToCart(this.c_data);
						});
						td.insert(addImg);

						tr.insert(td);
						table.insert(tr);
					});
					div.appendChild(table);
				}
		);
	
		var post = 	'Plugin={{ plugin.id }}&Method=getSavedItems';
		r.send('/youpi/process/plugin/', post);
	},

	delSavedItem: function(trid, name) {
		var trNode = $(trid);
		var r = new HttpRequest(
				uidscamp + '_result',
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
									if (last) eval(uidscamp + '.showSavedItems()');

									// Notify user
									document.fire('notifier:notify', "Item '" + name + "' successfully deleted");
								}
							});
						}
					});
				}
		);
	
		var post = {
			'Plugin': uidscamp,
			'Method': 'deleteCartItem',
			'Name'	: name
		};

		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	},

	addToCart: function(data) {
		var p_data = {	plugin_name : uidscamp,
						userData :	data
		};

		s_cart.addProcessing(p_data, function() {
			window.location.reload();
		});
	},

	selectImages: function() {
		var root = $('menuitem_sub_0');
		root.writeAttribute('align', 'center');
	
		// Container of the ImageSelector widget
		var div = new Element('div', {id: 'results_div', align: 'center'}).setStyle({paddingTop: '20px', width: '90%'});
		root.insert(div);
	
		ims = new ImageSelector('results_div');
		ims.setTableWidget(new AdvancedTable());
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
		var selDiv = new Element('div');
		selDiv.setAttribute('class', 'selectionModeTitle');
		selDiv.appendChild(document.createTextNode(txt + ' selection mode:'));
		container.appendChild(selDiv);
	
		selDiv = new Element('div');
		selDiv.setAttribute('class', 'listsOfSelections');
	
		for (var k=0; k < idList.length; k++) {
			c = idList[k].toString().split(',').length;
			if (idList.length > 1)
				selDiv.appendChild(document.createTextNode('Selection ' + (k+1) + ': ' + c + ' image' + (c > 1 ? 's' : '')));
			else
				selDiv.appendChild(document.createTextNode(c + ' image' + (c > 1 ? 's' : '')));
			selDiv.appendChild(new Element('br'));
		}
		container.appendChild(selDiv);
	},

	reprocess_ldac_selection: function(ldac_files, taskId) {
		var container = $('{{ plugin.id }}_xml_fields_result_div');
	
		var xhr = new HttpRequest(
			container,
			null,	
			// Custom handler for results
			function(resp) {
				var d = resp['result'];
				container.innerHTML = '';
				var log = new Logger(container);
				log.msg_status('Adding to processing cart...');
				var totalSels = d['IdList'].length;
				var idList = '[[';
				for (var k=0; k < d['IdList'].length; k++) {
					idList += d['IdList'][k] + ',';
				}
				idList = idList.substr(0, idList.length-1) + ']]';
	
				// Add to cart
				p_data = {	plugin_name	: 	'{{ plugin.id }}', 
							userData 	: 	{	config : 'The one used for this Scamp processing',
												idList : idList,
												taskId : d.TaskId,
												resultsOutputDir : d.ResultsOutputDir,
							}
				};
	
				// Add entry into the processing cart
				s_cart.addProcessing(	p_data,
										// Custom handler
										function() {
											msg = totalSels + ' LDAC file' + (totalSels > 1 ? 's' : '') + ' ha' + 
												(totalSels > 1 ? 've' : 's') + ' been added to the cart.';
											log.msg_ok(msg);
										}
				);
			}
		);
	
		var post = 'Plugin={{ plugin.id }}&Method=getImgIdListFromLDACFiles&TaskId=' + taskId + '&LDACFiles=' + ldac_files;
		xhr.setBusyMsg('Adding subselection to processing cart');
		xhr.send('/youpi/process/plugin/', post);
	}
};

/*
 * Class: ScampXMLParser
 * Scamp XML Parser facilities
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <FileBrowser> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *
 * taskId - string or int: processing task Id
 * container - string, DOM node: parent container
 *
 */
function ScampXMLParser(taskId, container) {
	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _rowIdx
	 * Current row index in table
	 *
	 */
	var _rowIdx = 0;


	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */
	var _container;
	/*
	 * Var: _taskId
	 * Processing task Id
	 *
	 */
	var _taskId;
	/*
	 * Var: _fields
	 * Array of available FIELDS element in XML file
	 *
	 * Format:
	 *  [['Field1', 'Type1'], ...]
	 *
	 */
	var _fields;
	/*
	 * Var: _fieldNames
	 * Array of available FIELDS (names only)
	 *
	 * Format:
	 *  ['Field1', 'Field2', ...]
	 *
	 */
	var _fieldNames;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _error
	 * Displays custom error message
	 *
	 */ 
	function _error(msg) {
		console.error(msg);
	}

	/*
	 * Function: _renderFrom
	 * Renders form when XML file has been found
	 *
	 */ 
	function _renderForm() {
		var xhr = new HttpRequest(
			container,
			null,	
			// Custom handler for results
			function(resp) {
				var d = resp['result'];
				_fields = d['Fields'];
				_container.innerHTML = '';

				_fieldNames = new Array();
				for (var k=0; k < _fields.length; k++) {
					_fieldNames[k] = _fields[k][0];
				}

				var tab = new Element('table');
				tab.setAttribute('id', '{{ plugin.id }}_xml_fields_tab');
				_container.appendChild(tab);

				// Add first line
				_addRow();

				var div = new Element('div');
				div.setAttribute('style', 'text-align: right;');
				var but = new Element('input');
				but.setAttribute('type', 'button');
				but.setAttribute('value', 'Find Matches');
				but.setAttribute('onclick', 'xmlParser.submitQuery()');
				div.appendChild(but);
				_container.appendChild(div);

				// Result div
				rdiv = new Element('div');
				rdiv.setAttribute('id', '{{ plugin.id }}_xml_fields_result_div');
				_container.appendChild(rdiv);
			}
		);

		var post = 'Plugin={{ plugin.id }}&Method=parseScampXML&TaskId=' + _taskId;
		xhr.setBusyMsg('Build form widget');
		xhr.send('/youpi/process/plugin/', post);
	}

	this.addRow = function() {
		_addRow();
	}

	this.submitQuery = function() {
		var container = $('{{ plugin.id }}_xml_fields_result_div');
		container.setAttribute('style', 'border-top: 3px solid #5b80b2; margin-top: 10px; padding-top: 5px;');
		var tab = $('{{ plugin.id }}_xml_fields_tab');
		var trs = tab.getElementsByTagName('tr');
		var query = new Array();
		for (var k=0; k < trs.length; k++) {
			var tds = trs[k].getElementsByTagName('td');
			var sel = tds[2].firstChild;
			var condSel = tds[3].firstChild;
			var idx = sel.selectedIndex;
			var type = _fields[idx][1];

			query[k] = new Array();
			query[k][0] = sel.selectedIndex;
			query[k][1] = condSel.selectedIndex;
			type != 'boolean' ? query[k][2] = tds[4].firstChild.value : query[k][2] = '';
		}

		var xhr = new HttpRequest(
			container,
			null,	
			// Custom handler for results
			function(resp) {
				var d = resp['result'];
				ldac_files = d['LDACFiles'];
				if (!ldac_files.length) {
					container.innerHTML = '';
					var idiv = new Element('div');
					idiv.setAttribute('class', 'tip');
					idiv.setAttribute('style', 'width: 30%;');
					idiv.appendChild(document.createTextNode('No LDAC files found matching\nthese criteria.'));
					container.appendChild(idiv);
					return;
				}
					
				container.innerHTML = '';
				log = new Logger(container);
				log.msg_ok(ldac_files.length + ' LDAC file' + (ldac_files.length > 1 ? 's' : '') + ' matched');
				var ldiv = new Element('div');
				ldiv.setAttribute('style', 'height: 100px; overflow: auto; width: 500px;');
				for (var k=0; k < ldac_files.length; k++) {
					ldiv.appendChild(document.createTextNode(d['DataPath'] + '/' + ldac_files[k]));
					ldiv.appendChild(new Element('br'));
				}
				container.appendChild(ldiv);

				// Button div
				var bdiv = new Element('div');
				bdiv.setAttribute('style', 'text-align: right;');
				var img = new Element('img');
				img.setAttribute('style', 'cursor: pointer;');
				img.setAttribute('onclick', "{{ plugin.id }}.reprocess_ldac_selection('" + ldac_files + "'," + d['TaskId'] + ");");
				img.setAttribute('src', '/media/themes/{{ user.get_profile.guistyle }}/img/misc/reprocess.gif');
				bdiv.appendChild(img);
				container.appendChild(bdiv);
			}
		);

		var post = 'Plugin={{ plugin.id }}&Method=processQueryOnXML&Query=' + query + '&TaskId=' + _taskId;
		xhr.setBusyMsg('Sending query');
		xhr.send('/youpi/process/plugin/', post);
	}

	function _addRow() {
		var tr, td;
		var tab = $('{{ plugin.id }}_xml_fields_tab');
		var type = _fields[0][1];

		tr = new Element('tr');
		tab.appendChild(tr);
		tr.setAttribute('id', '{{ plugin.id }}_xml_fields_tr_' + _rowIdx);

		// - button
		td = new Element('td');
		if (_rowIdx > 0) {
			var addb = new Element('input');
			addb.setAttribute('type', 'button');
			addb.setAttribute('value', '-');
			addb.setAttribute('onclick', "xmlParser.removeRow(" + _rowIdx + ");");
			td.appendChild(document.createTextNode('and '));
			td.appendChild(addb);
		}
		tr.appendChild(td);

		// + button
		td = new Element('td');
		addb = new Element('input');
		addb.setAttribute('type', 'button');
		addb.setAttribute('value', '+');
		addb.setAttribute('onclick', "xmlParser.addRow();");
		td.appendChild(addb);
		tr.appendChild(td);

		td = new Element('td');
		var sel = getSelect('{{ plugin.id }}_xml_fields_select_' + _rowIdx, _fieldNames);
		sel.setAttribute('onchange', "xmlParser.selectionHasChanged(" + _rowIdx + ");");
		td.appendChild(sel);
		tr.appendChild(td);

		// Condition
		td = new Element('td');
		td.setAttribute('id', '{{ plugin.id }}_xml_fields_cond_td_' + _rowIdx);
		td.appendChild(_getTypeSelect(type));
		tr.appendChild(td);

		// Text field
		td = new Element('td');
		td.setAttribute('id', '{{ plugin.id }}_xml_fields_text_td_' + _rowIdx);
		if (type != 'boolean') {
			var txt = new Element('input');
			txt.setAttribute('type', 'text');
			txt.setAttribute('size', '30');
			td.appendChild(txt);
			txt.focus();
		}
		tr.appendChild(td);

		_rowIdx++;
	}

	this.removeRow = function(rowIdx) {
		var tr = $('{{ plugin.id }}_xml_fields_tr_' + rowIdx);
		tr.parentNode.removeChild(tr);
	}

	function _getTypeSelect(type) {
		var id, data;
		if (type == 'boolean') {
			id = '{{ plugin.id }}_xml_fields_cond_bool_select_';
			data = ['True', 'False'];
		}
		else if (type == 'int' || type == 'float' || type == 'double') {
			id = '{{ plugin.id }}_xml_fields_cond_number_select_';
			data = ['=', '<', '>', '<>'];
		}
		else if (type == 'char') {
			id = '{{ plugin.id }}_xml_fields_cond_char_select_';
			data = ['matches', 'is different from'];
		}

		return getSelect(id + _rowIdx, data);
	}

	this.selectionHasChanged = function(curRowIdx) {
		var sel = $('{{ plugin.id }}_xml_fields_select_' + curRowIdx);
		var idx = sel.selectedIndex;
		var type = _fields[idx][1];

		var cond = $('{{ plugin.id }}_xml_fields_cond_td_' + curRowIdx);
		removeAllChildrenNodes(cond);
		cond.appendChild(_getTypeSelect(type));

		var text = $('{{ plugin.id }}_xml_fields_text_td_' + curRowIdx);
		removeAllChildrenNodes(text);
		if (type != 'boolean') {
			var txt = new Element('input');
			txt.setAttribute('type', 'text');
			txt.setAttribute('size', '30');
			text.appendChild(txt);
			txt.focus();
		}
	}

	/*
	 * Function: _render
	 * Renders widget
	 *
	 */ 
	function _render() {
		var xhr = new HttpRequest(
			container,
			null,	
			// Custom handler for results
			function(resp) {
				var d = resp['result'];
				filePath = d['FilePath'];
				if (filePath == -1)
					_container.innerHTML = 'NOT Found!';
				else {
					// Form can be rendered
					_renderForm();
				}
			}
		);

		var post = 'Plugin={{ plugin.id }}&Method=checkIfXMLExists&TaskId=' + _taskId;
		xhr.setBusyMsg('Looking for Scamp XML output file');
		xhr.send('/youpi/process/plugin/', post);
	}

	function _main() {
		if (typeof container == 'string') {
			_container = $(container);
		}
		else
			_container = container;

		_taskId = taskId;
		_render();
	}

	_main();
}
