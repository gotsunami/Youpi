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
 * Class: ConfigFileWidget
 * Simple widget that allows to select a configuration file to use with a processing plugin
 *
 * Constructor Parameters:
 *
 * container - string or DOM node: name of parent DOM block container
 * pluginId - string: unique plugin id
 *
 */
function ConfigFileWidget(container, pluginId)
{
	var _container = $(container);
	var id = 'CFW_' + Math.floor(Math.random() * 999999);
	var plugin_id = pluginId ? pluginId : null;

	function render() {
		var tr, th, td;
		var tab = new Element('table');
		tab.setAttribute('class', 'fileBrowser');

		tr = new Element('tr');
		th = new Element('th');
		th.insert('Config File');
		tr.insert(th);
		tab.insert(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('style', 'vertical-align: middle');
		td.insert('Select a configuration file to use for processing:');

		var butd = new Element('div');
		var bnew = new Element('input', {
								type: 'button',
								value: 'New',
								style: 'float: left; margin-right: 5px'
		});
		bnew.observe('click', _displayNewConfigFile);

		var bedit = new Element('input', {
								type: 'button',
								value: 'Edit selected',
								style: 'float: left; margin-right: 5px'
		});
		bedit.observe('click', _editSelectedConfigFile);

		var ndiv = new Element('div');
		ndiv.setAttribute('id', id + '_config_name_div');
		ndiv.setAttribute('style', 'float: right');

		butd.insert(bnew);
		butd.insert(bedit);
		butd.insert(ndiv);
		td.insert(butd);
		tr.insert(td);
		tab.insert(tr);
		_container.insert(tab);

		// Label div, reports current conf selected file
		ndiv = new Element('div');
		ndiv.setAttribute('id', id + '_config_current_div');
		ndiv.setAttribute('style', 'margin-top: 15px; color: brown; font-weight: bold');
		_container.insert(ndiv);

		// Editor div
		ndiv = new Element('div');
		ndiv.setAttribute('id', id + '_config_editor_div');
		ndiv.setAttribute('style', 'display: none;');
		tab = new Element('table');
		tab.setAttribute('class', 'fileBrowser');

		tr = new Element('tr');
		th = new Element('th');
		th.setAttribute('colspan', '2');
		th.insert('Config File Editor');
		tr.insert(th);
		tab.insert(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('id', id + '_config_editor_td');
		var ldiv = new Element('div');
		ldiv.setAttribute('id', id + '_editor_loading');
		var tarea = new Element('textarea');
		tarea.setAttribute('id', id + '_config_textarea');
		tarea.setAttribute('rows', '30');
		tarea.setAttribute('cols', '100');
		td.insert(ldiv);
		td.insert(tarea);
		tr.insert(td);

		td = new Element('td');
		td.setAttribute('style', id + 'background-color: #eaeaea; border-left: 2px solid #5b80b2; width: 30%');
		ldiv = new Element('div');
		var bsave = new Element('input', {type: 'button', value: 'Save config as...'});
		bsave.observe('click', _saveConfigFileAs);

		var sdiv = new Element('div');
		sdiv.setAttribute('id', id + '_config_save_div');
		sdiv.setAttribute('class', 'imageSelector');
		ldiv.insert(bsave);
		ldiv.insert(sdiv);
		sdiv = new Element('div');
		var bclose = new Element('input', {type: 'button', value: 'Close editor'});
		bclose.observe('click', _closeEditor);
		sdiv.insert(bclose);
		td.insert(ldiv);
		td.insert(sdiv);
		tr.insert(td);

		tab.insert(tr);
		ndiv.insert(tab);
		_container.insert(ndiv);
	}

	function _displayCurrentConfUsed() {
		var selNode = $(plugin_id + '_config_name_select');
		var txt = selNode.options[selNode.selectedIndex].text;
		var curConfDiv = $(id + '_config_current_div');
		removeAllChildrenNodes(curConfDiv);
		curConfDiv.insert("The '" + txt + "' configuration file will be used for processing.");
	}
	
	function _displayNewConfigFile() {
		editConfigFile('default');
	}

	function _editSelectedConfigFile() {
		var sel = $(plugin_id + '_config_name_select');
		var conf = sel.options[sel.selectedIndex].text;
		editConfigFile(conf);
	}

	function _closeEditor() {
		var div = $(id + '_config_editor_div');
		div.setAttribute('style', 'display: none');
	}

	function editConfigFile(configName) {
		var ldiv = $(id + '_editor_loading');
		var div = $(id + '_config_editor_div');
		div.setAttribute('style', 'display: block');
	
		var r = new HttpRequest(
			ldiv.id,
			null,
			// Custom handler for results
			function(resp) {
				ldiv.innerHTML = '';
				var edit = $(id + '_config_textarea');
				edit.value = resp['result'];
				edit.focus();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=getConfigFileContent&Name=' + configName;
		r.send('/youpi/process/plugin/', post);
	}

	function _saveConfigFileAs() {
		var div = $(id + '_config_save_div');
		var sub = $(id + '_config_save_subdiv');
	
		if (!sub) {
			sub = new Element('div');
			sub.setAttribute('id', id + '_config_save_subdiv');
			sub.setAttribute('class', 'show');
	
			var txt = new Element('input');
			txt.setAttribute('style', 'float: left; margin-right: 5px;');
			txt.setAttribute('id', id + '_config_save_text');
			txt.setAttribute('type', 'text');
			sub.insert(txt);
	
			var save = new Element('input', {type: 'button', value: 'Save!'});
			save.observe('click', _saveConfig);
			sub.insert(save);
	
			var res = new Element('div');
			res.setAttribute('id', id + '_config_save_res_div');
			res.setAttribute('style', 'vertical-align: middle');
			sub.insert(res);
	
			div.insert(sub);
	
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
				var nText = $(id + '_config_save_text');
				nText.select();
				nText.focus();
			}
		}
	}

	function _saveConfig() {
		var textNode = $(id + '_config_save_text');
		var name = textNode.value.replace('+', '%2B');
	
		if (name.length == 0) {
			alert('Cannot save a config file with an empty name!');
			textNode.focus();
			return;
		}
	
		// Checks for name availability (does not exits in DB)
		var cnode = $(id + '_config_save_res_div');
		var xhr = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				removeAllChildrenNodes(cnode);
				var nb = resp['result'];
				var p = new Element('p');
				if (nb > 0) {
					// Name already exists, ask for overwriting
					var r = confirm("A config file with that name already exists in the database.\nWould you like to overwrite it ?");
					if (!r) return;
				}
	
				// Saves to DB
				_saveConfigToDB(name);
			}
		);
	
		// Checks if a selection of that name already exists
		post = 	'Kind=' + plugin_id + '&Name=' + name;
	
		// Send HTTP POST request
		xhr.send('/youpi/process/checkConfigFileExists/', post);
	}

	function _saveConfigToDB(name) {
		var cnode = $(id + '_config_save_res_div');
		var area = $(id + '_config_textarea');
	
		var r = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Selection saved
				removeAllChildrenNodes(cnode);
				var p = new Element('p');
				p.setAttribute('class', 'done');
				p.insert("Done. Config file saved under");
				p.insert(new Element('br'));
				p.insert("'" + name + "'.");
				cnode.insert(p);
	
				// Refresh content
				setConfigFile();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=saveConfigFile&Name=' + escape(name) + 
			'&Content=' + escape(area.value);
		r.send('/youpi/process/plugin/', post);
	}

	function setConfigFile() {
		var cdiv = $(id + '_config_name_div');
		var r = new HttpRequest(
			id + '_config_name_div',
			null,
			// Custom handler for results
			function(resp) {
				removeAllChildrenNodes(cdiv);
				var selNode = getSelect(plugin_id + '_config_name_select', resp['result']['configs']);
				selNode.observe('change', _displayCurrentConfUsed);
				cdiv.insert(selNode);
	
				var txt = selNode.options[selNode.selectedIndex].text;
				var img = new Element('img', {
								style: 'cursor: pointer; margin-left: 5px;',
								src: '/media/themes/' + guistyle + '/img/16x16/cancel.png'
				});
				img.observe('click', _deleteConfigFile);
				cdiv.insert(img);
				
				_displayCurrentConfUsed();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=getConfigFileNames';
		r.send('/youpi/process/plugin/', post);
	}

	function _deleteConfigFile() {
		var selNode = $(plugin_id + '_config_name_select');
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
				_displayCurrentConfUsed();
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
