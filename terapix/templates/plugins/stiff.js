/*****************************************************************************
 *
 * Copyright (c) 2008-2010 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/

/* vim: set ts=4 */

/*
 * Group: Stiff Plugin
 *
 * JS code for Stiff plugin.
 *
 */

/* global */
var uidstiff = '{{ plugin.id }}';

var {{ plugin.id }} = {
	/*
	 * Variable: ims
	 * 
	 * <ImageSelector> instance
	 *
	 */
	ims: null,
	/*
	 * Function: addSelectionToCart
	 * Add the current selection to cart.
	 * Since this is a demo plugin, no real selection has been made. It's just adding the output data 
	 * directory to the userData variable
	 *
	 */
	addSelectionToCart: function() {
		sels = this.ims.getListsOfSelections();
		
		// Do your sanity checks here
		var msg = 'One Stiff-related job has been added to the cart. This is a DEMO plugin: it does nothing useful.';
	
		// Gets custom output directory
		var custom_dir = $('output_path_input').value.strip().gsub(/\ /, '');
		var output_data_path = '{{ processing_output }}{{ user.username }}/' + uidstiff + '/';
		if (custom_dir) output_data_path += custom_dir + '/';
	
		// Get config file
		var cSel = $(uidstiff + '_config_name_select');
		var config = cSel.options[cSel.selectedIndex].text;
	
		// Set mandatory structures
		var p_data = {	
			plugin_name : uidstiff,
			userData : {
				resultsOutputDir: output_data_path,
				config: config, 
				idList: sels
			}
		};
	
		// Add entry into the processing cart
		var total = this.ims.getImagesCount();
		s_cart.addProcessing(	
			p_data,
			// Custom handler
			function() {
				document.fire('notifier:notify', 'The current image selection (' + total + ' ' + 
					(total > 1 ? 'images' : 'image') + ') has been\nadded to the cart.');
			}
		);
	},

	/*
	 * Function: run
	 * Submits a job to the cluster
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
	
		var r = new HttpRequest(
				logdiv,
				null,	
				// Custom handler for results
				function(resp) {
					r = resp.result;
					var success = update_condor_submission_log(resp, silent);
					if (!success) return;
	
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
				}
		);
	
		opts = $H(opts);
		opts.set('Plugin', uidstiff);
		opts.set('Method', 'process');
		opts.set('ReprocessValid', (runopts.reprocessValid ? 1 : 0));
		opts = opts.merge(runopts.clusterPolicy.toQueryParams());

		r.send('{% url terapix.youpi.views.processing_plugin %}', opts.toQueryString());
	},

	/*
	 * Function:  reprocessAllFailedProcessings
	 * One click for reprocessing failed processings from the results page
	 *
	 * Parameters:
	 *  taskList - array: list of task Ids
	 *
	 */ 
	reprocessAllFailedProcessings: function(tasksList) {
		alert('TODO...');
	},

	/*
	 * Function: renderOutputDirStats
	 * Renders some statistics (from the results page)
	 * Those stats are bound to the results output directory.
	 *
	 * Parameters:
	 *  container_id - string: DOM container id
	 *
	 */ 
	renderOutputDirStats: function(container_id) {
		var container = $(container_id).update();
	
		// global var defined in results.html
		var resp = output_dir_stats_data;
		var stats = resp.Stats;
	
		var tab = new Element('table').addClassName('output_dir_stats');
		var tr,th,td;
		var tr = new Element('tr');
		// Headers
		var headers = $H({	
			task_success: 'Task success',
			task_failure: 'Task failures',
			task_total: 'Total processings'
		});
		headers.each(function(header) {
			th = new Element('th', {'colspan': '2'}).addClassName(header.key).update(header.value);
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
			var td = new Element('td').addClassName(cls).update(val);
			tr.insert(td);

			td = new Element('td').addClassName(cls).update(percent);
			tr.insert(td);
		});
		tab.insert(tr);
		container.insert(tab);
	},

	/*
	 * Function: saveItemForLater
	 * Save item for later processing then remove item from the processing cart
	 *
	 * Parameters:
	 *  trid - string: for row number
	 *  opts - hash: options
	 *  silent - boolean: silently submit item to the cluster
	 *
	 */ 
	saveItemForLater: function(trid, opts, silent) {
		opts = $H(opts);
		opts.set('Plugin', uidstiff);
		opts.set('Method', 'saveCartItem');

		var runopts = get_runtime_options(trid);
		var r = new HttpRequest(
				uidstiff + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					document.fire('notifier:notify', 'Stiff item saved successfully');
					// Silently remove item from the cart
					removeItemFromCart(trid, true);
				}
		);
	
		r.send('/youpi/process/plugin/', opts.toQueryString());
	},

	/*
	 * Function: resultsShowEntryDetails
	 * Displays custom results information on the results page. 
	 * 'resp' contains server-side info to display
	 *
	 * Parameters:
	 *  container_id - string: id of DOM container
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

		var d = new Element('div').addClassName('entryResult');
		var tab = new Element('table').addClassName('fileBrowser').setStyle({width: '100%'});
	
		tr = new Element('tr');
		th = new Element('th').update(resp['Title']);
		tr.insert(th);
		tab.insert(tr);
	
		// Duration
		var tdiv = new Element('div').addClassName('duration');
		tdiv.insert(resp.Start + '<br/>');
		tdiv.insert(resp.End + '<br/>');
		var src = resp.Success ? 'success' : 'error';
		var img = new Element('img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif'}).setStyle({paddingRight: '5px'});
		tdiv.insert(img);
		tdiv.insert(resp.Duration);
		tr = new Element('tr');
		td = new Element('td').setStyle({borderBottom: '2px #5b80b2 solid'});
		td.insert(tdiv);
		tr.insert(td);
		tab.insert(tr);
	
		// User
		var udiv = new Element('div').addClassName('user');
		udiv.insert('Job initiated by ' + resp.User);
		udiv.insert(new Element('br'));
		udiv.insert('Exit status: ');
		udiv.insert(new Element('br'));
		var txt = resp.Success ? 'success' : 'failure';
		var exit_s = new Element('span').addClassName('exit_' + txt).update(txt);
		udiv.insert(exit_s);
		td.insert(udiv);
	
		tr = new Element('tr');
		td = new Element('td', {style: 'padding: 0px'});
		var tab2 = new Element('table').addClassName('qfits-result-entry-params');
		td.insert(tab2);
		tr.insert(td);
		tab.insert(tr);
	
		// Error log file when failure
		if (!resp.Success) {
			tr = new Element('tr');
			td = new Element('td', {colspan: 2}).setStyle({borderBottom: '2px #5b80b2 solid'});
			var but = new Element('input', {type: 'button',
											value: 'Toggle error log file view',
											onclick: "toggleDisplay('log-" + resp.TaskId + "');"
			});
			td.insert(but);
			var cdiv = new Element('div', {id: 'log-' + resp.TaskId}).setStyle({
				height: '200px', 
				overflow: 'auto', 
				backgroundColor: 'black', 
				paddingLeft: '5px'
			}).hide();
			var pre = new Element('pre').update(resp.Log);
			cdiv.insert(pre);
			td.insert(cdiv);
			tr.insert(td);
			tab2.insert(tr);
		}
		
		// View Image
		tr = new Element('tr');
		td = new Element('td', {colspan: 2}).addClassName('qfits-result-header-title');
		td.insert('View Image In Browser');
		tr.insert(td);
		tab2.insert(tr);

		tr = new Element('tr');
		td = new Element('td').setStyle({padding: '8px'});
		td.update(new Element('img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/stiff-pyramid.png'}));
		tr.insert(td);
		td = new Element('td').setStyle({padding: '8px'});
		td.update(new Element('a', {href: '/youpi/image/view/' + resp.TaskId + '/'}).update('Click to see image'));
		tr.insert(td);
		tab2.insert(tr);
		
		// Permissions
		tr = new Element('tr');
		td = new Element('td', {colspan: 2}).setStyle({padding: '0px'});
		td.update(ResultsHelpers.getPermissionsEntry(resp.TaskId));
		tr.insert(td);
		tab2.insert(tr);

		// Image tags
		if (resp.Tags.length) {
			tr = new Element('tr');
			td = new Element('td', {colspan: 2}).addClassName('qfits-result-header-title');
			td.insert('Image Tags');
			tr.insert(td);
			tab2.insert(tr);

			tr = new Element('tr');
			td = new Element('td', {colspan: 2}).setStyle({padding: '8px'});
			$A(resp.Tags).each(function(tag) {
				td.insert(new Element('div', {style: 'float: left; ' + tag[1]}).addClassName('tagwidget').update(tag[0]));;
			});
			tr.insert(td);
			tab2.insert(tr);
		}

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
		td = new Element('td', {colspan: 2, 'class': 'qfits-result-header-title'});
		td.insert('Stiff processing history (' + hist.length + ')');
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
			var img = new Element('img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif'});
			td.insert(img);
			tr.insert(td);
	
			// Date-time, duration
			td = new Element('td');
			var a = new Element('a', {href: '/youpi/results/' + uidstiff + '/' + task.TaskId + '/'});
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
				onclick: uidstiff + ".reprocessImage('" + task.TaskId + "');",
				src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/reprocess.gif'
			});
			td.insert(img);
			tr.insert(td);
	
			htab.insert(tr);
		});
			
		// Stiff run parameters
		tr = new Element('tr'); 
		td = new Element('td', {colspan: '2'}).addClassName('qfits-result-header-title');
		td.update('Stiff run parameters');
		tr.insert(td);
		tab2.insert(tr);

		// Image
		tr = new Element('tr');
		td = new Element('td').update('Image:');
		tr.insert(td);
		td = new Element('td').update(resp.ImgPath + resp.ImgName + '.fits');
		tr.insert(td);
		tab2.insert(tr);
		
		// Output directory
		tr = new Element('tr');
		td = new Element('td', {nowrap: 'nowrap'}).update('Results output dir:');
		tr.insert(td);
		td = new Element('td').update(resp.ResultsOutputDir);
		tr.insert(td);
		tab2.insert(tr);
		
		// Config file
		tr = new Element('tr');
		td = new Element('td', {colspan: 2});
		if (resp.Success) td.writeAttribute('style', 'border-bottom: 2px #5b80b2 solid');
		var cdiv = new Element('div', {
			id: 'config-' + resp.TaskId,
			'class': 'config_file'
		});
		var pre = new Element('pre').insert(resp.Config);
		cdiv.insert(pre);
		tr.insert(td);
		tab2.insert(tr);

		var confbox = new DropdownBox(td, 'Toggle Stiff config file view');
		$(confbox.getContentNode()).insert(cdiv);
	
		d.insert(tab);
		container.insert(d);
	},

	/*
	 * Function: showSavedItems
	 * Displays saved cart items
	 *
	 */ 
	showSavedItems: function() {
		var cdiv = $('plugin_menuitem_sub_' + uidstiff).update();
		var div = new Element('div', {id: uidstiff + '_saved_items_div'}).addClassName('savedItems');
		cdiv.insert(div);
	
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
					var table = new Element('table').addClassName('savedItems');
					var tr, th;

					tr = new Element('tr');
					//var header = $A(['Date', 'Permissions', 'Name', 'Description', 'Action']);
					var headers = $A(['Date', 'Permissions', 'Name', '# images', 'Config', 'Action']);
					headers.each(function(elem) {
						tr.insert(new Element('th').update(elem));
					});
					table.insert(tr);
	
					var delImg, trid;
					var tabi, tabitr, tabitd;
					resp.result.each(function(res, k) {
						idLists = res.idList.evalJSON();
						trid = uidstiff + '_saved_item_' + k + '_tr';
						tr = new Element('tr', {id: trid});
						// Delete
						delImg = new Element('img', {	id: uidstiff + '_del_saved_item_' + k,	
														src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/delete.png'
						}).setStyle({marginRight: '5px'}).hide();
						delImg.c_data = {trid: trid, name: res.name};
						delImg.observe('click', function() {
							{{ plugin.id }}.delSavedItem(this.c_data.trid, this.c_data.name);
						});
	
						// Date
						td = new Element('td').update(res.date);
						tr.insert(td);
	
						// Permissions
						td = new Element('td').addClassName('config').update(get_permissions('cartitem', res.itemId, function(r, imgId) {
							// imgId is the misc parameter passed to get_permissions()
							var img = $(imgId);
							r.currentUser.write ? img.show() : img.hide();
						}, delImg.readAttribute('id') /* Misc data */));
						tr.insert(td);
	
						// Name
						td = new Element('td').addClassName('name').update(res.name);
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
						
						// Insert delete button
						td = new Element('td');
						td.insert(delImg);

						// Add to cart button
						addImg = new Element('img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.png'});
						addImg.c_data = $H(res);
						addImg.observe('click', function() {
							{{ plugin.id }}.addToCart(this.c_data);
						});
						td.insert(addImg);

						tr.insert(td);
						table.insert(tr);
					});
					div.insert(table);
				}
		);
	
		var post = {
			Plugin: uidstiff,
			Method: 'getSavedItems'
		};
		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	},

	/*
	 * Function: delSavedItem
	 * Delete a saved cart item
	 *
	 * Parameters:
	 *  trid - string: row id
	 *  name - string: item's name
	 *
	 */ 
	delSavedItem: function(trid, name) {
		var r = confirm("Are you sure you want to delete saved item '" + name + "'?");
		if (!r) return;

		var trNode = $(trid);
		var r = new HttpRequest(
				uidstiff + '_result',
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
									if (last) eval(uidstiff + '.showSavedItems()');

									// Notify user
									document.fire('notifier:notify', "Item '" + name + "' successfully deleted");
								}
							});
						}
					});
				}
		);
	
		var post = {
			'Plugin': uidstiff,
			'Method': 'deleteCartItem',
			'Name'	: name
		};

		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	},

	/*
	 * Function: addToCart
	 * Add a skel item to cart
	 *
	 * Parameters:
	 *  data - hash: any user data
	 *
	 */ 
	addToCart: function(data) {
		var p_data = {	plugin_name : uidstiff,
						userData : data
		};
	
		s_cart.addProcessing(p_data,
				// Custom hanlder
				function() {
					window.location.reload();
				}
		);
	},

	/*
	 * Function: selectImages
	 * Add an image selector widget
	 *
	 */ 
	selectImages: function() {
		var root = $('menuitem_sub_0');
		root.writeAttribute('align', 'center');
		// Container of the ImageSelector widget
		var div = new Element('div', {id: uidstiff + '_results_div', align: 'center'}).setStyle({width: '90%'});
		root.insert(div);

		/*
		this.ims = new ImageSelector(uidstiff + '_results_div');
		this.ims.setTableWidget(new AdvancedTable());
		*/
		{{ plugin.id }}.ims = new ImageSelector(uidstiff + '_results_div');
		{{ plugin.id }}.ims.setTableWidget(new AdvancedTable());
		
	},

	/*
	 * Function: reprocessImage
	 * Schedule a Stiff job for reprocessing
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
					p_data = {	
						plugin_name : uidstiff,
						userData : { 	
							'config' : 'The one used for the last processing',
							'taskId' : taskId,
							'idList' : data.idList,
							'resultsOutputDir' : data.resultsOutputDir
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

		var post = {
			Plugin: uidstiff,
			Method: 'getReprocessingParams',
			TaskId: taskId
		};
		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	},
};
