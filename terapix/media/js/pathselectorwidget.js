
if (!Youpi)
	var Youpi = {};

/*
 * Class: PathSelectorWidget
 * Simple widget that allows to add/select/delete multiple paths from a treeview.
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <PathSelectorWidget> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * varName - string: global variable name of instance, used internally for public interface definition
 * pluginId - string: plugin unique id
 *
 */
function PathSelectorWidget(container_id, varName, pluginId)
{
	// Name of instance if global namespace
	var instance_name = varName;
	var container = document.getElementById(container_id);
	var id = varName + '_psw_';
	var NO_SELECTION = '--';

	var plugin_id = pluginId ? pluginId : null;
	var file_browser = null;

	// List of tr DOM nodes to paths
	var tr_paths = new Array();
	var tr_prefix = new Array();
	var tr_mandatory = new Array();

	this.render = function() {
		var tr, th, td;

		var fd = document.createElement('div');
		fd.setAttribute('style', 'float: left; width: 400px');
		fd.setAttribute('id', plugin_id + '_fbw_div');
		container.appendChild(fd);

		var d = document.createElement('div');
		var tab = document.createElement('table');
		tab.setAttribute('class', 'flatmask');

		for (var k=0; k < tr_paths.length; k++) {
			tab.appendChild(tr_paths[k]);
		}

		d.appendChild(tab);
		container.appendChild(d);

		d = document.createElement('div');
		tab = document.createElement('table');
		tab.setAttribute('class', 'selectedPath');
		tr = document.createElement('tr');
		th = document.createElement('th');
		th.appendChild(document.createTextNode('Selected Path'));

		td = document.createElement('td');
		tdiv = document.createElement('div');
		tdiv.setAttribute('class', 'lightTip');
		tdiv.appendChild(document.createTextNode('Please note that you can append a file name to the selected path by typing its name in the box below.'));

		pin = document.createElement('input');
		pin.setAttribute('id', plugin_id + '_path_input');
		pin.setAttribute('type', 'text');
		pin.setAttribute('size', '80');
		pin.setAttribute('style', 'font-family: typewritter;');

		td.appendChild(tdiv);
		td.appendChild(pin);
		td.appendChild(document.createElement('br'));

		var sin;
		for (var k=0; k < tr_paths.length; k++) {
			sin = document.createElement('input');
			sin.setAttribute('type', 'button');
			sin.setAttribute('value', 'Save as ' + tr_prefix[k].toUpperCase());
			sin.setAttribute('style', 'margin-right: 5px');
			sin.setAttribute('onclick', instance_name + ".savePath('" + tr_prefix[k] + "');");
			td.appendChild(sin);
		}

		tr.appendChild(th);
		tr.appendChild(td);
		tab.appendChild(tr);
		d.appendChild(tab);
		container.appendChild(d);

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
					var div = document.getElementById(plugin_id + '_' + prefix + '_div');
					var msg_div;
					removeAllChildrenNodes(div);
					removeAllChildrenNodes(div);

					if (resp['result'][prefix].length == 0) {
						msg_div = document.getElementById(plugin_id + '_' + prefix + '_msg_div');
						msg_div.innerHTML = '';
						div.setAttribute('class', 'noFlagWeight');
						div.appendChild(document.createTextNode('No ' + prefix + ' paths available'));
					}
					else {
						// Insert element to the beginning
						resp['result'][prefix].unshift(NO_SELECTION);

						if(tr_mandatory[k]) {
							// This a mandatory path
							var m = document.createElement('span');
							m.setAttribute('class', 'mandatory_path');
							m.appendChild(document.createTextNode('MANDATORY'));
							div.appendChild(m);
						}
						sel = getSelect(plugin_id + '_' + prefix + '_select', resp['result'][prefix]);
						sel.setAttribute('onchange', instance_name + ".onPathChange('" + prefix + "', '" + sel.id + "')");
						div.appendChild(sel);
						img = document.createElement('img');
						img.setAttribute('style', 'cursor: pointer; margin-left: 5px;');
						img.setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/cancel.png');
						img.setAttribute('onclick', instance_name + ".deletePath('" + prefix + "')");
						div.appendChild(img);
		
						onPathChange(prefix, sel ? sel.id : null);
					}
				}
			}
		);

		var post = 'Plugin=' + plugin_id + '&Method=getMiscDataPaths&Keys=' + tr_prefix;
		r.send('/youpi/process/plugin/', post);
	}

	this.savePath = function(prefix) {
		var div, sel;
		div = document.getElementById(plugin_id + '_' + prefix + '_div');
		sel = document.getElementById(plugin_id + '_' + prefix + '_select');
	
		var pathNode = document.getElementById(plugin_id + '_path_input');
		var path = pathNode.value;
	
		if (!path.replace(/ /g,'').length) {
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

	this.deletePath = function(prefix) {
		var sel = document.getElementById(plugin_id + '_' + prefix + '_select');
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
		
	function onPathChange(prefix, selid) {
		var msg_div = document.getElementById(plugin_id + '_' + prefix + '_msg_div');
		if (!selid) {
			msg_div.innerHTML = '';
			return;
		}

		var sel = document.getElementById(selid);
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
		var mandatory = mandatory ? true : false;
		var tr, th, td;
		tr = document.createElement('tr');
		th = document.createElement('th');
		th.appendChild(document.createTextNode('Selected path to ' + title));
		td = document.createElement('td');
		td.setAttribute('id', plugin_id + '_' + prefix + '_td');
		td.setAttribute('style', 'vertical-align: middle');

		var md = document.createElement('div');
		md.setAttribute('id', plugin_id + '_' + prefix + '_msg_div');
		md.setAttribute('style', 'text-align: center');

		var d = document.createElement('div');
		d.setAttribute('id', plugin_id + '_' + prefix + '_div');
		d.setAttribute('style', 'text-align: center');

		td.appendChild(md);
		td.appendChild(d);
		tr.appendChild(th);
		tr.appendChild(td);

		tr_paths.push(tr);
		tr_prefix.push(prefix);
		tr_mandatory.push(mandatory);
	}

	this.setFileBrowser = function(fb_obj) {
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
	
		var pathNode = document.getElementById(plugin_id + '_path_input');
		pathNode.value = branch.struct.syspath.replace('//','/');
	
		var nb = branch.struct.num_children;
		var p = document.createElement('p');
	
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
