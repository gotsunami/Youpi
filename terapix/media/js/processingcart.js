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

/*
 * Class: ProcessingCart
 * Basic processing cart implementation
 *
 * External Dependencies:
 *  prototype.js - Enhanced Javascript library
 *  scriptaculous.js - Visual effects library
 *
 * Constructor Parameters:
 *  container - string or DOM: name of parent DOM block container
 *
 * Signals:
 *  processingCart:itemAlreadyExisting - signal emitted when the same item definition is already available in the processing cart
 *
 */
function ProcessingCart(container)
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container = $(container);
	/*
	 * Var: _itemsCount
	 * Number of items in cart
	 *
	 */ 
	var itemsCount = 0;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _getArticlesCountMsg
	 * Cart text rendering
	 *
	 */ 
	function _getArticlesCountMsg() {
		return itemsCount ? itemsCount + ' item' + 
			(itemsCount > 1 ? 's' : '') : 'Empty cart';
	}

	/*
	 * Function: _render
	 * Renders processing cart
	 *
	 */ 
	function _render() {
		var div = new Element('div', {id: 'shoppingCart'}).addClassName('nonempty')
			.update(new Element('img', {src: '/media/themes/' + guistyle + '/img/misc/minicart.png'}))
			.insert(_getArticlesCountMsg());
		div.observe('click', function(event) { location.href = '/youpi/cart/'; });
		_container.update();
		_container.insert(div);
	}

	/*
	 * Function: refresh
	 * Updates cart rendering
	 *
	 */ 
	this.refresh = function() {
		_render();
	}

	/*
	 * Function: addProcessing
	 * Adds an item to the processing cart
	 *
	 * Parameters:
	 *  obj - object: object with custom user data
	 *  handler - function: custom function to execute after an item has been added
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 *  plugin_name - string: internal plugin name
	 *  userData - object: custom user data 
	 *
	 */ 
	this.addProcessing = function(obj, handler) {
		var handler = typeof handler == 'function' ? handler : null;
		if (!obj.plugin_name || !obj.userData)
			throw "Missing object attributes plugin_name or userData";

		var r = new HttpRequest(
			null,
			null,
			function(resp) {
				if (resp.warning) {
					document.fire('processingCart:itemAlreadyExisting', resp.warning);
					return;
				}
				var nb = resp.data.length;
				itemsCount = resp.count;
				_render();
				// Call custom handler
				if (handler) handler();
			}
		);

		var post = {
			plugin: obj.plugin_name,
			userData: Object.toJSON(obj.userData)
		};					
		// Check for cookie
		r.send('/youpi/cart/additem/', $H(post).toQueryString());
	}

	/*
	 * Function: deletePluginItem
	 * Deletes an item from the processing cart
	 *
	 * Parameters:
	 *  obj - object: arbitrary object
	 *  handler - function: custom function to execute after an item has been deleted
	 *  deleteAll - boolean: true to delete all plugin's items at once
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 * plugin_name - string: internal plugin name
	 * idx - int: row index (in plugin context)
	 *
	 */ 
	this.deletePluginItem = function(obj, handler, deleteAll) {
		var handler = typeof handler == 'function' ? handler : null;
		var deleteAll = typeof deleteAll == 'boolean' ? deleteAll : false;

		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp.data.length;
				itemsCount = resp.count;
				_render();
				if (handler) handler();
			}
		);

		var post = 'plugin=' + obj.plugin_name;
		if (!deleteAll)
			post += '&idx=' + obj.idx;
		xhr.send('/youpi/cart/delitem/', post);
	}

	/*
	 * Function: deleteAllPluginItem
	 * Deletes an item from the processing cart
	 *
	 * Parameters:
	 *  obj - object: arbitrary object
	 *  handler - function: custom function to execute after an item has been deleted
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 *  plugin_name - string: internal plugin name
	 *  idx - int: row index (in plugin context)
	 *
	 */ 
	this.deleteAllPluginItems = function(plugin_name, handler) {
		this.deletePluginItem(plugin_name, handler, true);
	}

	/*
	 * Parameters:
	 *  data - object: of the form {plugin_name1: [0..n], plugin_name2: [0..n], ..., plugin_nameN: [0..n]}
	 *  handler - function: custom function to execute after all items have been deleted
	 *
	 */
	this.deleteItems = function(data, handler) {
		var handler = typeof handler == 'function' ? handler : null;
		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp.deleted;
				itemsCount = resp.count;
				_render();
				if (handler) handler(nb);
			}
		);
		xhr.send('/youpi/cart/delitems/', $H(data).toQueryString());
	}

	function _init() {
		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				itemsCount = resp.count;
				_render();
			}
		);

		// Count items
		xhr.send('/youpi/cart/itemsCount/');
	}
	
	// Main entry point
	_init();
}

