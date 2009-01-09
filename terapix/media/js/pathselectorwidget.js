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
	var _container = $(container);
	var NO_SELECTION = '--';

	var plugin_id = pluginId ? pluginId : null;
	var file_browser = null;

	// List of tr DOM nodes to paths
	var tr_paths = new Array();
	var tr_prefix = new Array();
	var tr_mandatory = new Array();

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
		tdiv = new Element('div');
		tdiv.setAttribute('class', 'lightTip');
		tdiv.insert('Please note that you can append a file name to the selected path ' + 
			'by typing its name in the box below.');

		pin = new Element('input');
		pin.setAttribute('id', plugin_id + '_path_input');
		pin.setAttribute('type', 'text');
		pin.setAttribute('size', '80');
		pin.setAttribute('style', 'font-family: typewritter;');

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

		loadExistingPaths();
	}

	function loadExistingPaths(afterLoadingHandler) {
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
					removeAllChildrenNodes(div);
					removeAllChildrenNodes(div);

					if (resp['result'][prefix].length == 0) {
						msg_div = $(plugin_id + '_' + prefix + '_msg_div');
						msg_div.innerHTML = '';
						div.setAttribute('class', 'noFlagWeight');
						div.insert('No ' + prefix + ' paths available');
					}
					else {
						// Insert element to the beginning
						resp['result'][prefix].unshift(NO_SELECTION);

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
				loadExistingPaths();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=saveMiscDataPath&Path=' + path + '&Key=' + prefix;
		r.send('/youpi/process/plugin/', post);
	}

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
				loadExistingPaths();
			}
		);

		var post = 'Plugin=' + plugin_id + '&Method=deleteMiscDataPath&Path=' + path + '&Key=' + prefix;
		r.send('/youpi/process/plugin/', post);
	}
	
	this.onPathChange = function(prefix, selid) {
		onPathChange(prefix, selid);
	}
		
	function _onPathChange(prefix, selid) {
		var msg_div = $(plugin_id + '_' + prefix + '_msg_div');
		if (!selid) {
			msg_div.innerHTML = '';
			return;
		}

		var sel = $(selid);
		var txt = sel.options[sel.selectedIndex].text;
		var d;
	
		var msg = prefix.toUpperCase();
	
		if (txt == NO_SELECTION) {
			// No selection (default)
			msg_div.setAttribute('class', 'lightTip');
			msg_div.innerHTML = 'Please make a selection below:';

		}
		else if (txt[txt.length-1] != '/') {
			// This is a file
			msg_div.setAttribute('class', 'lightTip');
			msg_div.innerHTML = 'This following file will <strong>overwrite</strong> paths to ' + msg + ' data. This ' + msg + ' file will be used for all images in the selection:';
		}
		else {
			// This is a directory
			msg_div.setAttribute('class', 'lightTip');
			msg_div.innerHTML = msg + ' files will be searched in the following directory:';
		}
	}

	// mandatory: boolean
	this.addPath = function(title, prefix, mandatory) {
		var mandatory = typeof mandatory == 'boolean' ? mandatory : false;
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

	this.setFileBrowser = function(fb_obj) {
		if (!typeof fb_obj == 'object')
			console.error('Argument must be a FileBrowser instance, not ' + typeof fb_obj + '!');

		file_browser = fb_obj ? fb_obj : null;
		file_browser.setBranchClickedHandler(branchClickedHandler);
	}

	this.getFileBrowser = function() {
		return file_browser;
	}

	this.getBranchClickedHandler = function() {
		return branchClickedHandler;
	}

	function branchClickedHandler(branch) {
		var id = branch.getId();
	
		// Exit if root node or FITS image (leaf)
		if (id == 'root')
			return;
	
		var pathNode = $(plugin_id + '_path_input');
		pathNode.value = branch.struct.syspath.replace('//','/');
	
		var nb = branch.struct.num_children;
		var p = new Element('p');
	
		if (nb > 0) {
			// directory contains files
		}
		else {
			// No files in it
		}
	}

	this.getNoSelectionPattern = function() {
		return NO_SELECTION;
	}

	this.getMandatoryPrefixes = function() {
		var mandvars = new Array();
		for (var k=0; k < tr_prefix.length; k++) {
			if (tr_mandatory[k])
				mandvars.push(tr_prefix[k]);
		}

		return mandvars;
	}
}
