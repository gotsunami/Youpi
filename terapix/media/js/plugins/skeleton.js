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

/* vim: set ts=4 */

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
 * addSelectionToCart()						: adds current selection to cart
 * addToCart(data)							: adds a previously saved selection to cart
 * delSavedItem(trid, name)					: deletes a previously saved item
 * renderOutputDirStats(container_id)		: renders some statistics (from the results page)
 * reprocessAllFailedProcessings(tasksList)	: one click for reprocessing failed processings from the results page
 * resultsShowEntryDetails(container_id)	: displays custom results information on the results page
 * run(trid, opts, silent)					: submits a job to the cluster
 * saveItemForLater(trid, opts, silent)		: save item for later processing then remove item from the processing cart
 * showSavedItems()							: displays saved cart items
 *
 */

var skel = {
	id: 'skel',
	/*
	 * Function: addSelectionToCart
	 * Add the current selection to cart.
	 * Since this is a demo plugin, no real selection has been made. It's just adding the output data 
	 * directory to the userData variable
	 *
	 */
	addSelectionToCart: function() {
		// Do your sanity checks here
		var msg = 'One Skeleton-related job has been added to the cart. This is a DEMO plugin: it does nothing useful.';
	
		// Custom output directory
		var output_data_path = skel_output_data;
	
		// Set mandatory structures
		var p_data = {	
			plugin_name : this.id,
			userData : {resultsOutputDir: output_data_path}
		};
	
		// Add entry into the processing cart
		s_cart.addProcessing(	
			p_data,
			// Custom handler
			function() {
				document.fire('notifier:notify', msg);
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
		opts.set('Plugin', this.id);
		opts.set('Method', 'process');
		opts.set('ReprocessValid', (runopts.reprocessValid ? 1 : 0));
		opts = opts.merge(runopts.clusterPolicy.toQueryParams());

		r.send('/youpi/process/plugin/', opts.toQueryString());
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
		opts.set('Plugin', this.id);
		opts.set('Method', 'saveCartItem');

		var runopts = get_runtime_options(trid);
		var r = new HttpRequest(
				this.id + '_result',
				null,	
				// Custom handler for results
				function(resp) {
					document.fire('notifier:notify', 'Skeleton item saved successfully');
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
		var img = new Element('img', {src: '/media/themes/' + guistyle + '/img/admin/icon_' + src + '.gif'}).setStyle({paddingRight: '5px'});
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
		
		// Permissions
		tr = new Element('tr');
		td = new Element('td').setStyle({padding: '0px'});
		td.update(ResultsHelpers.getPermissionsEntry(resp.TaskId));
		tr.insert(td);
		tab2.insert(tr);

		// Condor Job Logs
		tr = new Element('tr');
		td = new Element('td').setStyle({padding: '0px'});
		td.update(ResultsHelpers.getCondorJobLogsEntry(resp.ClusterId, resp.TaskId));
		tr.insert(td);
		tab2.insert(tr);
	
		d.insert(tab);
		container.insert(d);
	},

	/*
	 * Function: showSavedItems
	 * Displays saved cart items
	 *
	 */ 
	showSavedItems: function() {
		var cdiv = $('plugin_menuitem_sub_' + this.id).update();
		var div = new Element('div', {id: this.id + '_saved_items_div'}).addClassName('savedItems');
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
					var header = $A(['Date', 'Permissions', 'Name', 'Description', 'Action']);
					header.each(function(elem) {
						tr.insert(new Element('th').update(elem));
					});
					table.insert(tr);
	
					var delImg, trid;
					var tabi, tabitr, tabitd;
					resp.result.each(function(res, k) {
						trid = this.id + '_saved_item_' + k + '_tr';
						tr = new Element('tr', {id: trid});
						// Delete
						delImg = new Element('img', {	id: this.id + '_del_saved_item_' + k,	
														src: '/media/themes/' + guistyle + '/img/misc/delete.png'
						}).setStyle({marginRight: '5px'});
						delImg.c_data = {trid: trid, name: res.name};
						delImg.observe('click', function(c_data) {
							this.delSavedItem(c_data.trid, c_data.name);
						}.bind(this, delImg.c_data));
	
						// Date
						td = new Element('td').update(res.date);
						tr.insert(td);
	
						// Permissions
                        var perms = res.perms.evalJSON(sanitize=true);
						td = new Element('td').addClassName('config').update(get_permissions_from_data(res.perms, 'cartitem', res.itemId));
						tr.insert(td);
	
						// Name
						td = new Element('td').addClassName('name').update(res.name);
						tr.insert(td);
	
						// Description
						td = new Element('td').update(res.descr);
						tr.insert(td);
						
						// Insert delete button
						td = new Element('td');
                        if (perms.currentUser.write)
                            td.insert(delImg);

						// Add to cart button
						addImg = new Element('img', {src: '/media/themes/' + guistyle + '/img/misc/addtocart_small.png'});
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
	
		var post = {
			Plugin: this.id,
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
				}.bind(this)
		);
	
		var post = {
			'Plugin': this.id,
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
		var p_data = {	plugin_name : this.id,
						userData : data
		};
	
		s_cart.addProcessing(p_data,
				// Custom hanlder
				function() {
					window.location.reload();
				}
		);
	}
};