/*
 * Misc functions used by the processing cart
 *
 */

/*
 * Function: real_delete_items
 * Deletes a selection of items from the processing cart
 *
 * Parameters:
 *  count - integer: number of items to delete
 *  data - object: items grouped by plugin name
 *  removeEntries - boolean: whether to delete node entries after items are deleted
 *                           from the current user session [default: true]
 *
 */ 
function real_delete_items(count, data, removeEntries) {
	var removeEntries = typeof removeEntries == 'boolean' ? removeEntries : true;
	s_cart.deleteItems(data.toObject(), function(deleted) {
		data.each(function(p) {
			var trs = $$("tr[id^='" + p.key + "']");
			var table = trs[0].up('table.shoppingCart');
			p.value.each(function(idx) {
				var trNode = trs[idx];
				if (removeEntries) trNode.remove();
			});
			// Recomputes trs after row deletion to check if empty parent
			// table has to be deleted too
			if (removeEntries) {
				trs = $$("tr[id^='" + p.key + "']");
				if (trs.length == 0)
					table.remove();
			}
		});
		// Send signal once done
		if (removeEntries)
			document.fire('processingCart:itemRemoved', deleted);
	});
}

/*
 * Function: do_delete_items
 * Asks for confirmation before calling <real_delete_items>()
 *
 * Parameters:
 *  count - integer: number of items to delete
 *  data - object: items grouped by plugin name
 *
 */ 
function do_delete_items(count, data) {
	boxes.confirm('Are you sure you want to delete this item selection (' + count + ' item' + (count > 1 ? 's':'') + ') from the processing cart?', 
		function() {
			real_delete_items(count, data);
		}
	);
}

// Global meta data namespace for active items
var youpi_pc_meta = {};

/*
 * Function: real_save_items
 * Saves a selection of items from the processing cart to permanent DB storage
 *
 * Parameters:
 *  data - object: items grouped by plugin name
 *
 */ 
function real_save_items(data) {
	var opts = new Hash();
	var key = data.keys()[youpi_pc_meta.action_cur_key_idx];
	var trid = key + '_' + data.get(key)[youpi_pc_meta.action_cur_value_idx];
	var trNode = $(trid);
	// Sets metadata
	opts.set('Plugin', key);
	opts.set('Method', 'saveCartItem');
	opts.update(youpi_pc_meta[trid].userData);
	var r = new HttpRequest(
		null,
		null,	
		// Custom handler for results
		function(resp) {
			$('master_condor_log_div').update();
			if (youpi_pc_meta.action_cur_value_idx < data.get(key).length-1)
				youpi_pc_meta.action_cur_value_idx++;
			else {
				youpi_pc_meta.action_cur_value_idx = 0;
				if (youpi_pc_meta.action_cur_key_idx < data.keys().length)
					youpi_pc_meta.action_cur_key_idx++;

			}
			if (youpi_pc_meta.action_cur_key_idx < data.keys().length) {
				youpi_pc_meta.action_pb_value++;
				youpi_pc_meta.progressBar.setPourcentage((youpi_pc_meta.action_pb_value/youpi_pc_meta.action_pb_total)*100);
				real_save_items(data);
			}
			else {
				// All items are saved
				youpi_pc_meta.progressBar.setPourcentage(100);
				$('cart_pbar_div').fade({delay: 5.0});
				document.fire('notifier:notify', 'Items saved successfully');
				// Remove saved items from the pc
				real_delete_items(youpi_pc_meta.action_pb_total, data);
			}
		}
	);
	r.send('/youpi/process/plugin/', capitalizeHashKeys(opts).toQueryString());
}

