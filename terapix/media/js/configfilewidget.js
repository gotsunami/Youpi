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
 *  Simple widget that allows to select a configuration file to use with a processing plugin
 *
 * Constructor Parameters:
 *  container - string or DOM node: name of parent DOM block container
 *  pluginId - string: unique plugin id
 *  options - object: options
 *
 * Available Options:
 *  type - string: type of config file
 *
 */
function ConfigFileWidget(container, pluginId, options)
{
	var _container = $(container);
	var id = 'CFW_' + Math.floor(Math.random() * 999999);
	var plugin_id = pluginId ? pluginId : null;
	var _options;
	var _uploadPB;
	var _cancelImport = false;

	function render() {
		var tr, th, td;
		var tab = new Element('table').setStyle({width: '50%'});
		tab.setAttribute('class', 'fileBrowser');

		tr = new Element('tr');
		th = new Element('th');
		th.insert( _options.type + ' File');
		tr.insert(th);
		tab.insert(tr);

		tr = new Element('tr');
		td = new Element('td');
		td.setAttribute('style', 'vertical-align: middle');
		td.insert('Select a ' + _options.type + ' file to use for processing:');

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
		ndiv.setAttribute('id', id + '_' + _options.type + '_name_div');
		ndiv.setAttribute('style', 'float: right');

		butd.insert(bnew);
		butd.insert(bedit);
		butd.insert(ndiv);
		td.insert(butd);
		tr.insert(td);
		tab.insert(tr);

		// Options
		tr = new Element('tr');
		td = new Element('td', {id: id + '_' + options.type + '_import_files_td'});
		tr.insert(td);
		tab.insert(tr);

		_container.insert(tab);
		_showImportOption();

		// Label div, reports current conf selected file
		ndiv = new Element('div');
		ndiv.setAttribute('id', id + '_' + _options.type + '_current_div');
		ndiv.setAttribute('style', 'margin-top: 15px; color: brown; font-weight: bold');
		_container.insert(ndiv);

		// Editor div
		ndiv = new Element('div');
		ndiv.setAttribute('id', id + '_' + _options.type + '_editor_div');
		ndiv.setAttribute('style', 'display: none;');
		tab = new Element('table').addClassName('fileBrowser').setStyle({width: '-moz-fit-content'});

		tr = new Element('tr');
		th = new Element('th');
		th.setAttribute('colspan', '2');
		th.insert( _options.type + 'File Editor');
		tr.insert(th);
		tab.insert(tr);

		tr = new Element('tr');

		// Menu options
		// Text editor related
		td = new Element('td', {id: id + '_' + _options.type + '_editor_td'});
		var ldiv = new Element('div', {id: id + '_editor_loading'});
		var tarea = new Element('textarea', {id: id + '_' + _options.type + '_textarea', rows: 30, cols: 100});
		// Buttons
		var mdiv = new Element('div').addClassName('toolbar');
		var bsave = new Element('input', {
				id: id + '_save_as_input', 
				type: 'button', 
				value: 'Save ' + _options.type + ' as...'
		}).setStyle({marginRight: '10px'});
		bsave.observe('click', _saveConfigFileAs);
		var bdel = new Element('input', {
				id: id + '_del_input', 
				type: 'button', 
				value: 'Delete ' + _options.type
		}).setStyle({marginRight: '10px'});
		bdel.observe('click', _deleteConfigFile);
		var sdiv = new Element('div');
		sdiv.setAttribute('id', id + '_' + _options.type + '_save_div');
		sdiv.setAttribute('class', 'imageSelector');

		var bclose = new Element('input', {type: 'button', value: 'Close editor'});
		bclose.observe('click', _closeEditor);
		mdiv.insert(bsave);
		mdiv.insert(bdel);
		mdiv.insert(bclose);
		mdiv.insert(sdiv);

		td.insert(mdiv);
		td.insert(ldiv);
		td.insert(tarea);
		tr.insert(td);

		tab.insert(tr);
		ndiv.insert(tab);
		_container.insert(ndiv);
	}

	/*
	 * Function: _showImportOption
	 * Shows config file import option
	 *
	 */ 
	function _showImportOption() {
		var container = $(id + '_' + options.type + '_import_files_td');
		var opta = new Element('a', {href: '#'}).update('import config files');
		var optd = new Element('div').addClassName('all_mini');
		var patterns;

		opta.observe('click', function() {
			var pathi = new Element('input', {id: plugin_id + '_config_data_path_input', 
				readonly: 'readonly',
				type: 'text', 
				size: 50, 
				title: 'Click to open the path selector'}).addClassName('datapath');
			var importb = new Element('input', {type: 'button', value: 'Import!'});
			importb.observe('click', function() { 
				_cancelImport = false;
				_batchImport(pathi.value, patterns);
			}).hide();
			pathi.observe('click', function() {
				boxes.browsePath(['*.*'], function(path, filePatterns) {
					if (path) {
						pathi.writeAttribute('value', path);
						patterns = filePatterns;
						importb.show();
					}
				});
			});
			var backa = new Element('a', {href: '#'}).update('Back');
			backa.observe('click', function() { _showImportOption(); });
			optd.update('(').insert(backa).insert(')').insert(pathi).insert(importb).appear({
				afterFinish: function() {pathi.focus();}
			});
		});
		optd.update('(Or ').insert(opta).insert(' from a directory)');
		container.update(optd);
	}

	/*
	 * Function: _batchImport
	 * Sets things up for batch import
	 *
	 * Parameters:
	 *  path - string: path for searching files
	 *  patterns - array: array of regexp patterns
	 *
	 */ 
	function _batchImport(path, patterns) {
		var container = $(id + '_' + options.type + '_import_files_td');
		container.update();
		var cancelb = new Element('input', {id: id + _options.type + '_cancel_button', type: 'button', value: 'Cancel'});
		cancelb.observe('click', function() {
			boxes.confirm('Are you sure you want to cancel the import?', function() {
				_cancelImport = true;
			});
		});

		var tab = new Element('table').setStyle({width: '100%'});
		var tr, td;
		tr = new Element('tr');
		td = new Element('td').setStyle({width: '100%', verticalAlign: 'middle'});
		var p = new Element('div');
		_uploadPB = new ProgressBar(p, 0, {
			borderColor: 'grey', 
			color: 'lightblue',
			animate: false
		});
		var log = new Element('span', {id: id +  '_' + _options.type + '_upload_log'});
		td.insert(p).insert(log);
		tr.insert(td);

		td = new Element('td').insert(cancelb);
		tr.insert(td);
		tab.insert(tr);
		container.update(tab);

		_do_Import(0, path, patterns);
	}

	/*
	 * Function: _batchImport
	 * Import files recursively from a directory
	 *
	 * Parameters:
	 *  pos - integer: file number (seek)
	 *  path - string: path for searching files
	 *  patterns - array: array of regexp patterns
	 *  total - integer: total file count [optional]
	 *
	 */ 
	function _do_Import(pos, path, patterns, total) {
		var container = $(id +  '_' + _options.type + '_upload_log');
		var r = new HttpRequest(
			container,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var r = resp.result;
				var log = new Logger(container);
				if (r.error) {
					container.update();
					log.msg_error(r.error);
					return;
				}
				if (!_cancelImport && r.pos < r.total) {
					_uploadPB.setPourcentage(r.percent);			
					_do_Import(r.pos, path, patterns, r.total);
				}
				else {
					container.update();
					if (_cancelImport)
						log.msg_warning('Aborted. ' + r.pos + ' files imported');
					else {
						_uploadPB.setPourcentage(100);			
						log.msg_ok('Done. ' + r.total + ' files imported' + (r.total == 0 ? ' (<b>maybe not the right directory?</b>)' : ''));
					}
					var but = $(id + _options.type + '_cancel_button');
					but.writeAttribute('value', 'Close');
					but.stopObserving('click');
					but.observe('click', function() {
						_showImportOption();
					});
				}
			}
		);

		var post = {
			Plugin: plugin_id,
			Method: 'importConfigFiles',
			Path: path,
			Patterns: patterns.join(';'),
			Type: _options.type
		}

		if (pos) {
			post.Pos = pos;
			post.Total = total;
		}

		r.setBusyMsg('Please wait while processing');
		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	}

	function _displayCurrentConfUsed() {
		var selNode = $(plugin_id + '_' + _options.type +'_name_select');
		var txt = selNode.options[selNode.selectedIndex].text;
		var curConfDiv = $(id + '_' + _options.type + '_current_div');
		curConfDiv.update("The '" + txt + "' " + _options.type +" file will be used for processing.");
		if ($(id + '_' + _options.type + '_editor_div').visible()) _editSelectedConfigFile();
	}
	
	function _displayNewConfigFile() {
		editConfigFile('default');
	}

	function _editSelectedConfigFile() {
		var sel = $(plugin_id + '_' + _options.type + '_name_select');
		var conf = sel.options[sel.selectedIndex].text;
		editConfigFile(conf);
	}

	function _closeEditor() {
		$(id + '_' + _options.type + '_editor_div').hide();
	}

	function editConfigFile(configName) {
		var ldiv = $(id + '_editor_loading');
		var div = $(id + '_' + _options.type + '_editor_div');
		div.setAttribute('style', 'display: block');
		$(id + '_save_as_input').hide();
		$(id + '_del_input').hide();
	
		var post = {
			Plugin: plugin_id,
			Method: 'getConfigFileContent',
			Name: configName,
			Type: _options.type
		};

		var r = new HttpRequest(
			ldiv.id,
			null,
			// Custom handler for results
			function(resp) {
				ldiv.update();

				if (configName != 'default') {
					var d = get_permissions('config', resp.result.id, function(r) {
						var delb = $(id + '_del_input');
						r.currentUser.write ? delb.show() : delb.hide();
						if (r.currentUser.read) $(id + '_save_as_input').show();
					});
					ldiv.update(d);
				}
				else {
					var log = new Logger(ldiv);
					log.msg_warning('Default configuration file is always readable by everyone');
					$(id + '_save_as_input').show();
				}
				var edit = $(id + '_' + _options.type + '_textarea');
				edit.value = resp.result.data;
				edit.focus();
			}
		);

		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	}

	function _saveConfigFileAs() {
		var div = $(id + '_' + _options.type + '_save_div');
		var sub = $(id + '_' + _options.type + '_save_subdiv');

		if (!sub) {
			sub = new Element('div');
			sub.setAttribute('id', id + '_' + _options.type + '_save_subdiv');
			sub.setAttribute('class', 'show');
	
			var txt = new Element('input');
			txt.setAttribute('style', 'float: left; margin-right: 5px;');
			txt.setAttribute('id', id + '_' +_options.type +'_save_text');
			txt.setAttribute('type', 'text');
			sub.insert(txt);
	
			var save = new Element('input', {type: 'button', value: 'Save!'});
			save.observe('click', _saveConfig);
			sub.insert(save);
	
			var res = new Element('div');
			res.setAttribute('id', id + '_' +_options.type +'_save_res_div');
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
				var au = new _bsn.AutoSuggest(id + '_' + _options.type + '_save_text', options);
			} catch(e) {}
	
			txt.focus();
		}
		else {
			if (sub.getAttribute('class') == 'show') {
				sub.setAttribute('class', 'hide');
			}
			else {
				sub.setAttribute('class', 'show');
				var nText = $(id + '_' + _options.type + '_save_text');
				nText.select();
				nText.focus();
			}
		}
	}

	function _saveConfig() {
		var textNode = $(id + '_' + _options.type + '_save_text');
		var name = textNode.value.replace('+', '%2B');
	
		if (name.length == 0) {
			alert('Cannot save a ' + _options.type + ' file with an empty name!');
			textNode.focus();
			return;
		}
	
		// Checks for name availability (does not exits in DB)
		var cnode = $(id + '_' + _options.type + '_save_res_div');
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
						alert("A default " + _options.type + " file can't be overwritten !");
						return;
					}
					else {
						// Name already exists, ask for overwriting
						var r = confirm("A "+ _options.type + " file with that name already exists in the database.\nWould you like to overwrite it ?");
						if (!r) return;
					}
				}
	
				// Saves to DB
				_saveConfigToDB(name);
			}
		);
	
		// Checks if a selection of that name already exists
		//post = 	'Kind=' + plugin_id + '&Name=' + name + '&Type=' + _options.type;
		var post = {
			Kind: plugin_id,
			Name: name,
			Type: _options.type
		};
	
		// Send HTTP POST request
		xhr.send('/youpi/process/checkConfigFileExists/', $H(post).toQueryString());
	}

	function _saveConfigToDB(name) {
		var cnode = $(id + '_' + _options.type + '_save_res_div');
		var area = $(id + '_' +_options.type + '_textarea');

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
				p.insert("Done. " + _options.type + " file saved under");
				p.insert(new Element('br'));
				p.insert("'" + name + "'.");
				cnode.insert(p);
	
				// Refresh content
				setConfigFile();
			}
		);

		var post = {
			Plugin: plugin_id,
			Method: 'saveConfigFile',
			Name: name,
			Content: area.value.unescapeHTML(),
			Type: _options.type
		}

		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	}

	function setConfigFile() {
		var cdiv = $(id + '_' + _options.type + '_name_div');
		var r = new HttpRequest(
			id + '_' + _options.type + '_name_div',
			null,
			// Custom handler for results
			function(resp) {
				cdiv.update();
				var confs = resp.result.configs;
				var selNode = getSelect(plugin_id + '_' + _options.type +'_name_select', confs.map(function(conf) { return conf.name; }));
				selNode.observe('change', _displayCurrentConfUsed);
				// Set as default
				var defopt = selNode.select("option[value=\"default\"]")[0];
				defopt.writeAttribute('selected', 'selected');
				cdiv.insert(selNode);
	
				var txt = selNode.options[selNode.selectedIndex].text;
				_displayCurrentConfUsed();
			}
		);
	
		var post = {
			Plugin: plugin_id,
			Method: 'getConfigFileNames',
			Type: _options.type
		};

		r.send('/youpi/process/plugin/', $H(post).toQueryString());
	}

	function _deleteConfigFile() {
		var selNode = $(plugin_id + '_' + _options.type + '_name_select');
		var txt = selNode.options[selNode.selectedIndex].text;
	
		if (txt == 'default') {
			alert('Cannot remove default ' + _options.type + ' file.');
			return;
		}

		boxes.confirm("Are you sure you want to delete the " + _options.type + "  file '" + txt + "'?", function() {
			var r = new HttpRequest(
				id + '_' + _options.type + '_current_div',
				null,
				// Custom handler for results
				function(resp) {
					if (resp.result.success) {
						document.fire('notifier:notify', "Config file '" + txt + "' deleted");
						selNode.remove(selNode.selectedIndex);
					}
					else
						boxes.perms_discard();
					_displayCurrentConfUsed();
				}
			);
		
			var post = 'Plugin=' + plugin_id + '&Method=deleteConfigFile&Name=' + txt + '&Type=' + _options.type;
			r.send('/youpi/process/plugin/', post);
		});
	}

	// Constructor
	function init() {
		if (typeof options != 'object') {
			throw "options must be an object"
			return;
		}
		if (typeof options.type != 'string') {
			throw "type not available"
			return;
		}

		_options = options;
		render();
		setConfigFile();
	}

	init();
}
