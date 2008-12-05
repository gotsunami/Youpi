/*
 * Class: CondorPanel
 * Condor panel widget, usefull to easily choose which Condor nodes are to be used
 * for processing.
 *
 * File:
 *
 *  condorpanel.js
 *
 * Dependencies:
 *
 *  advancedtable.js - Table rendering (<AdvancedTable> class)
 *  common.js - Selects rendering with <getSelect> function; <DropdownBox> class
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function CondorPanel(container_id, varName) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _instance_name
	 * Name of instance in global namespace
	 *
	 */
	var _instance_name = varName;
	/*
	 * Var: _headerTitle
	 * Header box's title
	 *
	 */
	var _headerTitle = 'Select Condor Nodes';
	/*
	 * Var: container
	 * Parent DOM container
	 *
	 */ 
	var container = document.getElementById(container_id);
	/*
	 * Var: SELECTION
	 * Use by <_showSavedData>'s *kind* parameter
	 *
	 */ 
	var SELECTION = 1;
	/*
	 * Var: POLICY
	 * Use by <_showSavedData>'s *kind* parameter
	 *
	 */ 
	var POLICY = 2;


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _advT
	 * <AdvancedTable> instance
	 *
	 */ 
	var _advT;
	/*
	 * Var: _savedSelectionSelectId
	 * DOM select ID for saved selection names
	 *
	 */ 
	var	_savedSelectionSelectId;
	/*
	 * Var: _savedSelectionDivId
	 * DOM div ID for saved selections 
	 *
	 */ 
	var _savedSelectionDivId;
	/*
	 * Var: _savedPolicySelectId
	 * DOM select ID for saved selection names
	 *
	 */ 
	var	_savedPolicySelectId;
	/*
	 * Var: _savedPolicyDivId
	 * DOM div ID for saved policies 
	 *
	 */ 
	var _savedPolicyDivId;
	/*
	 * Var: _custom_container
	 * DOM container for rendering custom policies
	 *
	 */ 
	var _custom_container;
	/*
	 * Var: _saved_container
	 * DOM container for rendering saved selections
	 *
	 */ 
	var _saved_container;
	/*
	 * Var: _savedSelBox
	 * <DropdownBox> instance for saved selections
	 *
	 */ 
	var _savedSelBox;
	/*
	 * Var: _savedPolBox
	 * <DropdownBox> instance for saved policies
	 *
	 */ 
	var _savedPolBox;
	/*
	 * Var: _viewSelContentBox
	 * <DropdownBox> instance for saved selection members
	 *
	 */ 
	var _viewSelContentBox;
	/*
	 * Var: _viewPolContentBox
	 * <DropdownBox> instance for saved policy members
	 *
	 */ 
	var _viewPolContentBox;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _error
	 * Displays custom error message
	 *
	 * Parameters:
	 *  msg - string: error message
	 *
	 */ 
	function _error(msg) {
		alert('CondorPanel::' + msg);
	}

	/*
	 * Function: _validate_container
	 * Checks whether a container is valid.
	 *
	 * Parameters:
	 *  container - string of DOM element for rendering content
	 *
	 * Returns:
	 *  DOM element or null
	 *
	 */ 
	function _validate_container(container) {
		var d;
		if (typeof container == 'string' && container.length) {
			d = document.getElementById(container);
			if (!d) {
				_error("bad container '" + container + "' used!");
				return null;
			}
		}
		else if (typeof container == 'object') {
			d = container;
		}
		else {
			_error('container must be string or a DOM object!');
			return null;
		}

		return d;
	}

	/*
	 * Function: showSavedSelections
	 * Shows saved selections name
	 *
	 * Parameters:
	 *  container_id - string: DOM element id
	 *  can_delete - boolean: optional callback function
	 *  handler - optional callback function
	 *
	 */ 
	this.showSavedSelections = function(container_id, can_delete, handler) {
		_showSavedData(SELECTION, container_id, can_delete, handler);
	}

	/*
	 * Function: showSavedPolicies
	 * Shows saved policies
	 *
	 * Parameters:
	 *  container_id - string: DOM element id
	 *  can_delete - boolean: optional callback function
	 *  handler - optional callback function
	 *
	 */ 
	this.showSavedPolicies = function(container_id, can_delete, handler) {
		_showSavedData(POLICY, container_id, can_delete, handler);
	}

	/*
	 * Function: getSavedSelBox
	 * Returns saved selections box instance
	 *
	 * Returns:
	 *  <DropdownBox> instance
	 *
	 */ 
	this.getSavedSelBox = function() { 
		return _savedSelBox; 
	}

	/*
	 * Function: getSavedPolBox
	 * Returns saved policies box instance
	 *
	 * Returns:
	 *  <DropdownBox> instance
	 *
	 */ 
	this.getSavedPolBox = function() { 
		return _savedPolBox; 
	}

	/*
	 * Function: getViewSelContentBox
	 * Returns selection content box instance
	 *
	 * Returns:
	 *  <DropdownBox> instance
	 *
	 */ 
	this.getViewSelContentBox = function() { 
		return _viewSelContentBox; 
	}

	/*
	 * Function: getViewPolContentBox
	 * Returns policy content box instance
	 *
	 * Returns:
	 *  <DropdownBox> instance
	 *
	 */ 
	this.getViewPolContentBox = function() { 
		return _viewPolContentBox; 
	}

	/*
	 * Function: savedSelectionChanged
	 * Refreshes box's label and closes it
	 *
	 */ 
	this.savedSelectionChanged = function() { 
		return _savedSelectionChanged();
	}

	/*
	 * Function: _savedSelectionChanged
	 * Refreshes box's label and closes it
	 *
	 */ 
	function _savedSelectionChanged() { 
		var sel = document.getElementById(_savedSelectionSelectId);
		_viewSelContentBox.setTitle("View '" + sel.options[sel.selectedIndex].text + "' selection content");
		// Closes box
		_viewSelContentBox.setOpen(false);
	}

	/*
	 * Function: savedPolicyChanged
	 * Refreshes box's label and closes it
	 *
	 */ 
	this.savedPolicyChanged = function() { 
		_savedPolicyChanged();
	}	

	/*
	 * Function: savedPolicyChanged
	 * Refreshes box's label and closes it
	 *
	 */ 
	function _savedPolicyChanged() { 
		var sel = document.getElementById(_savedPolicySelectId);
		_viewPolContentBox.setTitle("Instant view of '" + sel.options[sel.selectedIndex].text + "' policy requirements string");
		// Closes box
		_viewPolContentBox.setOpen(false);
	}

	/*
	 * Function: removeCurrentSelection
	 * Remove current custom selection
	 *
	 */ 
	this.removeCurrentSelection = function() {
		var sel = document.getElementById(_savedSelectionSelectId);
		var opt = sel.options[sel.selectedIndex];
		name = opt.text;

		var c = confirm("Are you sure you want to delete the '" + name + "' selection?");
		if (!c) return;

		var r = new HttpRequest(
			null,
			null,	
			function(resp) {
				if (sel.options.length == 1)
					_showSavedData(SELECTION, _savedSelectionDivId);
				else {
					sel.removeChild(opt);
					_savedSelectionChanged();
				}
			}
		);
		var post = 'Label=' + name;
		r.send('/youpi/cluster/delCondorNodeSelection/', post);
	}

	/*
	 * Function: removeCurrentPolicy
	 * Remove current custom policy
	 *
	 */ 
	this.removeCurrentPolicy = function() {
		var sel = document.getElementById(_savedPolicySelectId);
		var opt = sel.options[sel.selectedIndex];
		name = opt.text;

		var c = confirm("Are you sure you want to delete the '" + name + "' policy?");
		if (!c) return;

		var r = new HttpRequest(
			null,
			null,	
			function(resp) {
				if (sel.options.length == 1)
					_showSavedData(POLICY, _savedPolicyDivId);
				else {
					sel.removeChild(opt);
					_savedPolicyChanged();
				}
			}
		);
		var post = 'Label=' + name;
		r.send('/youpi/cluster/delCondorPolicy/', post);
	}


	/*
	 * Function: _showSavedData
	 * Show saved data (selections or policies)
	 *
	 * Parameters:
	 *  kind - int: <SELECTION> or <POLICY>
	 *  container_id - string: block container
	 *  can_delete - boolean: displays a delete button if true
	 *  handler - function: custom handler to execute
	 *  is_top_level - boolean: use it to switch CSS classes
	 *
	 */ 
	function _showSavedData(kind, container_id, can_delete, handler, is_top_level) {
		if (kind != SELECTION && kind != POLICY) {
			_error('showSavedData: bad kind value: ' + kind);
			return;
		}
		var callback = typeof handler == 'function' ? true : false;
		var show_delete = can_delete ? true : false;
		var top_level = is_top_level == false ? false : true;
		var container = document.getElementById(container_id);
		var log = new Logger(container);
		var url, m_url;

		if (kind == SELECTION) {
			_savedSelectionDivId = container_id;
			url = '/youpi/cluster/getCondorNodeSelections/';
			m_url = '/youpi/cluster/getCondorSelectionMembers/';
		}
		else {
			_savedPolicyDivId = container_id;
			url = '/youpi/cluster/getCondorPolicies/';
			m_url = '/youpi/cluster/getCondorRequirementString/';
		}

		var r = new HttpRequest(
			null,
			null,	
			function(resp) {
				log.clear();

				var sels = kind == SELECTION ? resp['Selections'] : resp['Policies'];
				if (!sels.length) {
					log.msg_warning('No saved ' + (kind == SELECTION ? 'selections' : 'policies') + ' at the moment.');
				}
				else {
					var d = document.createElement('div');
					container.appendChild(d);
					var top_box, child_box;

					if (kind == SELECTION) {
						_savedSelBox = new DropdownBox(_instance_name + '.getSavedSelBox()', d, 'View saved selections');
						top_box = _savedSelBox;
					}
					else {
						_savedPolBox = new DropdownBox(_instance_name + '.getSavedPolBox()', d, 'View saved policies');
						top_box = _savedPolBox;
					}

					if (!top_level) 
						top_box.setTopLevelContainer(false);

					var sp = document.createElement('span');
					var select = getSelect(container_id + '_' + (kind == 'SELECTION' ? 'sel_' : 'pol_') + 'select', sels);
					select.setAttribute('onchange', _instance_name + '.saved' + (kind == SELECTION ? 'Selection' : 'Policy') + 
						'Changed();');
					sp.appendChild(document.createTextNode('Saved ' + (kind == SELECTION ? 'selections' : 'policies') + ': '));
					sp.appendChild(select);
	
					if (show_delete) {
						var img = document.createElement('img');
						img.setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/cancel.png');
						img.setAttribute('style', 'cursor: pointer; margin-left: 5px;');
						img.setAttribute('onclick', _instance_name + '.removeCurrent' + (kind == SELECTION ? 'Selection' : 'Policy') + 
							'();');
						sp.appendChild(img);
					}

					top_box.getContentNode().appendChild(sp);
					if (kind == SELECTION) {
						_savedSelectionSelectId = select.id;
						_viewSelContentBox = new DropdownBox(_instance_name + '.getViewSelContentBox()', _savedSelBox.getContentNode(), 
							"View '" + select.options[select.selectedIndex].text + "' selection content");
						_viewSelContentBox.setTopLevelContainer(false);
						child_box = _viewSelContentBox;
					}
					else {
						_savedPolicySelectId = select.id;
						_viewPolContentBox = new DropdownBox(_instance_name + '.getViewPolContentBox()', _savedPolBox.getContentNode(), 
							"Instant view of '" + select.options[select.selectedIndex].text + "' requirement string");
						_viewPolContentBox.setTopLevelContainer(false);
						child_box = _viewPolContentBox;
					}

					// Handler function to show member nodes
					child_box.setOnClickHandler(function() {
						if (!child_box.isOpen())
							return;
						var ndiv = child_box.getContentNode();
						log = new Logger(ndiv);
						var selText = select.options[select.selectedIndex].text;
						var mr = new HttpRequest(
							ndiv,
							null,	
							function(resp) {
								ndiv.innerHTML = '';
								if (resp['Error'].length) {
									log.clear();
									log.msg_error('Error: ' + resp['Error']);
									return;
								}
								var d = document.createElement('div');
								if (kind == SELECTION) {
									d.setAttribute('class', 'custom_sel_members');
									for (var k=0; k < resp['Members'].length; k++) {
										d.appendChild(document.createTextNode(resp['Members'][k]));
										d.appendChild(document.createElement('br'));
									}
								}
								else {
									var area = document.createElement('textarea');
									area.setAttribute('style', 'width: 90%;');
									area.setAttribute('rows', '4');
									area.setAttribute('readonly', 'readonly');
									area.appendChild(document.createTextNode(resp['ReqStr']));
									d.appendChild(area);
								}
								ndiv.appendChild(d);
							}
						);
						post = 'Name=' + selText;
						mr.setBusyMsg('Loading ' + (kind == 'SELECTION' ? 'members' : 'requirements string'));
						mr.send(m_url, post);
					} );
				}
				
				if (callback) handler();
			}
		);
		r.send(url);
	}

	/*
	 * Function: render
	 * Main rendering function
	 *
	 * See Also:
	 * <update>
	 *
	 */ 
	this.render = function() {
		var tr, th, td;
		var tab = document.createElement('table');
		tab.setAttribute('class', 'condorPanelBox');

		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('id', container_id + '_host_list_td');
		tr.appendChild(td);
		tab.appendChild(tr);

		container.appendChild(tab);

		this.update();
	}

	/*
	 * Function: getTable
	 * Returns current <AdvancedTable> instance
	 *
	 */ 
	this.getTable = function() {
		return _advT;
	}

	/*
	 * Function: update
	 * Updates Condor's nodes data
	 *
	 * See Also:
	 * <render>
	 *
	 */ 
	this.update = function() {
		var tr, th, td, tab;
		td = document.getElementById(container_id + '_host_list_td');

		var xhr = new HttpRequest(
			td.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				td.innerHTML = '';

				var sdiv = document.createElement('div');
				sdiv.setAttribute('class', 'stats');
				td.appendChild(sdiv);

				var ldiv = document.createElement('div');
				ldiv.setAttribute('id', _instance_name + '_content_div');
				ldiv.setAttribute('class', 'list');
				td.appendChild(ldiv);
				var nbidle=0, nbbusy=0, total = resp['results'].length;

				_advT = new AdvancedTable(_instance_name + '.getTable()');
				_advT.setContainer(ldiv.id);
				_advT.setColStyles(['slot', 'state']);

				var check, statusClass;
				for (var k=0; k < total; k++) {
					if(resp['results'][k][1] == 'Idle') {
						statusClass = 'idle';
						nbidle++;
					}
					else {
						statusClass = 'busy';
						nbbusy++;
					}

					_advT.appendRow([resp['results'][k][0], resp['results'][k][1]], statusClass);
				}
				_advT.render();

				sdiv.appendChild(document.createTextNode('Idle: ' + nbidle + ' (' + (nbidle/total*100).toFixed(2) + '%), Busy: ' 
					+ nbbusy + ' (' + (nbbusy/total*100).toFixed(2) + '%) ['));
				var ref = document.createElement('a');
				ref.setAttribute('href', '#');
				ref.setAttribute('onclick', _instance_name + '.update();');
				ref.appendChild(document.createTextNode('Refresh'));
				sdiv.appendChild(ref);
				sdiv.appendChild(document.createTextNode(']'));

				var htd = document.getElementById(container_id + '_host_list_td');

				// Buttons div
				var bdiv = document.createElement('div');
				bdiv.setAttribute('style', 'text-align: center');
				var but = document.createElement('input');
				but.setAttribute('type', 'button');
				but.setAttribute('value', 'Select all');
				but.setAttribute('style', 'margin-right: 10px;');
				but.setAttribute('onclick', _instance_name + '.selectAll();');
				bdiv.appendChild(but);

				but = document.createElement('input');
				but.setAttribute('type', 'button');
				but.setAttribute('value', 'Unselect all');
				but.setAttribute('onclick', _instance_name + '.unselectAll();');
				bdiv.appendChild(but);

				htd.appendChild(bdiv);

				// Get any hosts saved selection
				var savedNodeSelection; 
				var ry = new HttpRequest(
					td.id,
					null,	
					function(re) {
						savedNodeSelection = re['SavedHosts'];
						if (!savedNodeSelection.length) {
							this.selectAll();
							return;
						}	

						for (var n=0; n < total; n++) {
							var e = document.getElementById(_instance_name + '_host_check' + n);
							e.checked = false;
							for (var t=0; t < savedNodeSelection.length; t++) {
								if (savedNodeSelection[t] == resp['results'][n][0]) {
									e.checked = true;
									break;
								}
							}	
						}	
					}
				);
			}
		);

		// Send POST HTTP query
		xhr.setBusyMsg('Getting Condor nodes information, please wait');
		xhr.send('/youpi/cluster/status/');
	}

	/*
	 * Function: selectAll
	 * Checks all checkboxes list
	 *
	 */ 
	this.selectAll = function() {
		_advT.selectAll(true);
	}

	/*
	 * Function: unselectAll
	 * Unchecks all checkboxes list
	 *
	 */ 
	this.unselectAll = function() {
		_advT.selectAll(false);
	}

	/*
	 * Function: getSelectedHosts
	 * Returns array of names of selected Condor nodes 
	 *
	 * Returns:
	 *  Array of strings (Condor node names) or null if none selected
	 *
	 */ 
	this.getSelectedHosts = function() {
		var vals = _advT.getSelectedColsValues();
		return vals.length > 0 ? vals.split(',') : null;
	}

	/*
	 * Function: saveCurrentNodeSelection
	 * Save current Condor node selection
	 *
	 * Parameters:
	 *  name - string: selection name
	 *  handler - optional callback function
	 *
	 */ 
	this.saveCurrentNodeSelection = function(name, handler) {
		var callback = typeof(handler) == 'function' ? true : false;
		var hosts;
		try {
			hosts = this.getSelectedHosts();
		} catch(e) { hosts = null; }

		var log = new Logger('custom_sel_save_log_div');
		log.clear();

		if (!hosts) {
			log.msg_warning('No selection to save! Please select some Condor nodes first.');
			return;
		}

		if (!name.length) {
			log.msg_warning('Cannot save a selection with an empty name!');
			return;
		}

		var r = new HttpRequest(
			'custom_sel_save_log_div',
			null,	
			function(resp) {
				log.clear();
				if (resp['Error']) {
					log.msg_error(resp['Error']);
					return;
				}
				log.msg_ok("Selection '" + resp['Label'] + "' has been saved (" + resp['SavedCount'] + ' host' + 
					(resp['SavedCount'] > 1 ? 's' : '') + ')');

				if (callback) handler();
			}
		);
		var post = 'Label=' + name + '&SelectedHosts=' + hosts;
		r.setBusyMsg('Saving selection');
		r.send('/youpi/cluster/saveNodeSelection/', post);
	}
}