/*
 * Function: do_save_items
 * Asks for confirmation first then call <real_save_items>()
 *
 * Parameters:
 *  count - integer: number of items to save
 *  data - object: items grouped by plugin name
 *
 */ 
function do_save_items(count, data) {
	boxes.confirm('Are you sure you want to save this item selection (' + count + ' item' + (count > 1 ? 's':'') + ') for later use?', 
		function() { 
			// Some init before calling the real stuff
			// Current key pos for saving in data.keys()
			youpi_pc_meta.action_cur_key_idx = 0;
			// Current position of item for that key
			youpi_pc_meta.action_cur_value_idx = 0;
			// For the progress bar
			youpi_pc_meta.action_pb_value = 0;
			youpi_pc_meta.action_pb_total = count;
			$('cart_pbar_div').appear();
			// Real stuff
			real_save_items(data); 
		}
	);
}

/*
 * Function: real_run_items
 * Send a selection of items to the cluster
 *
 * Parameters:
 *  data - object: items grouped by plugin name
 *
 */ 
function real_run_items(data) {
	var opts = new Hash();
	var key = data.keys()[youpi_pc_meta.action_cur_key_idx];
	var trid = key + '_' + data.get(key)[youpi_pc_meta.action_cur_value_idx];
	var trNode = $(trid);
	var runopts = get_runtime_options();

	// Sets metadata
	opts.set('Plugin', key);
	opts.set('Method', 'process');
	opts.set('ReprocessValid', (runopts.reprocessValid ? 1 : 0));
	opts.update(youpi_pc_meta[trid].userData);
	opts = opts.merge(runopts.clusterPolicy.toQueryParams());

	var r = new HttpRequest(
		null,
		null,	
		// Custom handler for results
		function(resp) {
			$('master_condor_log_div').update();
			var res = resp.result;
			if (res.CondorError || res.Error) {
				// Submission failure
				trNode.addClassName('job_sent_failure');
				trNode.select('.pc_item_name')[0].up().up()
					.insert(new Element('span', {title: res.CondorError + '\n' + res.Error}).update('Job Error').addClassName('job_error'));
			}
			else {
				if (res.NoData) {
					trNode.removeClassName('job_sent_failure');
					trNode.select('.pc_item_name')[0].up().up()
						.insert(new Element('span', {title: res.NoData}).update('NOP').addClassName('job_no_data'));
				}
				else {
					// Success
					try { trNode.select('input.item_select_input')[0].remove(); }
					catch(e) {}
					trNode.removeClassName('job_sent_failure');
					trNode.addClassName('job_sent_success');
					if (res.ClusterIds.length > 0) {
						var cid = res.ClusterIds[0].clusterId;
						trNode.select('.pc_item_name')[0].up().up()
							.insert(new Element('span', {title: 'Success: job cluster id is ' + cid}).update(cid).addClassName('job_sent'));
					}
				}
			}

			if (youpi_pc_meta.action_cur_value_idx < data.get(key).length-1)
				youpi_pc_meta.action_cur_value_idx++;
			else {
				youpi_pc_meta.action_cur_value_idx = 0;
				if (youpi_pc_meta.action_cur_key_idx < data.keys().length)
					youpi_pc_meta.action_cur_key_idx++;

			}
			if (youpi_pc_meta.action_cur_key_idx < data.keys().length) {
				// More items to process?
				youpi_pc_meta.action_pb_value++;
				youpi_pc_meta.progressBar.setPourcentage((youpi_pc_meta.action_pb_value/youpi_pc_meta.action_pb_total)*100);
				real_run_items(data);
			}
			else {
				// All items are sent
				youpi_pc_meta.progressBar.setPourcentage(100);
				$('cart_pbar_div').fade({delay: 5.0});

				// Builds a new hash of successfully sent jobs in order to delete them from 
				// user session (but keep them in the processing cart until page reload)
				var pluginName = trid.sub(/_\d+$/, '');
				var jdata = new Hash();
				$$('.job_sent_success').each(function(tr) {
					// -1 for the row header
					var idx = tr.previousSiblings().length-1;
					if (!jdata.get(pluginName))
						jdata.set(pluginName, new Array());
					jdata.get(pluginName).push(idx);
				});
				if (jdata.keys().length)
					real_delete_items(youpi_pc_meta.action_pb_total, jdata, false);
			}
		}
	);
	r.send('/youpi/process/plugin/', capitalizeHashKeys(opts).toQueryString());
}

