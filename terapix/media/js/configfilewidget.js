if (!Spica2)
	var Spica2 = {};

/*
 * Class: ConfigFileWidget
 * Simple widget that allows to select a configuration file to use with a processing plugin
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <ConfigFileWidget> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * varName - string: global variable name of instance, used internally for public interface definition
 * pluginId - string: unique plugin id
 *
 */
function ConfigFileWidget(container_id, varName, pluginId)
{
	// Name of instance if global namespace
	var instance_name = varName;
	var container = document.getElementById(container_id);
	var id = varName + '_cfw_';
	var plugin_id = pluginId ? pluginId : null;

	function render() {
		var tr, th, td;
		var tab = document.createElement('table');
		tab.setAttribute('class', 'fileBrowser');

		tr = document.createElement('tr');
		th = document.createElement('th');
		th.appendChild(document.createTextNode('Config File'));
		tr.appendChild(th);
		tab.appendChild(tr);

		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('style', 'vertical-align: middle');
		td.appendChild(document.createTextNode('Select a configuration file to use for processing:'));

		var butd = document.createElement('div');
		var bnew = document.createElement('input');
		bnew.setAttribute('type', 'button');
		bnew.setAttribute('value', 'New');
		bnew.setAttribute('style', 'float: left; margin-right: 5px');
		bnew.setAttribute('onclick', instance_name + '.displayNewConfigFile();');

		var bedit = document.createElement('input');
		bedit.setAttribute('type', 'button');
		bedit.setAttribute('value', 'Edit selected');
		bedit.setAttribute('style', 'float: left; margin-right: 5px');
		bedit.setAttribute('onclick', instance_name + '.editSelectedConfigFile();');

		var ndiv = document.createElement('div');
		ndiv.setAttribute('id', id + '_config_name_div');
		ndiv.setAttribute('style', 'float: right');

		butd.appendChild(bnew);
		butd.appendChild(bedit);
		butd.appendChild(ndiv);
		td.appendChild(butd);
		tr.appendChild(td);
		tab.appendChild(tr);
		container.appendChild(tab);

		// Label div, reports current conf selected file
		ndiv = document.createElement('div');
		ndiv.setAttribute('id', id + '_config_current_div');
		ndiv.setAttribute('style', 'margin-top: 15px; color: brown; font-weight: bold');
		container.appendChild(ndiv);

		// Editor div
		ndiv = document.createElement('div');
		ndiv.setAttribute('id', id + '_config_editor_div');
		ndiv.setAttribute('style', 'display: none;');
		tab = document.createElement('table');
		tab.setAttribute('class', 'fileBrowser');

		tr = document.createElement('tr');
		th = document.createElement('th');
		th.setAttribute('colspan', '2');
		th.appendChild(document.createTextNode('Config File Editor'));
		tr.appendChild(th);
		tab.appendChild(tr);

		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('id', id + '_config_editor_td');
		var ldiv = document.createElement('div');
		ldiv.setAttribute('id', id + '_editor_loading');
		var tarea = document.createElement('textarea');
		tarea.setAttribute('id', id + '_config_textarea');
		tarea.setAttribute('rows', '30');
		tarea.setAttribute('cols', '100');
		td.appendChild(ldiv);
		td.appendChild(tarea);
		tr.appendChild(td);

		td = document.createElement('td');
		td.setAttribute('style', id + 'background-color: #eaeaea; border-left: 2px solid #5b80b2; width: 30%');
		ldiv = document.createElement('div');
		var bsave = document.createElement('input');
		bsave.setAttribute('type', 'button');
		bsave.setAttribute('value', 'Save config as...');
		bsave.setAttribute('onclick', instance_name + '.saveConfigFileAs();');
		var sdiv = document.createElement('div');
		sdiv.setAttribute('id', id + '_config_save_div');
		sdiv.setAttribute('class', 'imageSelector');
		ldiv.appendChild(bsave);
		ldiv.appendChild(sdiv);
		sdiv = document.createElement('div');
		var bclose = document.createElement('input');
		bclose.setAttribute('type', 'button');
		bclose.setAttribute('value', 'Close editor');
		bclose.setAttribute('onclick', instance_name + '.closeEditor();');
		sdiv.appendChild(bclose);
		td.appendChild(ldiv);
		td.appendChild(sdiv);
		tr.appendChild(td);

		tab.appendChild(tr);
		ndiv.appendChild(tab);
		container.appendChild(ndiv);
	}

	this.displayCurrentConfUsed = function() {
		displayCurrentConfUsed();
	}

	function displayCurrentConfUsed() {
		var selNode = document.getElementById(plugin_id + '_config_name_select');
		var txt = selNode.options[selNode.selectedIndex].text;
		var curConfDiv = document.getElementById(id + '_config_current_div');
		removeAllChildrenNodes(curConfDiv);
		curConfDiv.appendChild(document.createTextNode("The '" + txt + "' configuration file will be used for processing."));
	}
	
	this.displayNewConfigFile = function() {
		editConfigFile('default');
	}

	this.editSelectedConfigFile = function() {
		var sel = document.getElementById(plugin_id + '_config_name_select');
		var conf = sel.options[sel.selectedIndex].text;
		editConfigFile(conf);
	}

	this.closeEditor = function() {
		var div = document.getElementById(id + '_config_editor_div');
		div.setAttribute('style', 'display: none');
	}

	function editConfigFile(configName) {
		var ldiv = document.getElementById(id + '_editor_loading');
		var div = document.getElementById(id + '_config_editor_div');
		div.setAttribute('style', 'display: block');
	
		var r = new HttpRequest(
			ldiv.id,
			null,
			// Custom handler for results
			function(resp) {
				ldiv.innerHTML = '';
				var edit = document.getElementById(id + '_config_textarea');
				edit.value = resp['result'];
				edit.focus();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=getConfigFileContent&Name=' + configName;
		r.send('/youpi/process/plugin/', post);
	}

	this.saveConfigFileAs = function() {
		var div = document.getElementById(id + '_config_save_div');
		var sub = document.getElementById(id + '_config_save_subdiv');
	
		if (!sub) {
			sub = document.createElement('div');
			sub.setAttribute('id', id + '_config_save_subdiv');
			sub.setAttribute('class', 'show');
	
			var txt = document.createElement('input');
			txt.setAttribute('style', 'float: left; margin-right: 5px;');
			txt.setAttribute('id', id + '_config_save_text');
			txt.setAttribute('type', 'text');
			sub.appendChild(txt);
	
			var save = document.createElement('input');
			save.setAttribute('type', 'button');
			save.setAttribute('onclick', instance_name + ".saveConfig();");
			save.setAttribute('value', 'Save!');
			sub.appendChild(save);
	
			var res = document.createElement('div');
			res.setAttribute('id', id + '_config_save_res_div');
			res.setAttribute('style', 'vertical-align: middle');
			sub.appendChild(res);
	
			div.appendChild(sub);
	
			// Add auto-completion capabilities
			try {
				var options = {
					script: '/youpi/autocompletion/ConfigFile/',
					varname: 'Value',
					json: true,
					maxresults: 20,
					timeout: 3000
				};
				var au = new _bsn.AutoSuggest(id + '_config_save_text', options);
			} catch(e) {}
	
			txt.focus();
		}
		else {
			if (sub.getAttribute('class') == 'show') {
				sub.setAttribute('class', 'hide');
			}
			else {
				sub.setAttribute('class', 'show');
				var nText = document.getElementById(id + '_config_save_text');
				nText.select();
				nText.focus();
			}
		}
	}

	this.saveConfig = function() {
		var textNode = document.getElementById(id + '_config_save_text');
		var name = textNode.value.replace('+', '%2B');
	
		if (name.length == 0) {
			alert('Cannot save a config file with an empty name!');
			textNode.focus();
			return;
		}
	
		// Checks for name availability (does not exits in DB)
		var cnode = document.getElementById(id + '_config_save_res_div');
		var xhr = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				removeAllChildrenNodes(cnode);
				var nb = resp['result'];
				var p = document.createElement('p');
				if (nb > 0) {
					// Name already exists, ask for overwriting
					var r = confirm("A config file with that name already exists in the database.\nWould you like to overwrite it ?");
					if (!r) return;
				}
	
				// Saves to DB
				saveConfigToDB(name);
			}
		);
	
		// Checks if a selection of that name already exists
		post = 	'Kind=' + plugin_id + '&Name=' + name;
	
		// Send HTTP POST request
		xhr.send('/youpi/process/checkConfigFileExists/', post);
	}

	function saveConfigToDB(name) {
		var cnode = document.getElementById(id + '_config_save_res_div');
		var area = document.getElementById(id + '_config_textarea');
	
		var r = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Selection saved
				removeAllChildrenNodes(cnode);
				var p = document.createElement('p');
				p.setAttribute('class', 'done');
				p.appendChild(document.createTextNode("Done. Config file saved under"));
				p.appendChild(document.createElement('br'));
				p.appendChild(document.createTextNode("'" + name + "'."));
				cnode.appendChild(p);
	
				// Refresh content
				setConfigFile();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=saveConfigFile&Name=' + escape(name) + 
			'&Content=' + escape(area.value);
		r.send('/youpi/process/plugin/', post);
	}

	function setConfigFile() {
		var cdiv = document.getElementById(id + '_config_name_div');
		var r = new HttpRequest(
			id + '_config_name_div',
			null,
			// Custom handler for results
			function(resp) {
				removeAllChildrenNodes(cdiv);
				var selNode = getSelect(plugin_id + '_config_name_select', resp['result']['configs']);
				selNode.setAttribute('onchange', instance_name + ".displayCurrentConfUsed();");
				cdiv.appendChild(selNode);
	
				var txt = selNode.options[selNode.selectedIndex].text;
				var img = document.createElement('img');
				img.setAttribute('style', 'cursor: pointer; margin-left: 5px;');
				img.setAttribute('src', '/media/' + guistyle + '/img/16x16/cancel.png');
				img.setAttribute('onclick', instance_name + ".deleteConfigFile();");
				cdiv.appendChild(img);
				
				displayCurrentConfUsed();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=getConfigFileNames';
		r.send('/youpi/process/plugin/', post);
	}

	this.deleteConfigFile = function() {
		var selNode = document.getElementById(plugin_id + '_config_name_select');
		var txt = selNode.options[selNode.selectedIndex].text;
	
		if (txt == 'default') {
			alert('Cannot remove default configuration file.');
			return;
		}
		else {
			var r = confirm("Are you sure you want to delete the configuration file '" + txt + "'?");
			if (!r) return;
		}
	
		var r = new HttpRequest(
			id + '_config_current_div',
			null,
			// Custom handler for results
			function(resp) {
				selNode.remove(selNode.selectedIndex);
				displayCurrentConfUsed();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=deleteConfigFile&Name=' + txt;
		r.send('/youpi/process/plugin/', post);
	}

	// Constructor
	function init() {
		render();
		setConfigFile();
	}

	init();
}
