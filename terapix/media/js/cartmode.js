/*****************************************************************************
 *
 * Copyright (c) 2008-2010 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/

/*
 * Object: cartmode
 * Adds automatic submission capabilities to the process cart
 *
 * Signals:
 *  CartMode:newSelection - signal emitted when the a new selection of items is made
 *
 */
var cartmode = {
	initialized: false,
	/*
	 * Variable: mode
	 * 
	 * Available Swarp modes: manual (default) or automatic
	 *
	 */
	mode: {MANUAL: 1, AUTOMATIC: 2},
	/*
	 * Constant: PROCESS_BUTTON_CAPTION
	 * 
	 * Button title
	 *
	 */
	PROCESS_BUTTON_CAPTION: 'Process',
	/*
	 * Constant: PAUSE_BUTTON_CAPTION
	 * 
	 * Pause button title
	 *
	 */
	PAUSE_BUTTON_CAPTION: 'Pause',
	/*
	 * Variable: curMode
	 * 
	 * Current Swarp mode (in use)
	 *
	 */
	curMode: null,
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
	 * Function: getSavedSelections
	 * Gets a list of saved selections
	 *
	 * Parameters:
	 *	handler - function: custom handler called with result data as parameter
	 *
	 */ 
	getSavedSelections: function(container, handler) {
		var r = new HttpRequest(
				container,
				null,	
				// Custom handler for results
				function(resp) {
					var data = resp.data;
					if (typeof handler == 'function')
						handler(data);
				}
		);
		r.send('/youpi/ims/collection/savedselections/');
	},
	/*
	 * Function: autoProcessSelections
	 * Auto-process selections of images
	 */ 
	autoProcessSelections: function() {
		// Custom output directory
		var output_data_path = $('output_target_path').innerHTML;
	
		// Set mandatory structures
		var p_data = {	plugin_name : this.plugin_id, 
						userData : {resultsOutputDir: output_data_path}
		};

		var r = new HttpRequest(
			null,
			null,	
			// Custom handler for results
			function(resp) {
				res = resp.result;
				// Adds entry to processing cart
				res.resultsOutputDir = output_data_path;
				if (this.auto_handler) {
					// Call custom handler
					this.auto_handler(res);
				}
				if (res.warning.length > 0) {
					$(this.plugin_id + '_automatic_log').insert('<br/><br/>').insert('Selection <b>' + this.autoSelections[0][this.curSelectionIdx] + '</b>:<br/>');
					this.autoWarningCount += res.warning.length;
					res.warning.each(function(w) {
						$(this.plugin_id + '_automatic_log').insert(w + '<br/>');
					}.bind(this));
				}
				$(this.plugin_id + '_automatic_warning').update(this.autoWarningCount + ' warning' + (this.autoWarningCount>1?'s':''));
				this.autoCurSelectionImageCount = res.imgCount;
				// Prepares recursive call
				this.curSelectionIdx++;
				if (this.curSelectionIdx < this.autoSelections[0].length) {
					if (!this.pauseAutoProcess)
						this.autoProcessSelections();
				}
				else {
					// All selections processed
					this.autoProgressBar.setPourcentage(100);
					// Reset values
					this.curSelectionIdx = 0;
					this.autoWarningCount = 0;
					$('process_sels_submit').update(this.PROCESS_BUTTON_CAPTION).removeClassName('PAUSE');
					// Send final notification message
					document.fire('notifier:notify', 'The selection has been added to the processing cart');
				}
			}.bind(this)
		);

		this.autoProgressBar.setPourcentage((this.curSelectionIdx/this.autoSelections[0].length)*100);
		var post = $H({
			Plugin: this.plugin_id,
			Method: 'autoProcessSelection',
			SelName: this.autoSelections[0][this.curSelectionIdx]
		});
		post.update(this.auto_params);
		// Send HTTP POST request
		r.send('/youpi/process/plugin/', post.toQueryString());
	},
	/*
	 * Handles cart's current working mode changes
	 *
	 */
	refreshCartMode: function(root) {
		if(this.curMode == null)
			throw "Cart current running mode not set";
		var root = $(root);
		var d = new Element('div').addClassName('cart_mode').update('Cart mode: ');
		var m, a;
		var caption = ' (change to ';
		if (this.curMode == this.mode.MANUAL) {
			m = new Element('span').addClassName('cart_active_mode').update('Manual');
			a = new Element('a', {href: '#'}).update('Automatic');
			a.observe('click', function() {
				this.curMode = this.mode.AUTOMATIC;
				this.refreshCartMode(root);
			}.bind(this));
			d.insert(m).insert(caption).insert(a).insert(')');
			try {
				if (this.hidden_entries)
					this.hidden_entries.invoke('show');
			}
			catch(e) {
				console.error('Some hidden entries are null! ' + this.hidden_entries);
			}
			$(this.plugin_id + '_automatic_div').hide();
			// Change menu entry caption
			menu.getEntry(0).select('a')[0].update('Select images');
		}
		else {
			// Automatic
			m = new Element('a', {href: '#'}).update('Manual');
			m.observe('click', function() {
				this.curMode = this.mode.MANUAL;
				this.refreshCartMode(root);
			}.bind(this));
			a = new Element('span').addClassName('cart_active_mode').update('Automatic');
			d.insert(a).insert(caption).insert(m).insert(')');
			// Hide/show panels
			if (this.hidden_entries)
				this.hidden_entries.invoke('hide');
			var ad = $(this.plugin_id + '_automatic_div').show();
			// Change menu entry caption
			menu.getEntry(0).select('a')[0].update('Select selections');

			var auto = $(this.plugin_id + '_automatic_sels').show();
			if (auto.empty()) {
				$('process_sels_submit').observe('click', function() {
					if (this.autoSelections.length == 0) {
						alert('Please make a selection first!');
						return;
					}
					boxes.confirm('Those image selections will be processed with the data paths to weight/head ' +
						'files and output directory parameters you specifed (or with default values).<br/><br/>Proceed?'
						, function() {
						if (this.before_handler)
							this.before_handler();
						if (!this.autoProgressBar) {
							this.autoProgressBar = new ProgressBar('automatic_pb_div', 0, {
								animate: false,
								color: '#ffe9c4',
								borderColor: '#ed9600',
								width: 400,
								height: 20,
								captionClassName: 'cart_caption'
							});
						}
						if ($('process_sels_submit').hasClassName('PAUSE')) {
							this.pauseAutoProcess = true;
							$('process_sels_submit').update(this.PROCESS_BUTTON_CAPTION).removeClassName('PAUSE');
							document.fire('notifier:notify', 'Paused, click again to resume');
						}
						else {
							$('automatic_pb_div').show();
							$('process_sels_submit').update(this.PAUSE_BUTTON_CAPTION).addClassName('PAUSE');
							$(this.plugin_id + '_automatic_warning').update(this.autoWarningCount + ' warning' + (this.autoWarningCount>1?'s':''));
							if (this.curSelectionIdx == 0)
								$(this.plugin_id + '_automatic_log').update();
							this.pauseAutoProcess = false;
							this.autoProcessSelections();
						}
					}.bind(this));
				}.bind(this));
				this.getSavedSelections(auto, function(data) {
					$('submit_automatic_sels').show();
					var s = new Element('select', {id: this.plugin_id + '_sels_select', size: 25, multiple: 'multiple'}).setStyle({width: '90%'});
					data.each(function(sel, k) {
						s.insert(new Element('option', {value: sel}).update(new Element('span').update(k+1).addClassName('option_num')).insert(' ' + sel));
					});
					s.observe('change', function() {
						var sel = new Array();
						$A(this.options).each(function(opt) {
							if (opt.selected) sel.push(opt.value);
						});
						$('sel_count_div').update('Selected ' + sel.length + ' out of ' + this.options.length);
						document.fire('CartMode:newSelection', sel); 
					});
					auto.update(s);
					$('process_sels_submit').update(this.PROCESS_BUTTON_CAPTION);
				}.bind(this));
			}	
		}
		root.update(d);
		menu.activate(0);
	},
	/*
	 * Function: initPanel
	 * Widget's initialisation
	 *
	 */ 
	initPanel: function() {
		var c = menu.getContentNodeForEntry(menu.getEntry(0));
		var d = new Element('div', {id: this.plugin_id + '_automatic_div'}).setStyle({width: '90%'});
		var sc = new Element('div', {id: 'sel_count_div'}).addClassName('largy').update('Please make a selection of image selections:');
		var ac = new Element('div', {id: this.plugin_id + '_automatic_sels'});
		var sac = new Element('div', {id: 'submit_automatic_sels'});
		var usac = new Element('ul');
		var isac = new Element('li', {id: 'process_sels_submit'}).addClassName('action_button');
		usac.insert(isac);
		isac = new Element('li', {id: 'automatic_pb_div'}).setStyle({listStyle: 'none'});
		usac.insert(isac);
		var aw = new Element('div', {id: this.plugin_id + '_automatic_warning'}).addClassName('largy');
		var al = new Element('div', {id: this.plugin_id + '_automatic_log'}).setStyle({height: '500px', overflow: 'auto', textAlign: 'left', color: 'brown'});
		sac.update(usac);
		c.insert(d.update(sc).insert(ac).insert(sac).insert(aw).insert(al));
	},
	/*
	 * Function: init
	 * Entry point
	 *
	 * Parameters:
	 *	plugin_id - string: unique plugin identifier
	 *	hidden_entries - array: list of DOM nodes to hide/show when changing selector mode
	 *	auto_params - object: extra parameters passed as is to the <autoProcessSelections> plugin function
	 *	before_handler - function: custom handler called just before doing the real stuff, and just after validating the confirm box
	 *	auto_handler - function: custom handler called on each iteration with the results as single parameter
	 *
	 */ 
	init: function(plugin_id, hidden_entries, auto_params, before_handler, auto_handler) {
		if (typeof plugin_id != 'string')
			throw "plugin_id must be a string";
		if (typeof auto_params != 'object')
			throw "auto_params must be an object";
		if (typeof auto_handler != 'function')
			throw "auto_handler must be a function";
		if (this.initialized) return;
		this.plugin_id = plugin_id;
		this.hidden_entries = hidden_entries;
		this.auto_params = auto_params;
		this.before_handler = typeof before_handler == 'function' ? before_handler : null;
		this.auto_handler = auto_handler;

		this.curMode = this.mode.MANUAL;
		var d = new Element('div', {id: plugin_id + '_mode_div'});

		$$('#content div')[0].insert(d);
		this.curSelectionIdx = 0;
		this.autoWarningCount = 0;
		this.initPanel();
		$(this.plugin_id + '_automatic_div').hide();
		$('submit_automatic_sels').hide();
		this.refreshCartMode(d);

		// Connects to custom signal
		document.observe('CartMode:newSelection', function(event) {
			this.autoSelections = new Array(event.memo);
		}.bind(this));
		this.initialized = true;
	}
};