/*
 * Function: do_run_items
 * Asks for confirmation first then call <real_run_items>()
 *
 * Parameters:
 *  count - integer: number of items to run
 *  data - object: items grouped by plugin name
 *
 */ 
function do_run_items(count, data) {
	boxes.confirm('Are you sure you want to run this item selection (' + count + ' item' + (count > 1 ? 's':'') + ') on the cluster?', 
		function() { 
			// Some init before calling the real stuff
			// Current key pos for saving in data.keys()
			youpi_pc_meta.action_cur_key_idx = 0;
			// Current position of item for that key
			youpi_pc_meta.action_cur_value_idx = 0;
			// For the progress bar
			youpi_pc_meta.action_pb_value = 0;
			youpi_pc_meta.action_pb_total = count;
			$('cart_pbar_div').appear();
			youpi_pc_meta.progressBar.setPourcentage(0);
			// Real stuff
			real_run_items(data); 
		}
	);
}

/*
 * Function: find_checked_items
 * Find checked inputs widgets in the processing cart
 *
 * Returns:
 *  data - hash: collection of checked items: {plugin_name1: [i0, ..., in], ..., plugin_nameN: [i0, ..., in]}
 *
 */ 
function find_checked_items() {
	var cursel = new Array();
	var checks = $$('table.shoppingCart input.item_select_input');
	checks.each(function(check) {
		if (check.checked)
			cursel.push(check);
	});
	var count = cursel.length;
	if (count == 0) 
		return null;
	// Builds input list of items to be deleted
	var data = new Hash();
	cursel.each(function(check) {
		var trid = check.up('tr').getAttribute('id');
		var pluginName = trid.sub(/_\d+$/, '');
		// -1 for the row header
		var idx = check.up('tr').previousSiblings().length-1;
		if (!data.get(pluginName))
			data.set(pluginName, new Array());
		data.get(pluginName).push(idx);
	});
	return data;
}

/*
 * Function: count_checked_items
 * Computes number of checked items from a collection of checked items
 *
 * Parameters:
 *  data - object: items grouped by plugin name
 *
 * Returns:
 *  count - integer: number of items in the collection
 *
 */ 
function count_checked_items(data) {
	var count = 0;
	data.keys().each(function(key) {
		count += data.get(key).length;
	});
	return count;
}

/*
 * Function: toggle_node_policy_radio
 *
 * Parameters:
 *  FIXME
 *
 */ 
function toggle_node_policy_radio(def_id, cus_id, cus_div_id) {
	var def = $(def_id);
	var cus = $(cus_id);
	var cusdiv = $(cus_div_id);
	cus.checked ? cusdiv.setStyle({paddingLeft: '20px'}).appear() : cusdiv.fade();
}

/*
 * Function: cart_select_all_items
 *
 * Parameters:
 *  FIXME
 *
 */ 
function cart_select_all_items(selectall) {
	var selectall = typeof selectall == 'boolean' ? selectall : true;
	$$('table.shoppingCart input.item_select_input').each(function(check) {
		check.checked = selectall;
	});
}

