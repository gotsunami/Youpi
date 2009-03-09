/*
 * Class: PathSelectorWidget
 * Simple widget that allows to add/select/delete multiple paths from a treeview.
 *
 * Constructor Parameters:
 *
 * container - string or DOM node: name of parent DOM block container
 * pluginId - string: plugin unique id
 *
 */
function PathSelectorWidget(container, pluginId)
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * DOM parent container
	 *
	 */ 
	var _container = $(container);
	/*
	 * Var: NO_SELECTION
	 * String used to show that no selection has been made
	 *
	 */ 
	var NO_SELECTION = '--';


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: plugin_id
	 * Internal name of plugin. Used to call AJAX functions
	 *
	 */ 
	var plugin_id = typeof pluginId == 'string' ? pluginId : console.error('plugin_id must be a string for plugin unique ID!');
	/*
	 * Var: file_browser
	 * Internal name of plugin. Used to call AJAX functions
	 *
	 */ 
	var file_browser = null;

	// List of tr DOM nodes to paths
	var tr_paths = new Array();
	var tr_prefix = new Array();
	var tr_mandatory = new Array();
	/*
	 * Var: _extra
	 * Object of options for extra entry
	 * : _extra = {title: null, selected: false, help: null};
	 *
	 * See Also:
	 *  <addPath>
	 *
	 */ 
	var _extra = {title: null, selected: false, help: null};

	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: render
	 * Initial rendering step
	 *
	 * This is the main entry point.
	 *
	 */ 
	this.render = function() {
		var tr, th, td;

		var fd = new Element('div');
		fd.setAttribute('style', 'float: left; width: 400px');
		fd.setAttribute('id', plugin_id + '_fbw_div');
		_container.insert(fd);

		var d = new Element('div');
		var tab = new Element('table');
		tab.setAttribute('class', 'flatmask');

		for (var k=0; k < tr_paths.length; k++) {
			tab.insert(tr_paths[k]);
		}

		d.insert(tab);
		_container.insert(d);

		d = new Element('div');
		tab = new Element('table');
		tab.setAttribute('class', 'selectedPath');
		tr = new Element('tr');
		th = new Element('th');
		th.insert('Selected Path');

		td = new Element('td');
		tdiv = new Element('div', {'class': 'lightTip'});
		tdiv.insert('Please note that you can append a file name to the selected path ' + 
			'by typing its name in the box below.');

		pin = new Element('input', {
					id: plugin_id + '_path_input',
					type: 'text',
					size: 80,
					style: 'font-family: typewritter;'
		});

		td.insert(tdiv);
		td.insert(pin);
		td.insert(new Element('br'));

		var sin;
		for (var k=0; k < tr_paths.length; k++) {
			sin = new Element('input', {
					type: 'button', 
					value: 'Save as ' + tr_prefix[k].toUpperCase(),
					style: 'margin-right: 5px'
			});
			sin.tr_prefix = tr_prefix[k];
			sin.observe('click', function() {
				_savePath(this.tr_prefix);
			});
			td.insert(sin);
		}

		tr.insert(th);
		tr.insert(td);
		tab.insert(tr);
		d.insert(tab);
		_container.insert(d);

		_loadExistingPaths();
	}

	/*
	 * Function: _loadExistingPaths
	 * Loads stored data paths into the combobox
	 *
	 * Parameters:
	 *  afterLoadingHandler - function: custom handler to execute (NOT YET IMPLEMENTED)
	 *
	 */ 
	function _loadExistingPaths(afterLoadingHandler) {
		var handler = afterLoadingHandler ? afterLoadingHandler : null;
		var r = new HttpRequest(
			null,
			null,
			// Custom handler for results
			function(resp) {
				var img, sel = null;

				for (var k=0; k < tr_prefix.length; k++) {
					var prefix = tr_prefix[k];
					var div = $(plugin_id + '_' + prefix + '_div');
					var msg_div;
					div.update();

					if (resp.result[prefix].length == 0 && !_extra.title) {
						msg_div = $(plugin_id + '_' + prefix + '_msg_div');
						msg_div.innerHTML = '';
						div.setAttribute('class', 'noFlagWeight');
						div.insert('No ' + prefix + ' paths available');
					}
					else {
						// Insert element to the beginning
						if (_extra.title)
							resp.result[prefix].unshift(_extra.title);
						resp.result[prefix].unshift(NO_SELECTION);

						if(tr_mandatory[k]) {
							// This a mandatory path
							var m = new Element('span');
							m.setAttribute('class', 'mandatory_path');
							m.insert('MANDATORY');
							div.insert(m);
						}
						sel = getSelect(plugin_id + '_' + prefix + '_select', resp['result'][prefix]);
						sel.pathChange = {prefix: prefix, selid: sel.id};
						sel.observe('change', function() {
							_onPathChange(this.pathChange.prefix, this.pathChange.selid);
						});
						if (_extra.selected)
							sel.options[1].writeAttribute({selected: 'selected'});
						div.insert(sel);
						img = new Element('img', {
							style: 'cursor: pointer; margin-left: 5px;',
							src: '/media/themes/' + guistyle + '/img/16x16/cancel.png'
						});
						img.kind_prefix = prefix;
						img.observe('click', function() {
							_deletePath(this.kind_prefix);
						});
						div.insert(img);
		
						_onPathChange(prefix, sel ? sel.id : null);
					}
				}
			}
		);

		var post = 'Plugin=' + plugin_id + '&Method=getMiscDataPaths&Keys=' + tr_prefix;
		r.send('/youpi/process/plugin/', post);
	}

	/*
	 * Function: setDefaultEntry
	 * Creates a new entry and selects it
	 *
	 * Parameters:
	 *  label - string: text for entry
	 *
	 */ 
	this.setDefaultEntry = function(label) {
		if (!typeof label == 'string')
			console.error('label must be a string!');

		_hasDefaultEntry = true;
		_defaultEntry = label;
		$(plugin_id + '_' + prefix + '_select')
	}

	/*
	 * Function: _savePath
	 * Loads stored data paths into the combobox
	 *
	 * Parameters:
	 *  prefix - string: 2nd arg of <addPath>
	 *
	 */ 
	function _savePath(prefix) {
		var div, sel;
		div = $(plugin_id + '_' + prefix + '_div');
		sel = $(plugin_id + '_' + prefix + '_select');
	
		var pathNode = $(plugin_id + '_path_input');
		var path = pathNode.value;
	
		if (path.empty()) {
			alert('The selected path is empty! There is nothing to add. Please select a path in the path selector on the left.');
			return;
		}
	
		var r = new HttpRequest(
			div.id,
			null,
			// Custom handler for results
			function(resp) {
				// Refresh data
				_loadExistingPaths();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=saveMiscDataPath&Path=' + path + '&Key=' + prefix;
		r.send('/youpi/process/plugin/', post);
	}

	/*
	 * Function: _deletePath
	 * Deletes currently selected data path
	 *
	 * Parameters:
	 *  prefix - string: 2nd arg of <addPath>
	 *
	 */ 
	function _deletePath(prefix) {
		var sel = $(plugin_id + '_' + prefix + '_select');
		var path = sel.options[sel.selectedIndex].text;

		if (path == NO_SELECTION) {
			alert("Cannot delete this entry. Please select a real path to delete.");
			return;
		}
	
		var r = confirm("Are you sure you want to delete '" + path + "' path?");
		if (!r) return;
	
		var r = new HttpRequest(
			sel.id,
			null,
			// Custom handler for results
			function(resp) {
				// Refresh data
				_loadExistingPaths();
			}
		);

		var post = 'Plugin=' + plugin_id + '&Method=deleteMiscDataPath&Path=' + path + '&Key=' + prefix;
		r.send('/youpi/process/plugin/', post);
	}
	
	/*
	 * Function: _onPathChange
	 * Updates the UI when a new data path is selected
	 *
	 * Parameters:
	 *  prefix - string: 2nd arg of <addPath>
	 *
	 */ 
	function _onPathChange(prefix, selid) {
		var msg_div = $(plugin_id + '_' + prefix + '_msg_div');
		if (!selid) {
			msg_div.update();
			return;
		}

		var sel = $(selid);
		var txt = sel.options[sel.selectedIndex].text;
		var d;
	
		var msg = prefix.toUpperCase();
		msg_div.setAttribute('class', 'lightTip');

		if (txt == NO_SELECTION) {
			// No selection (default)
			msg_div.update('Please make a selection below:');
		}
		else if (txt[txt.length-1] != '/' && !_extra.title) {
			// This is a file
			msg_div.update('This following file will <strong>overwrite</strong> paths to ' + msg + ' data. This ' + msg + ' file will be used for all images in the selection:');
		}
		else if (txt == _extra.title) {
			msg_div.update(_extra.help + ':');
		}
		else {
			// This is a directory
			msg_div.update(' files will be searched in the following directory:');
		}
	}

	/*
	 * Function: hasExtra
	 * Returns true is an extra path option has been defined with <addPath>
	 *
	 * Returns:
	 *  boolean
	 *
	 */
	this.hasExtra = function() {
		return _extra.title ? true : false;
	}

	/*
	 * Function: getExtra
	 * Returns extra option value for a path entry (See <addPath> for more info)
	 *
	 * Returns:
	 *  <_extra>: object
	 *
	 */
	this.getExtra = function() {
		return _extra;
	}

	/*
	 * Function: addPath
	 * Add a new data path combobox to the widget
	 *
	 * Parameters:
	 *  title - string: title displayed
	 *  prefix - string: name of internal prefix name to be used (one word)
	 *  options - object: hash for options (see below)
	 *
	 * Options:
	 *  The *options* parameter is an object of the form: 
	 *  (code)
	 *  {mandatory: true, extra: {
	 *			title: "My option's title", 
	 *			help: 'Use it to do anything',
	 *			selected: true
	 *  }} 
	 *  (end)
	 *  Optional properties are:
	 *
	 *  mandatory - boolean: specify whether this path is mandatory (i.e. no <NO_SELECTION> allowed)
	 *  extra - object: adds an extra entry (not a path name) to combo box (See below)
	 *
	 * The extra property:
	 *  The *extra* option has the following properties:
	 *
	 *  title - string: option's title (required)
	 *  help - string: help string used to display information on item selection (required)
	 *  selected -  boolean: true if you want it selected instead of the <NO_SELECTION> (optional)
	 *
	 * Notes:
	 *  _prefix_ variable must be one word (no spaces allowed).
	 *
	 * See Also:
	 *  <hasExtra>, <getExtra>
	 *
	 */ 
	this.addPath = function(title, prefix, options) {
		if (typeof options != 'object')
			options = {mandatory: false};

		var mandatory = typeof options.mandatory == 'boolean' ? options.mandatory : false;

		if (typeof options.extra == 'object') {
			if (typeof options.extra.title != 'string')
				console.error('extra object does not have its title property set (required)');

			if (typeof options.extra.help != 'string')
				console.error("'extra object does not have its 'help' property set (required)");
			
			_extra = options.extra;
		}

		var tr, th, td;
		tr = new Element('tr');
		th = new Element('th').insert('Selected path to ' + title);
		td = new Element('td', {id: plugin_id + '_' + prefix + '_td', style: 'vertical-align: middle'});

		var md = new Element('div', {id: plugin_id + '_' + prefix + '_msg_div', style: 'text-align: center'});
		var d = new Element('div', {id: plugin_id + '_' + prefix + '_div', style: 'text-align: center'});

		td.insert(md).insert(d);
		tr.insert(th).insert(td);

		tr_paths.push(tr);
		tr_prefix.push(prefix);
		tr_mandatory.push(mandatory);
	}

	/*
	 * Function: setFileBrowser
	 * Attaches to a <FileBrowser> instance
	 *
	 * Parameters:
	 *  fb_obj - object: <FileBrowser> instance
	 *
	 * Notes:
	 *  The <FileBrowser> instance is used to select a data path from the tree.
	 *
	 */ 
	this.setFileBrowser = function(fb_obj) {
		if (!typeof fb_obj == 'object')
			console.error('Argument must be a FileBrowser instance, not ' + typeof fb_obj + '!');

		file_browser = fb_obj ? fb_obj : null;
		file_browser.setBranchClickedHandler(_branchClickedHandler);
	}

	/*
	 * Function: getFileBrowser
	 * Returns current <FileBrowser> instance
	 *
	 * Returns:
	 *  <FileBrowser> instance
	 *
	 */ 
	this.getFileBrowser = function() {
		return file_browser;
	}

	/*
	 * Function: getBranchClickedHandler
	 * Returns a reference to <branchClickedhandler> function
	 *
	 * Returns:
	 *  <_branchClickedHandler> instance
	 *
	 */ 
	this.getBranchClickedHandler = function() {
		return _branchClickedHandler;
	}

	/*
	 * Function: _branchClickedHandler
	 * Custom handler for the <file_browser> private instance.
	 *
	 * Parameters:
	 *  branch - object
	 *
	 */ 
	function _branchClickedHandler(branch) {
		var id = branch.getId();
	
		// Exit if root node or FITS image (leaf)
		if (id == 'root')
			return;
	
		var pathNode = $(plugin_id + '_path_input');
		try {
			pathNode.value = branch.struct.syspath.replace('//','/');
		} catch(err) {
			// Click on a leaf; no syspath defined
		}
	
		var nb = branch.struct.num_children;
		var p = new Element('p');
	
		if (nb > 0) {
			// directory contains files
		}
		else {
			// No files in it
		}
	}

	/*
	 * Function: _getNoSelectionPattern
	 * Returns the <NO_SELECTION> constant string
	 *
	 * Parameters:
	 *  branch - object
	 *
	 */ 
	this.getNoSelectionPattern = function() {
		return NO_SELECTION;
	}

	/*
	 * Function: getMandatoryPrefixes
	 * Returns an array of mandatory prefixes
	 *
	 * Returns:
	 *  mandvars - array: mandatory prefixes
	 *
	 */ 
	this.getMandatoryPrefixes = function() {
		var mandvars = new Array();
		for (var k=0; k < tr_prefix.length; k++) {
			if (tr_mandatory[k])
				mandvars.push(tr_prefix[k]);
		}

		return mandvars;
	}
}
