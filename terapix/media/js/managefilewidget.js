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
 * Class: FileWidget
 * Simple widget that allows to select a file to use with a processing plugin
 *
 * Constructor Parameters:
 *
 * container - string or DOM node: name of parent DOM block container
 * pluginId - string: unique plugin id
 * filetype - string: the type of the file 
 *
 */
function FileWidget(container, pluginId, filetype)
{
	var _container = $(container);
	var id = 'FW_' + Math.floor(Math.random() * 999999);
	var plugin_id = pluginId ? pluginId : null;

	function render() {
		var tr, th, td;
		var tab = new Element('table');
		tab.setAttribute('class', 'fileBrowser');

		tr = new Element('tr');
		th = new Element('th');
		th.insert( filetype + ' File');
		tr.insert(th);
		tab.insert(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('style', 'vertical-align: middle');
		td.insert('Select a ' + filetype + ' file to use for processing:');

		var butd = new Element('div');
		var bnew = new Element('input', {
								type: 'button',
								value: 'New',
								style: 'float: left; margin-right: 5px'
		});
		bnew.observe('click', _displayNewFile);

		var bedit = new Element('input', {
								type: 'button',
								value: 'Edit selected',
								style: 'float: left; margin-right: 5px'
		});
		bedit.observe('click', _editSelectedFile);

		var ndiv = new Element('div');
		ndiv.setAttribute('id', id + '_' + filetype + '_name_div');
		ndiv.setAttribute('style', 'float: right');

		butd.insert(bnew);
		butd.insert(bedit);
		butd.insert(ndiv);
		td.insert(butd);
		tr.insert(td);
		tab.insert(tr);
		_container.insert(tab);

		// Label div, reports current selected file
		ndiv = new Element('div');
		ndiv.setAttribute('id', id + '_' + filetype + '_current_div');
		ndiv.setAttribute('style', 'margin-top: 15px; color: brown; font-weight: bold');
		_container.insert(ndiv);

		// Editor div
		ndiv = new Element('div');
		ndiv.setAttribute('id', id + '_' + filetype + '_editor_div');
		ndiv.setAttribute('style', 'display: none;');
		tab = new Element('table');
		tab.setAttribute('class', 'fileBrowser');

		tr = new Element('tr');
		th = new Element('th');
		th.setAttribute('colspan', '2');
		th.insert( filetype + 'File Editor');
		tr.insert(th);
		tab.insert(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('id', id + '_' + filetype + '_editor_td');
		var ldiv = new Element('div');
		ldiv.setAttribute('id', id + '_editor_loading');
		var tarea = new Element('textarea');
		tarea.setAttribute('id', id + '_' + filetype + '_textarea');
		tarea.setAttribute('rows', '30');
		tarea.setAttribute('cols', '100');
		td.insert(ldiv);
		td.insert(tarea);
		tr.insert(td);

		td = new Element('td');
		td.setAttribute('style', id + 'background-color: #eaeaea; border-left: 2px solid #5b80b2; width: 30%');
		ldiv = new Element('div');
		var bsave = new Element('input', {type: 'button', value: 'Save ' + filetype + ' as...'});
		bsave.observe('click', _saveFileAs);

		var sdiv = new Element('div');
		sdiv.setAttribute('id', id + '_' + filetype + '_save_div');
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

	function _displayCurrentUsed() {
		var selNode = $(plugin_id + '_' + filetype +'_name_select');
		var txt = selNode.options[selNode.selectedIndex].text;
		var curDiv = $(id + '_' + filetype + '_current_div');
		removeAllChildrenNodes(curDiv);
		curDiv.insert("The '" + txt + "' " + filetype +" file will be used for processing.");
	}
	
	function _displayNewFile() {
		editFile('default');
	}

	function _editSelectedFile() {
		var sel = $(plugin_id + '_' + filetype + '_name_select');
		var conf = sel.options[sel.selectedIndex].text;
		editFile(conf);
	}

	function _closeEditor() {
		var div = $(id + '_' + filetype + '_editor_div');
		div.setAttribute('style', 'display: none');
	}

	function editFile(configName) {
		var ldiv = $(id + '_editor_loading');
		var div = $(id + '_' + filetype + '_editor_div');
		div.setAttribute('style', 'display: block');
	
		var r = new HttpRequest(
			ldiv.id,
			null,
			// Custom handler for results
			function(resp) {
				ldiv.innerHTML = '';
				var edit = $(id + '_' + filetype + '_textarea');
				edit.value = resp['result'];
				edit.focus();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=getFileContent&Name=' + configName;
		r.send('/youpi/process/plugin/', post);
	}

	function _saveFileAs() {
		var div = $(id + '_' + filetype + '_save_div');
		var sub = $(id + '_' + filetype + '_save_subdiv');
	
		if (!sub) {
			sub = new Element('div');
			sub.setAttribute('id', id + '_' + filetype + '_save_subdiv');
			sub.setAttribute('class', 'show');
	
			var txt = new Element('input');
			txt.setAttribute('style', 'float: left; margin-right: 5px;');
			txt.setAttribute('id', id + '_' + filetype + '_save_text');
			txt.setAttribute('type', 'text');
			sub.insert(txt);
	
			var save = new Element('input', {type: 'button', value: 'Save!'});
			save.observe('click', _save);
			sub.insert(save);
	
			var res = new Element('div');
			res.setAttribute('id', id + '_' +filetype +'_save_res_div');
			res.setAttribute('style', 'vertical-align: middle');
			sub.insert(res);
	
			div.insert(sub);
	
			// Add auto-completion capabilities
			try {
				var options = {
					script: '/youpi/autocompletion/File/',
					varname: 'Value',
					json: true,
					maxresults: 20,
					timeout: 3000
				};
				var au = new _bsn.AutoSuggest(id + '_' + filetype + '_save_text', options);
			} catch(e) {}
	
			txt.focus();
		}
		else {
			if (sub.getAttribute('class') == 'show') {
				sub.setAttribute('class', 'hide');
			}
			else {
				sub.setAttribute('class', 'show');
				var nText = $(id + '_' + filetype + '_save_text');
				nText.select();
				nText.focus();
			}
		}
	}

	function _save() {
		var textNode = $(id + '_' + filetype + '_save_text');
		var name = textNode.value.replace('+', '%2B');
	
		if (name.length == 0) {
			alert('Cannot save a ' + filetype + ' file with an empty name!');
			textNode.focus();
			return;
		}
	
		// Checks for name availability (does not exits in DB)
		var cnode = $(id + '_' + filetype + '_save_res_div');
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
	
					//if the configuration filename is default
					if (name == 'default') {
						
						//adding this rule to not permit it
						alert("A default " + filetype + " file can't be overwritten !");
						return;

					}

					else {

						// Name already exists, ask for overwriting
						var r = confirm("A "+ filetype + " file with that name already exists in the database.\nWould you like to overwrite it ?");
						if (!r) return;
					}
				}
	
				// Saves to DB
				_saveToDB(name);
			}
		);
	
		// Checks if a selection of that name already exists
		post = 	'Kind=' + plugin_id + '&Name=' + name;
	
		// Send HTTP POST request
		xhr.send('/youpi/process/checkFileExists/', post);
	}

	function _saveToDB(name) {
		var cnode = $(id + '_' + filetype + '_save_res_div');
		var area = $(id + '_' +filetype + '_textarea');
	
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
				p.insert("Done. " + filetype + " file saved under");
				p.insert(new Element('br'));
				p.insert("'" + name + "'.");
				cnode.insert(p);
	
				// Refresh content
				setFile();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=saveFile&Name=' + escape(name) + 
			'&Content=' + escape(area.value) + '&Type=' + escape(filetype) ;
		r.send('/youpi/process/plugin/', post);
	}

	function setFile() {
		var cdiv = $(id + '_' + filetype + '_name_div');
		var r = new HttpRequest(
			id + '_' + filetype + '_name_div',
			null,
			// Custom handler for results
			function(resp) {
				removeAllChildrenNodes(cdiv);
				var selNode = getSelect(plugin_id + '_' + filetype +'_name_select', resp['result']['manages']);
				selNode.observe('change', _displayCurrentUsed);
				cdiv.insert(selNode);
	
				var txt = selNode.options[selNode.selectedIndex].text;
				var img = new Element('img', {
								style: 'cursor: pointer; margin-left: 5px;',
								src: '/media/themes/' + guistyle + '/img/16x16/cancel.png'
				});
				img.observe('click', _deleteFile);
				cdiv.insert(img);
				
				_displayCurrentUsed();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=getFileNames';
		r.send('/youpi/process/plugin/', post);
	}

	function _deleteFile() {
		var selNode = $(plugin_id + '_' + filetype + '_name_select');
		var txt = selNode.options[selNode.selectedIndex].text;
	
		if (txt == 'default') {
			alert('Cannot remove default ' + filetype + ' file.');
			return;
		}
		else {
			var r = confirm("Are you sure you want to delete the " + filetype + "  file '" + txt + "'?");
			if (!r) return;
		}
	
		var r = new HttpRequest(
			id + '_' + filetype + '_current_div',
			null,
			// Custom handler for results
			function(resp) {
				selNode.remove(selNode.selectedIndex);
				_displayCurrentUsed();
			}
		);
	
		var post = 'Plugin=' + plugin_id + '&Method=deleteFile&Name=' + txt;
		r.send('/youpi/process/plugin/', post);
	}

	// Constructor
	function init() {
		render();
		setFile();
	}

	init();
}