// A processing cart item has just been removed
document.observe('processingCart:itemRemoved', function(event) {
	// Is the processing cart empty?
	var container = menu.getContentNodeForCurrentEntry();
	if (!container.select('table.shoppingCart').length) {
		container.update();
		var d = new Element('div', {id: 'emptycart_div'}).setStyle({marginTop: '70px', padding: '5px'}).hide();
		d.update(new Element('h1').update('Your cart is currently empty'));
		container.insert(d);
		d.appear();
	}

	var msg = 'Item removed from the processing cart';
	if (typeof event.memo == 'number') msg = event.memo + ' item' + (event.memo > 1 ? 's':'') + ' removed from the processing cart';
	document.fire('notifier:notify', msg);
});

/*
 * Function: get_runtime_options
 * Returns per-item runtime options
 *
 * Called by used by {plugin}_run() functions
 *
 * Parameters:
 *  prefix_id - string: TR id that identifies a SC item uniquely
 *
 * Data Format:
 *  {reprocessValid: bool, itemPrefix: string, clusterPolicy: POST string}
 *
 * Returns:
 *  JSON object as described in Data Format
 *
 */ 
function get_runtime_options() {
	var options = {
		reprocessValid: false,
		itemPrefix: '',
		clusterPolicy: ''
	};
	options.reprocessValid = !$('reprocess_successful_checkbox').checked;
	options.itemPrefix = $('prefix_name_input').value.strip();
	var post = "CondorSetup=";
	if ($('node_policy_default').checked) {
		// Use default Condor setup configuration
		post += "default";
	}
	else {
		post += "custom";
		var sel = $('node_select');
		var opt = sel.options[sel.selectedIndex];
		if (opt.hasClassName('policy'))
			post += "&Policy=";
		else
			post += "&Selection=";
		post += opt.value;
	}
	options.clusterPolicy = post;
	return options;
}

function getSavedItemsStats() {
	var r = new HttpRequest(
			null,
			null,	
			// Custom handler for results
			function(resp) {
				var st = $H(resp.stats);
				st.keys().each(function(uid) {
					var total = st.get(uid);
					$('plugin_' + uid + '_saved_count').update(total > 0 ? total + ' item' + (total > 1 ? 's' : '') : 'No item');
					// Disable panel when no saved items in it
					if (total == 0) {
						var panel = $('plugin_' + uid + '_saved_count').up(sc_accordion.headers[0]);
						sc_accordion.headers.each(function(head, k) {
							if (head == panel) {
								sc_accordion.disable(k);
								throw $break;
							}
						});
					}
				});
			}
	);

	r.send('/youpi/cart/savedItemsStats/');
}

/*
 * Removes one item from the processing cart
 */
function removeItemFromCart(trid, force) {
	var silent = typeof force == 'boolean' ? force : false;
	var trNode = $(trid);
	var pluginName = trid.sub(/_\d+$/, '');
	var idx = trNode.previousSiblings().length - 1;

	// Ask for item deletion
	s_cart.deletePluginItem(
		{'plugin_name' : pluginName, 'idx' : idx},
		// Custom handler called when item deletion is complete
		function() {
			var table = trNode.up('table.shoppingCart');
			// Number of items left for that plugin
			var left = table.select('tr[id]').length;
			var n = left == 1 ? table : trNode;

			n.fade({ 
				afterFinish: function() { 
					n.remove(); 
					document.fire('processingCart:itemRemoved');
				}
			});
		}
	);
}

