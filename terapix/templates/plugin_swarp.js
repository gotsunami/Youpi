/*
 * Group: Swarp Plugin
 *
 * JS code for Swarp plugin.
 *
 */
var {{ plugin.id }} = {
	/*
	 * Function: addSelectionToCart
	 *
	 */
	addSelectionToCart: function() {
		// Do your sanity checks here
		// FIXME: checks...
	
		// Custom output directory
		var output_data_path = '{{ processing_output }}{{ user.username }}/{{ plugin.id }}/';
	
		// Set mandatory structures
		var p_data = {	plugin_name : '{{ plugin.id }}', 
					userData : {resultsOutputDir: output_data_path}
		};
		alert('TODO...');
		return;
	
		// Add entry into the shopping cart
		s_cart.addProcessing(	p_data,
								// Custom handler
								function() {
									alert('TODO...');
								}
		);
	},

	/*
	 * Function: run
	 * Run processing
	 *
	 * Parameters:
	 *	name - string: name part of ID 
	 *  row - integer: for row number
	 *
	 */ 
	run: function(trid, itemId, resultsOutputDir, silent) {
		var silent = silent == true ? true : false;
		var runopts = get_runtime_options(trid);
		var logdiv = $('master_condor_log_div');
	
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
	},

	reprocessAllFailedProcessings: function(tasksList) {
		alert('TODO...');
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

	saveItemForLater: function(trid, itemId, resultsOutputDir) {
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
		var img = new Element(	'img', {src: '/media/themes/{{ user.get_profile.guistyle }}/img/admin/icon_' + src + '.gif',
										style: 'padding-right: 5px;'
		});
		tdiv.insert(img);
		tdiv.insert(resp['Duration']);
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
	
		d.insert(tab);
		container.insert(d);
	},

	showSavedItems: function() {
		var cdiv = $('plugin_menuitem_sub_{{ plugin.id }}').update();
		var div = new Element('div', {'class': 'savedItems', id: '{{ plugin.id }}_saved_items_div'});
		cdiv.insert(div);
	
		var r = new HttpRequest(
				div.id,
				null,	
				// Custom handler for results
				function(resp) {
					div.update();
	
					var total = resp['result'].length;
					var countNode = $('plugin_{{ plugin.id }}_saved_count').update();
					var txt;
					if (total > 0)
						txt = total + ' item' + (total > 1 ? 's' : '');
					else
						txt = 'No item';
					countNode.update(txt);
	
					var table = new Element('table', {'class': 'savedItems'});
					var tr, th;
					var icon = new Element('img', {	'src': '/media/themes/{{ user.get_profile.guistyle }}/img/32x32/{{ plugin.id }}' + '.png',
													'style': 'vertical-align:middle; margin-right: 10px;'
					});
	
					tr = new Element('tr');
					th = new Element('th', {'colspan': '8'});
					th.insert(icon);
					th.insert('{{ plugin.description }}: ' + resp['result'].length + ' saved item' + (resp['result'].length > 1 ? 's' : ''));
					tr.insert(th);
					table.insert(tr);
	
					tr = new Element('tr');
					var header = $A(['Date', 'User', 'Name', 'Description', 'Action']);
					header.each(function(elem) {
						tr.insert(new Element('th').update(elem));
					});
					table.insert(tr);
	
					var delImg, trid;
					var tabi, tabitr, tabitd;
					for (var k=0; k < resp['result'].length; k++) {
						trid = '{{ plugin.id }}_saved_item_' + k + '_tr';
						tr = new Element('tr', {id: trid});
	
						// Date
						td = new Element('td').update(resp['result'][k]['date']);
						tr.insert(td);
	
						// User
						td = new Element('td', {'class': 'config'}).update(resp['result'][k]['username']);
						tr.insert(td);
	
						// Name
						td = new Element('td', {'class': 'name'}).update(resp['result'][k]['name']);
						tr.insert(td);
	
						// Description
						td = new Element('td').update(resp['result'][k]['descr']);
						tr.insert(td);
						
						// Delete
						td = new Element('td');
						delImg = new Element('img', {	style: 'margin-right: 5px',
														src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/delete.gif',
														onclick: "{{ plugin.id }}.delSavedItem('" + trid + "', '" + 
															resp['result'][k]['name'] + "')"
						});
						td.insert(delImg);

						delImg = new Element('img', {	src: '/media/themes/{{ user.get_profile.guistyle }}/img/misc/addtocart_small.gif',
														onclick: "{{ plugin.id }}.addToCart('" + resp['result'][k]['resultsOutputDir'] + "')"
						});
						td.insert(delImg);

						tr.insert(td);
						table.insert(tr);
					}
	
					if (resp['result'].length) {
						div.insert(table);
					}
					else {
    	                div.insert(icon);
        	            div.insert('  : no saved item');
					}
				}
		);
	
		var post = 	'Plugin={{ plugin.id }}&Method=getSavedItems';
		r.send('/youpi/process/plugin/', post);
	},

	delSavedItem: function(trid, name) {
		var r = confirm("Are you sure you want to delete saved item '" + name + "'?");
		if (!r) return;
	
		var trNode = $(trid);
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
						trNode.remove();
				}
		);
	
		var post = 	'Plugin={{ plugin.id }}&Method=deleteCartItem&Name=' + name;
		r.send('/youpi/process/plugin/', post);
	},

	addToCart: function(resultsOutputDir) {
		var p_data = {	plugin_name : '{{ plugin.id }}', 
						userData : {'resultsOutputDir' : resultsOutputDir}
		};
	
		s_cart.addProcessing(p_data,
				// Custom hanlder
				function() {
					window.location.reload();
				}
		);
	},

	selectImages: function() {
		var root = document.getElementById('menuitem_sub_0');
		root.setAttribute('align', 'center');
		// Container of the ImageSelector widget
		var div = document.createElement('div');
		div.setAttribute('id', '{{ plugin.id }}_results_div');
		div.setAttribute('align', 'center');
		root.appendChild(div);

		{{ plugin.id }}_ims = new ImageSelector('{{ plugin.id }}_results_div');
		{{ plugin.id }}_advTab = new AdvancedTable('{{ plugin.id }}_advTab');
		{{ plugin.id }}_ims.setTableWidget({{ plugin.id }}_advTab);
	}
};
