/*****************************************************************************
 *
 * Copyright (c) 2008-2011 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/

/*
 * Group: Swarp Plugin
 *
 * JS code for Swarp plugin.
 *
 */

// Defines various exceptions
var Exception = {
	WEIGHT_NOT_FOUND: 2000,
	HEAD_NOT_FOUND: 2001
};

var swarp = {
	id: 'swarp',
	/*
	 * Variable: autoProgressBar
	 * 
	 * Progress bar widget for automatic processing of selections
	 *
	 */
	autoProgressBar: null,
	/*
	 * Variable: autoCurSelectionImageCount
	 * 
	 * Image count in current image selection being processed in automatic mode
	 *
	 */
	autoCurSelectionImageCount: 0,
	/*
	 * Variable: autoSelections
	 * 
	 * Current selections in auto mode (array of 1 array of selections) for backward 
	 * compatibility with the <checkForQFITSData> function.
	 *
	 */
	autoSelections: new Array(),
	/*
	 * Variable: ims
	 * 
	 * <ImageSelector> instance
	 *
	 */
	ims: null,
	/*
	 * Variable: headDataPaths
	 * 
	 * Array: per-selection path to .head files
	 *
	 */
	headDataPaths: new Array(),
	/*
	 * Variable: curSelectionIdx
	 * Used by <checkForQFITSData> to mark the current selection
	 *
	 */
	curSelectionIdx: 0,
	/*
	 * Variable: weightMissingError
	 * Used by <checkForQFITSData>
	 *
	 */
	weightMissingError: false,
	/*
	 * Function: addSelectionToCart
	 *
	 */
	addSelectionToCart: function() {
		this.curSelectionIdx = 0;
		this.weightMissingError = false;
		sels = this.ims.getListsOfSelections();

		if (!sels) {
			alert('No images selected. Nothing to add to cart !');
			return;
		}

		// Used when using automatic searching of weight or head files
		var AUTO = 'AUTO';
		// Custom output directory
		var output_data_path = $('output_target_path').innerHTML;
	
		// Set mandatory structures
		var p_data = {	plugin_name : this.id, 
						userData : {resultsOutputDir: output_data_path}
		};

		// Finds weight path
		var wSel = $(this.id + '_weights_select');
		var weightPath = '';
		var path = wSel.options[wSel.selectedIndex].text;
		if (path != selector.getNoSelectionPattern()) {
			//weightPath = (path == selector.getExtra(0).title) ? 'QFits-generated weight maps' : path;
			weightPath = (path == selector.getExtra(0).title) ? 'AUTO' : path;
		}
		else {
			menu.activate(1);
			alert("Invalid data path selected for WEIGHT data.");
			wSel.up().up().pulsate();
			return;
		}
		
		// Finds head path
		var hSel = $(this.id + '_heads_select');
		var headPath = '';
		var path = hSel.options[hSel.selectedIndex].text;
		if (path != selector.getNoSelectionPattern()) {
			headPath = (path == selector.getExtra(1).title) ? 'AUTO' : path;
		}
		else {
			menu.activate(1);
			alert("Invalid data path selected for HEAD data.");
			hSel.up().up().pulsate();
			return;
		}

		var total = this.ims.getImagesCount();

		// Get config file
		var cSel = $(this.id + '_config_name_select');
		var config = cSel.options[cSel.selectedIndex].text;

		// Gets custom output directory
		var output_data_path = $('output_target_path').innerHTML;

		// Checks that all weight maps are available if EXTRA option has been selected
		var c = $('menuitem_sub_4').update();
		menu.activate(4);
		var pre = new Element('pre');
		c.insert(pre);
		var log = new Logger(pre);

		if (weightPath == AUTO) {
			// Use QFits weight maps from Youpi
			log.msg_status('Please note that these tests DO NOT CHECK that WEIGHT files are <b>physically</b> available on disks!');
			var sName = this.ims.getSavedSelectionUsed() ? "<span class=\"saved_selection_used\">" + this.ims.getSavedSelectionUsed() + "</span>" : "";
			log.msg_status("Will use output data path '" + output_data_path + "'");
			if (sName.length)
				log.msg_status("Using '" + sName + "' for image selection (" + total + ' image' + (total > 1 ? 's' : '') + ")");
			else
				log.msg_status("Found " + total + ' image' + (total > 1 ? 's' : '') + " selected");
			log.msg_status("Using '<span class=saved_selection_used>" + config + "</span>' as configuration file");
			log.msg_status('Checking <b>weight maps</b> availability (from QualityFITS)...');

			this.checkForQFITSData(pre, function() {
				// Reset
				this.curSelectionIdx = 0;
				if (headPath == AUTO) {
					// Automatic checks for Scamp: looks for Scamp-generated .head files
					// Now do Scamp-related checks
					this.checkForScampData(pre, function() {
						this.do_addSelectionToCart({
							useAutoQFITSWeights: 1,
							useAutoScampHeads: 1,
							config: config, 
							idList: sels, 
							weightPath: weightPath, 
							headPath: headPath, 
							resultsOutputDir: output_data_path,
							headDataPaths: this.headDataPaths.join(',')
						});
					}.bind(this));
				}
				else {
					log.msg_warning('Since you have choosen <i>a custom path</i> to HEAD data, <b>no checks for successful Scamp processings are ' +
						'made at this time</b>. ');
					log.msg_status("Will use HEAD path '" + headPath + "'");
					// Custom path to head files is provided
					this.do_addSelectionToCart({
						useAutoQFITSWeights: 1,
						useAutoScampHeads: 0,
						config: config, 
						idList: sels, 
						weightPath: weightPath, 
						headPath: headPath, 
						resultsOutputDir: output_data_path,
						headDataPaths: this.headDataPaths.join(',')
					});
				}
			}.bind(this));

			return;
		}
		else {
			// Custom path to weight maps provided
			log.msg_warning('Since you have choosen <i>a custom path</i> to WEIGHT data, <b>no checks for successful QFITS are ' +
				'made at this time</b>. ');
			log.msg_status("Will use WEIGHT path '" + weightPath + "'");
			var sName = this.ims.getSavedSelectionUsed() ? "<span class=\"saved_selection_used\">" + this.ims.getSavedSelectionUsed() + "</span>" : "";
			log.msg_status("Will use output data path '" + output_data_path + "'");
			if (sName.length)
				log.msg_status("Using '" + sName + "' for image selection (" + total + ' image' + (total > 1 ? 's' : '') + ")");
			else
				log.msg_status("Found " + total + ' image' + (total > 1 ? 's' : '') + " selected");
			log.msg_status("Using '<span class=saved_selection_used>" + config + "</span>' as configuration file");

			if (headPath == AUTO) {
				// Automatic checks for Scamp: looks for Scamp-generated .head files
				// Checks for Scamp processings (for .head files support)
				this.checkForScampData(pre, function() {
					this.do_addSelectionToCart({
						useAutoQFITSWeights: 0,
						useAutoScampHeads: 1,
						config: config, 
						idList: sels, 
						weightPath: weightPath, 
						headPath: headPath, 
						resultsOutputDir: output_data_path,
						headDataPaths: this.headDataPaths.join(',')
					});
				}.bind(this));
			}
			else {
				// Custom path to head files is provided
				log.msg_warning('Since you have choosen <i>a custom path</i> to HEAD data, <b>no checks for successful Scamp processings are ' +
					'made at this time</b>. ');
				log.msg_status("Will use HEAD path '" + headPath + "'");
				this.do_addSelectionToCart({
					useAutoQFITSWeights: 0,
					useAutoScampHeads: 0,
					config: config, 
					idList: sels, 
					weightPath: weightPath, 
					headPath: headPath, 
					resultsOutputDir: output_data_path,
					headDataPaths: this.headDataPaths.join(',')
				});
			}
		}
	},

	/*
	 * Function: adds current selection to processing cart
	 *
	 * Parameters:
	 *  data - object: user data to be saved
	 *  notify - boolean: Sends notification message after an item has been added to the PC [default: true]
	 *
	 */
	do_addSelectionToCart: function(data, notify) {
		var notify = typeof notify == 'boolean' ? notify : true;
		var total = cartmode.curMode == cartmode.mode.MANUAL ? this.ims.getImagesCount() : this.autoCurSelectionImageCount;

		// Add to the processing cart
		p_data = {	
			plugin_name	: this.id,
			userData 	: data
		};
	
		// Add entry into the processing cart
		s_cart.addProcessing(p_data,
			// Custom handler
			function() {
				if (notify) {
					document.fire('notifier:notify', 'The current image selection (' + total + ' ' + 
						(total > 1 ? 'images' : 'image') + ') has been\nadded to the cart.');
				}
			}
		);
	},

	/*
	 * Function: checkForQFITSData
	 * Check if every images in that selection has associated WEIGHT maps data
	 *
	 * Parameters:
	 *  container - DOM element: DOM block container
	 *  handler - function: custom handler executed once checks are successful
	 *
	 */ 
	checkForQFITSData: function(container, handler) {
		var handler = typeof handler == 'function' ? handler : null;
		var div = new Element('div');
		var log = new Logger(div);
		var sels, total;
		var selArr;

		if (cartmode.curMode == cartmode.mode.MANUAL) {
			sels = this.ims.getListsOfSelections();
			total = this.ims.getImagesCount();
			selArr = eval(sels);
		}
		else {
			selArr = this.autoSelections;
		}

		var idList = selArr[this.curSelectionIdx];
	
		div.setStyle({textAlign: 'left'});
		container.insert(div);
	
		var r = new HttpRequest(
				div,
				null,	
				// Custom handler for results
				function(resp) {
					div.update();
					missing = resp.result.missingQFITS;
	
					if (missing.length > 0) {
						log.msg_warning('Missing WEIGHT data for selection ' + (this.curSelectionIdx+1) + 
							' (' + missing.length + ' image' + (missing.length > 1 ? 's' : '') + ' failed!)');
						this.weightMissingError = true;
					}	
					else {
						log.msg_ok('WEIGHT data for selection ' + (this.curSelectionIdx+1) + 
							' (' + idList.length + ' image' + (idList.length > 1 ? 's' : '') + ') is OK');
					}
	
					this.curSelectionIdx++;
	
					if (this.curSelectionIdx < selArr.length) {
						this.checkForQFITSData(container, handler);
					}
					else {
						if (this.weightMissingError) {
							var c = new Element('div').setStyle({paddingLeft: '3px'});
							div.insert(c);
							var wm = new DropdownBox(c, 'View list of images with missing weight maps');
							var pre = new Element('pre').setStyle({
								color: 'brown',
								overflow: 'auto',
								maxHeight: '200px'
							});

							missing.each(function(miss) {
								pre.insert(miss + '<br/>');
							});
							wm.getContentNode().update(pre);

							log.msg_error('Missing WEIGHT information. Selection(s) not added to cart!', true);
							return;
						}

						// All checks are OK. Executes custom handler, if any
						if (handler) handler();
					}
				}.bind(this)
		);
	
		var post = 	'Plugin=' + this.id + '&' + 
					'Method=checkForQFITSData&' +
					'IdList=' + idList;
		// Send query
		r.setBusyMsg('Checking selection ' + (this.curSelectionIdx+1) + ' (' + idList.length + ' images)');
		r.send('/youpi/process/plugin/', post);
	},

	/*
	 * Function: checkForScampData
	 * Check if every images in that selection has associated .head file
	 *
	 * Parameters:
	 *  container - DOM element: DOM block container
	 *  handler - function: custom handler executed once checks are successful
	 *
	 */ 
	checkForScampData: function(container, handler) {
		var handler = typeof handler == 'function' ? handler : null;
		var div = new Element('div');
		var log = new Logger(div);
		var sels = this.ims.getListsOfSelections();
		var total = this.ims.getImagesCount();

		var selArr = eval(sels);
		var idList = selArr[this.curSelectionIdx];
	
		div.setStyle({textAlign: 'left'});
		container.insert(div);
	
		var r = new HttpRequest(
				div,
				null,	
				// Custom handler for results
				function(resp) {
					div.update();
					var res = resp.result;
					if (res.Warning) {
						log.msg_warning('Selection ' + (this.curSelectionIdx + 1) + ': ' + res.Warning);
						// Store empty path: no .head files
						this.headDataPaths.push('');

						this.curSelectionIdx++;
						if (this.curSelectionIdx < selArr.length)
							this.checkForScampData(container, handler);
						else {
							// No selection left. Executes final custom handler, if any
							if (handler) handler();
						}
					}
					else {
						log.msg_ok('Selection ' + (this.curSelectionIdx + 1) + ': found ' + res.Tasks.length + ' matches. Please ' +
							'select one in the list:');
						var dat = new Element('div').setStyle({
							width: '80%', 
							maxHeight: '130px', 
							overflow: 'auto',
							marginLeft: '15px'
						});
						var bdiv = new Element('div').setStyle({marginLeft: '15px'});

						var at = new AdvancedTable();
						at.setContainer(dat);
						at.setExclusiveSelectionMode(true);
						at.setRowIdsFromColumn(0);
						// Fill table
						res.Tasks.each(function(task) {
							at.appendRow(task);
						});

						// Registers rowClicked events
						at.attachEvent('onRowClicked', function() {
							var txt = this.curSelectionIdx == selArr.length - 1 ? 'Validate' : 'Validate and show next selection';
							var but = new Element('input', {type: 'button', value: txt});

							but.observe('click', function() {
								var dataPath = at.getRowData(at.getSelectedRows()[0])[4];
								// Store path
								this.headDataPaths.push(dataPath);

								// FIXME this.remove();
								dat.update();
								log.msg_ok('Selection ' + (this.curSelectionIdx + 1) + ': Will use <tt>' + 
									dataPath + '</tt> to access .head files');

								this.curSelectionIdx++;
								if (this.curSelectionIdx < selArr.length)
									this.checkForScampData(container, handler);
								else {
									// No selection left, executes final custom handler, if any
									if (handler) handler();
								}
							}.bind(this));
							bdiv.update(but);
						}.bind(this));

						div.insert(dat);
						div.insert(bdiv);
						at.render();
						return;
					}
				}.bind(this)
		);
	
		var post = {
			Plugin: this.id,
			Method: 'checkForScampData',
			IdList: idList
		}

		// Send query
		r.setBusyMsg('Running Scamp checks for selection ' + (this.curSelectionIdx+1) + ' (' + 
			idList.length + ' images)');
		r.send('/youpi/process/plugin/', $H(post).toQueryString());
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
		opts.set('Plugin', this.id);
		opts.set('Method', 'process');
		opts.set('ReprocessValid', (runopts.reprocessValid ? 1 : 0));
		opts = opts.merge(runopts.clusterPolicy.toQueryParams());

		r.send('/youpi/process/plugin/', opts.toQueryString());
	},

	reprocessAllFailedProcessings: function(tasksList) {
		alert('TODO...');
	},

	/*
	 * Function: reprocessStack
	 * Schedule a Swarp reprocessing
	 *
	 * Parameters:
	 *	taskId - string: DB task ID
	 *
	 */ 
	reprocessStack: function(taskId) {
		var r = new HttpRequest(
				null,
				null,	
				// Custom handler for results
				function(resp) {
					data = resp.result;
					var total = eval(data.idList)[0].length;

					var userData = $H(data);
					userData.set('config', 'The one used for this Swarp processing');
					userData.set('taskId', taskId);

					// Add to the processing cart
					var p_data = {	plugin_name	: this.id,
								userData 	: userData,
					};
				
					s_cart.addProcessing(	p_data,
											// Custom handler
											function() {
												alert('Swarp scheduled for reprocessing (' + total + ' ' + (total > 1 ? 'images' : 'image') + 
													') and\nadded to the processing cart.');
											}
					);
				}
		);

		var post = { Plugin: this.id,
					 Method: 'getReprocessingParams',
					 TaskId: taskId
		};
		r.send('/youpi/process/plugin/', getQueryString(post));
	},

	renderOutputDirStats: function(container_id) {
		var container = $(container_id).update();
	
		// global var defined in results.html
		var resp = output_dir_stats_data;
		var stats = resp['Stats'];
	
		var tab = new Element('table', {'class': 'output_dir_stats'});
		var tr,th,td;
		var tr = new Element('tr');
		// Headers
		var headers = $H({	task_success: 'Task success',
							task_failure: 'Task failures',
							task_total: 'Total processings'
		});
		headers.each(function(header) {
			th = new Element('th', {'class': header.key, 'colspan': '2'}).update(header.value);
			tr.insert(th);
		});
		tab.insert(tr);
	
		tr = new Element('tr');
		var val, percent, cls;
		headers.each(function(header, k) {
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
			var td = new Element('td', {'class': cls}).update(val);
			tr.insert(td);

			td = new Element('td', {'class': cls}).update(percent);
			tr.insert(td);
		});
		tab.insert(tr);
		container.insert(tab);
	},

	saveItemForLater: function(trid, opts, silent) {
		opts = $H(opts);
		opts.set('Plugin', this.id);
		opts.set('Method', 'saveCartItem');

		var runopts = get_runtime_options(trid);
		var r = new HttpRequest(
				this.id + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					document.fire('notifier:notify', 'Swarp item saved successfully');
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
		var resp = currentReturnedData;
		var container = $(container_id);
		if (resp.Error) {
			container.addClassName('perm_not_granted');
			container.update(resp.Error);
			return;
		}
		container.removeClassName('perm_not_granted');

		var d = new Element('div', {'class': 'entryResult'});
		var tab = new Element('table', {'class': 'fileBrowser', 'style': 'width: 100%'});
	
		tr = new Element('tr');
		th = new Element('th').update(resp['Title']);
		tr.insert(th);
		tab.insert(tr);
	
		// Duration
		var tdiv = new Element('div', {'class': 'duration'});
		tdiv.insert(resp['Start'] + '<br/>');
		tdiv.insert(resp['End'] + '<br/>');
		var src;
		resp['Success'] ? src = 'success' : src = 'error';
		var img = new Element(	'img', {src: '/media/themes/' + guistyle + '/img/admin/icon_' + src + '.gif',
										style: 'padding-right: 5px;'
		});
		tdiv.insert(img);
		tdiv.insert(resp.Duration + ' on').insert(new Element('br')).insert(resp.Hostname);
		tr = new Element('tr');
		td = new Element('td', {style: 'border-bottom: 2px #5b80b2 solid'});
		td.insert(tdiv);
		tr.insert(td);
		tab.insert(tr);
	
		// User
		var udiv = new Element('div', {'class': 'user'});
		udiv.insert('Job initiated by ' + resp['User']);
		udiv.insert(new Element('br'));
		udiv.insert('Exit status: ');
		udiv.insert(new Element('br'));
		var txt;
		resp['Success'] ? txt = 'success' : txt = 'failure';
		var exit_s = new Element('span', {'class': 'exit_' + txt}).update(txt);
		udiv.insert(exit_s);
		td.insert(udiv);
	
		tr = new Element('tr');
		td = new Element('td', {style: 'padding: 0px'});
		var tab2 = new Element('table', {'class': 'qfits-result-entry-params'});
		td.insert(tab2);
		tr.insert(td);
		tab.insert(tr);

		// Thumbnails when successful
		if (resp.Success) {
			tr = new Element('tr', {'class': 'scamp-result-entry-tn'});
			td = new Element('td', {
					onclick: "window.open('" + resp.WWW + resp.Index + "');",
					onmouseover: "this.setAttribute('class', 'scamp-result-entry-complete-on');",
					onmouseout: "this.setAttribute('class', 'scamp-result-entry-complete-off');",
					'class': 'scamp-result-entry-complete-off'
			});
			td.update('See Swarp XML file');
			tr.insert(td);
	
			td = new Element('td');
			var tn, imgpath, a;
			resp.Previews.each(function(thumb, k) {
				imgpath = resp.WWW + thumb;
				a = new Element('a', { href: imgpath.replace(/tn_/, ''), rel: 'lightbox[swarp]', title: 'Swarp bitmap of coadded images' });
				tn = new Element('img', {
					src: resp.HasThumbnails ? imgpath : imgpath.replace(/tn_/, ''),
					'class' : 'scamp-result-entry-tn'
				}).hide();
				// Adds a cool fade-in effect
				$(tn).appear({duration: k/3});
	
				if (!resp.HasThumbnails)
					tn.setAttribute('width', '60px');
	
				a.insert(tn);
				td.insert(a);
			});
			tr.insert(td);
			tab2.insert(tr);
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

		// Processing history
		// Header title
		var hist = resp.History;
		tr = new Element('tr');
		td = new Element('td', { colspan: 2, 'class': 'qfits-result-header-title'});
		td.insert('Swarp processing history (' + hist.length + ')');
		tr.insert(td);
		tab2.insert(tr);

		tr = new Element('tr');
		td = new Element('td', {colspan: '2'});
		htab = new Element('table', {'class': 'qfits-result-history'});
		td.insert(htab);
		tr.insert(td);
		tab2.insert(tr);
	
		hist.each(function(task) {
			tr = new Element('tr');
			// Emphasis of current history entry
			if (resp.TaskId == task.TaskId)
				tr.setAttribute('class', 'history-current');
	
			// Icon
			td = new Element('td');
			var src = task.Success ? 'success' : 'error';
			var img = new Element('img', {src: '/media/themes/' + guistyle + '/img/admin/icon_' + src + '.gif'});
			td.insert(img);
			tr.insert(td);
	
			// Date-time, duration
			td = new Element('td');
			var a = new Element('a', {href: '/youpi/results/' + this.id + '/' + task.TaskId + '/'});
			a.insert(task.Start + ' (' + task.Duration + ')');
			td.insert(a);
			tr.insert(td);
	
			// Hostname
			tr.insert(new Element('td').update(task.Hostname));
	
			// User
			tr.insert(new Element('td').update(task.User));
	
			// Reprocess option
			td = new Element('td', {'class': 'reprocess'});
			img = new Element('img', {
				onclick: this.id + ".reprocessStack('" + task.TaskId + "');",
				src: '/media/themes/' + guistyle + '/img/misc/reprocess.gif'
			});
			td.insert(img);
			tr.insert(td);
	
			htab.insert(tr);
		}.bind(this));

		// Run parameters
		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('colspan', '2');
		td.setAttribute('class', 'qfits-result-header-title');
		td.insert('Swarp run parameters');
		tr.insert(td);
		tab2.insert(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.insert('Input FITS files (' + resp.FITSImages.length + '):');
		tr.insert(td);
	
		td = new Element('td');
		var img_div = new Element('div', {'class': 'min_size'});
		td.insert(img_div);
		resp.FITSImages.each(function(image) {
			img_div.insert(image).insert(new Element('br'));
		});
		tr.insert(td);
		tab2.insert(tr);

		// Weight path
		tr = new Element('tr');
		td = new Element('td').insert('Weight path:');
		tr.insert(td);

		td = new Element('td').insert(resp.WeightPath.length > 0 ? resp.WeightPath : '--');
		tr.insert(td);
		tab2.insert(tr);

		// Head path
		tr = new Element('tr');
		td = new Element('td').insert('Head path:');
		tr.insert(td);

		td = new Element('td').insert(resp.HeadPath.length > 0 ? resp.HeadPath : '--');
		tr.insert(td);
		tab2.insert(tr);

		// Output directory
		tr = new Element('tr');
		td = new Element('td', {nowrap: 'nowrap'}).update('Results output dir:');
		tr.insert(td);
	
		td = new Element('td').update(resp.ResultsOutputDir);
		tr.insert(td);
		tab2.insert(tr);

		// Total exposure time
		tr = new Element('tr');
		td = new Element('td').insert('Exposure time (s):');
		tr.insert(td);

		td = new Element('td').insert(resp.TotalExposureTime);
		tr.insert(td);
		tab2.insert(tr);
	
		// Config file
		tr = new Element('tr');
		td = new Element('td', {colspan: 2});
		if (resp.Success) {
			td.setAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		}
		var cdiv = new Element('div', {
						id: 'config-' + resp.TaskId,
						'class': 'config_file'
		});
		var pre = new Element('pre').insert(resp.Config);
		cdiv.insert(pre);
		tr.insert(td);
		tab2.insert(tr);

		var confbox = new DropdownBox(td, 'Toggle Swarp config file view');
		$(confbox.getContentNode()).insert(cdiv);
	
		// Error log file when failure
		if (!resp['Success']) {
			tr = new Element('tr');
			td = new Element('td', {style: 'border-bottom: 2px #5b80b2 solid',
									colspan: '2'
			});
			var but = new Element('input', {type: 'button',
											value: 'Toggle error log file view',
											onclick: "toggleDisplay('log-" + resp['TaskId'] + "');"
			});
			td.insert(but);
			var cdiv = new Element('div', { id: 'log-' + resp['TaskId'],
											style: 'height: 200px; overflow: auto; background-color: black; padding-left: 5px; display: none'
			});
			var pre = new Element('pre').update(resp['Log']);
			cdiv.insert(pre);
			td.insert(cdiv);
			tr.insert(td);
			tab2.insert(tr);
		}
		else {
			// Stack image
			tr = new Element('tr');
			td = new Element('td', {colspan: '2'}).addClassName('qfits-result-header-title');
			td.insert('Stack Image');
			tr.insert(td);
			tab2.insert(tr);

			tr = new Element('tr');
			td = new Element('td');
			td.insert('Final stack name:');
			tr.insert(td);
			td = new Element('td');
			td.insert(resp.ResultsOutputDir + resp.StackName);
			tr.insert(td);
			tab2.insert(tr);
		}
	
		d.insert(tab);
		container.insert(d);
	},

	showSavedItems: function() {
		var cdiv = $('plugin_menuitem_sub_' + this.id).update();
		var div = new Element('div', {'class': 'savedItems', id: this.id + '_saved_items_div'});
		cdiv.insert(div);
	
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
					var table = new Element('table', {'class': 'savedItems'});
					var tr, th;
					tr = new Element('tr');
					var headers = $A(['Date', 'Permissions', 'Name', '# images', 'Config', 'Paths', 'Action']);
					headers.each(function(header) {
						tr.insert(new Element('th').update(header));
					});
					table.insert(tr);
	
					var delImg, trid;
					var tabi, tabitr, tabitd;
					resp.result.each(function(res, k) {
						idLists = res.idList.evalJSON();
						trid = this.id + '_saved_item_' + k + '_tr';
						tr = new Element('tr', {id: trid});
						delImg = new Element('img', {	id: this.id + '_del_saved_item_' + k,
														style: 'margin-right: 5px',
														src: '/media/themes/' + guistyle + '/img/misc/delete.png'
						});

						// Date
						td = new Element('td').update(res.date);
						tr.insert(td);
	
						// Permissions
                        var perms = res.perms.evalJSON(sanitize=true);
						td = new Element('td').addClassName('config').update(get_permissions_from_data(res.perms, 'cartitem', res.itemId));
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

						// Handling paths
						td = new Element('td');
						tabi = new Element('table', {'class': 'info'});
						// Weight
						tabitr = new Element('tr');
						tabitd = new Element('td', {'class': 'label'});
						tabitd.update('Weight: ');
						tabitr.insert(tabitd);
						tabitd = new Element('td', {'class': 'file'});
						if (res.weightPath.length)
							tabitd.update(reduceString(res.weightPath));
						else
							tabitd.update('Not specified');
						tabitr.insert(tabitd);
						tabi.insert(tabitr);
						td.insert(tabi);
						tr.insert(td);
						
						// Head
						tabitr = new Element('tr');
						tabitd = new Element('td', {'class': 'label'});
						tabitd.update('Head: ');
						tabitr.insert(tabitd);
						tabitd = new Element('td', {'class': 'file'});
						if (res.headPath.length)
							tabitd.update(reduceString(res.headPath));
						else
							tabitd.update('Not specified');
						tabitr.insert(tabitd);
						tabi.insert(tabitr);
						td.insert(tabi);
						tr.insert(td);
	
						// Delete
						td = new Element('td');
						delImg.c_data = {trid: trid, name: res.name};
						delImg.observe('click', function(c_data) {
							this.delSavedItem(c_data.trid, c_data.name);
						}.bind(this, delImg.c_data));
                        if (perms.currentUser.write)
                            td.insert(delImg);

						var addImg = new Element('img', {src: '/media/themes/' + guistyle + '/img/misc/addtocart_small.png'});
						addImg.observe('click', function(c_data) {
							this.addToCart(c_data);
						}.bind(this, $H(res)));
						td.insert(addImg);

						tr.insert(td);
						table.insert(tr);
					}.bind(this));
					div.insert(table);
				}.bind(this)
		);
	
		var post = 	'Plugin=' + this.id + '&Method=getSavedItems';
		r.send('/youpi/process/plugin/', post);
	},

	delSavedItem: function(trid, name) {
		var r = confirm("Are you sure you want to delete saved item '" + name + "'?");
		if (!r) return;
	
		var trNode = $(trid);
		var r = new HttpRequest(
				this.id + '_result',
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
									if (last) eval(this.id + '.showSavedItems()');
									// Notify user
									document.fire('notifier:notify', "Item '" + name + "' successfully deleted");
								}.bind(this)
							});
						}.bind(this)
					});
				}
		);
	
		var post = {
			'Plugin': this.id,
			'Method': 'deleteCartItem',
			'Name'	: name
		};

		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	},

	addToCart: function(data) {
		var p_data = {	plugin_name : this.id,
						userData :	data
		};
	
		s_cart.addProcessing(p_data,
				// Custom hanlder
				function() {
					window.location.reload();
				}
		);
	},

	getHeadPath: function() {
		var hSel = $(this.id + '_heads_select');
		var headPath;
		var path = hSel.options[hSel.selectedIndex].text;
		if (path != selector.getNoSelectionPattern()) {
			headPath = (path == selector.getExtra(1).title) ? 'AUTO' : path;
		}
		else {
			menu.activate(1);
			alert("Invalid data path selected for HEAD data.");
			hSel.up().up().pulsate();
			throw Exception.HEAD_NOT_FOUND
		}
		return headPath;
	},

	getWeightPath: function() {
		var wSel = $(this.id + '_weights_select');
		var weightPath;
		var path = wSel.options[wSel.selectedIndex].text;
		if (path != selector.getNoSelectionPattern()) {
			weightPath = (path == selector.getExtra(0).title) ? 'AUTO' : path;
		}
		else {
			menu.activate(1);
			alert("Invalid data path selected for WEIGHT data.");
			wSel.up().up().pulsate();
			throw Exception.WEIGHT_NOT_FOUND
		}
		return weightPath;
	},

	/*
	 * More initialization
	 */
	init: function() {
		var root = $('menuitem_sub_0');
		root.writeAttribute('align', 'center');
		// Container for the ImageSelector widget
		var div = new Element('div', {id: this.id + '_results_div', align: 'center'}).setStyle({width: '90%'});
		root.insert(div);
		// Container for the ImageSelector widget
		this.ims = new ImageSelector(this.id + '_results_div');
		this.ims.setTableWidget(new AdvancedTable());

		// Activates cart mode feature (automatic/manual)
		document.observe('PathSelectorWidget:pathsLoaded', function() {
			cartmode.init(this.id, 
				[$(this.id + '_results_div'), $('cartimg'), menu.getEntry(2), menu.getEntry(4)],
				{}, // No auto params during init, instead provide them later
				// Before handler
				function() {
					// extra params for autoProcessSelection() plugin call (in cartmode.js)
					cartmode.auto_params = {HeadPath: this.getHeadPath(), WeightPath: this.getWeightPath()}; 
				}.bind(this),
				function(res) {
					if (res.qfitsdata) {
						if (res.qfitsdata.missingQFITS.length > 0) {
							res.qfitsdata.missingQFITS.each(function(w) {
								$(this.id + '_automatic_log').insert('<i>MISSING QFits</i> for image ' + w + '<br/>');
							}.bind(this));
							cartmode.autoWarningCount += res.qfitsdata.missingQFITS.length;
						}
					}
				}.bind(this)
			);
		}.bind(this));
	}
};