function update_condor_submission_log(resp, silent) {
	var silent = typeof silent == 'boolean' ? silent : false;
	var logdiv = document.getElementById('master_condor_log_div');
	var r = resp['result'];
	var log = new Logger(logdiv);
	log.clear();

	if (r['Error']) {
		log.msg_error(r['Error']);
		return false;
	}
	else if (r.NoData) {
		log.msg_ok(r.NoData);
		return false;
	}

	if (r['CondorError']) {
		var d = document.createElement('div');
		d.setAttribute('style', 'width: 50%;');
		d.setAttribute('class', 'warning');
		d.appendChild(document.createTextNode('Condor has returned a runtime error:'));
		var d2 = document.createElement('div');
		var pre = document.createElement('pre');
		pre.setAttribute('style', 'color: red; overflow: auto; text-align: left;');
		pre.appendChild(document.createTextNode(r['CondorError']));
		var tipd = document.createElement('div');
		tipd.innerHTML = 'If this is a parsing error in your Condor submission file, maybe ' +
			'the requirements you are using cause the error. In this case, you should have a look at the ' + 
			"<a href=\"/youpi/condor/setup/\">Condor Setup</a> page, check the <b>policies</b> and <b>selection" +
			'</b> your are using for this item submission.';

		d2.appendChild(pre);
		d.appendChild(d2);
		d.appendChild(tipd);
		logdiv.appendChild(d);
		return false;
	}

	if (!silent) {
		log.msg_ok('Done. Jobs successfully sent to the cluster.');
		var i = eval(r['ClusterIds']);
		for (var k=0; k < i.length; k++) {
			log.msg_ok(i[k]['count'] + ' job(s) submitted to cluster ' + i[k]['clusterId']);
		}
	}

	return true;
}


/*
 * Function: build_runtime_options
 * Builds a runtime options control panel suitable for the processing cart
 *
 * Returns:
 *  Parent DOM element node
 *
 */ 
function build_runtime_options() {
	var root = new Element('div', {id: 'ro_content'});
	var norepro = new Element('div').insert(new Element('input', {id: 'reprocess_successful_checkbox', type: 'checkbox', checked: 'checked'}))
		.insert(new Element('label').update('Do not reprocess already successful processings'));
	var item = new Element('div').insert(new Element('label').update('Item prefix name')).insert(new Element('input', {id: 'prefix_name_input', type: 'text'}));
	var idefault = new Element('input', {id: 'node_policy_default', type: 'radio', checked: 'checked', name: 'policy'});
	var icustom = new Element('input', {id: 'node_policy_custom', type: 'radio', name: 'policy'});

	var custom_sel = new Element('select', {id: 'node_select'}).hide();
	custom_sel.insert(new Element('option', {disabled: true}).addClassName('header').update("Policies"));
	youpi_pc_meta.saved_policies.each(function(pol) {
		var opt = new Element('option', {value: pol}).addClassName('policy').update(pol);
		custom_sel.insert(opt);
	});
	custom_sel.insert(new Element('option', {disabled: true}).addClassName('header').update("Selections"));
	youpi_pc_meta.saved_selections.each(function(sel) {
		var opt = new Element('option', {value: sel}).addClassName('selection').update(sel);
		custom_sel.insert(opt);
	});

	var policy = new Element('div', {id: 'ro_policy_div'}).update(new Element('label').update('Cluster node policy'))
		.insert(new Element('div')
			.insert(idefault)
			.insert(new Element('label').update('Use your default Condor setup configuration')))
		.insert(new Element('div')
			.insert(icustom)
			.insert(new Element('label').update('Select a custom configuration for this processing'))
			.insert(new Element('div').addClassName('cart_item_policy').update(custom_sel)));
	root.update(norepro).insert(item).insert(policy);

	idefault.observe('click', function() {
		$('node_select').hide();
	});
	icustom.observe('click', function() {
		$('node_select').show();
	});

	return root;
}

/*
 * Function displayImageCount
 * Renders list of images to be processed as a summary (used in the processing cart plugin rendering)
 *
 * Parameters:
 *
 * idList - array of arrays of idLists
 *
 */
function displayImageCount(idList, container_id) {
	var container = $(container_id);
	var idList = eval(idList);
	var c = 0;
	var txt;
	idList.length > 1 ? txt = 'Batch' : txt = 'Single';
	var selDiv = new Element('div').addClassName('selectionModeTitle').update(txt + ' selection mode: ');
	container.insert(selDiv);
	for (var k=0; k < idList.length; k++) {
		c = idList[k].toString().split(',').length;
		if (idList.length > 1)
			txt = 'Selection ' + (k+1) + ': ' + c + ' image' + (c > 1 ? 's' : '');
		else
			txt = c + ' image' + (c > 1 ? 's' : '');

		selDiv.insert(new Element('span').update(txt));
	}
	container.insert(selDiv);
}

