/*
 * Class: CondorPanel
 * Condor panel widget, usefull to easily choose which Condor nodes are to be used
 * for processing.
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <CondorPanel> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * File:
 *
 *  condorpanel.js
 *
 * Dependencies:
 *
 *  Table rendering - <AdvancedTable> widget
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


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _advT
	 * <AdvancedTable> instance
	 *
	 */ 
	var _advT;
	/*
	 * Var: _custom_container
	 * DOM container for rendering custom selections
	 *
	 */ 
	var _custom_container;
	/*
	 * Var: _saved_container
	 * DOM container for rendering saved selections
	 *
	 */ 
	var _saved_container;


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
		alert('CondorPanel: ' + msg);
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
	 * Function: getCustomPolicies
	 * Returns custom policies data
	 *
	 * Returns:
	 *  data
	 *
	 */ 
	this.getCustomPolicies = function() {
		return null;
	}

	/*
	 * Function: getSavedSelections
	 * Returns saved selections data
	 *
	 * Returns:
	 *  data
	 *
	 */ 
	this.getSavedSelections = function() {
		return null;
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
				/* FIXME: delete
				var s_chk = document.createElement('input');
				s_chk.setAttribute('id', _instance_name + '_save_sel_check');
				s_chk.setAttribute('type', 'checkbox');
				s_chk.setAttribute('checked', 'checked');
				s_chk.setAttribute('style', 'margin-right: 5px;');
				htd.appendChild(s_chk);
				htd.appendChild(document.createTextNode('Save current selection for later use'));
				*/

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
				// FIXME ry.send('/youpi/profile/loadCondorNodeSelection/');
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
	 *  name - string: selection name (must be unique)
	 *
	 */ 
	this.saveCurrentNodeSelection = function(name) {
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
			}
		);
		var post = 'Label=' + name + '&SelectedHosts=' + hosts;
		r.setBusyMsg('Saving selection');
		r.send('/youpi/profile/saveCondorNodeSelection/', post);
	}
}
