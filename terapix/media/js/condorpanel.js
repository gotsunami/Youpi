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
	 * Var: instance_name
	 * Name of instance in global namespace
	 *
	 */
	var instance_name = varName;
	/*
	 * Var: headerTitle
	 * Header box's title
	 *
	 */
	var headerTitle = 'Select Condor Nodes';
	/*
	 * Var: container
	 * Parent DOM container
	 *
	 */ 
	var container = document.getElementById(container_id);


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


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
		tab.setAttribute('class', 'box');

		tr = document.createElement('tr');
		th = document.createElement('th');
		th.appendChild(document.createTextNode(headerTitle));
		tr.appendChild(th);
		tab.appendChild(tr);

		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('id', container_id + '_host_list_td');
		tr.appendChild(td);
		tab.appendChild(tr);

		container.appendChild(tab);

		this.update();
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
				ldiv.setAttribute('style', 'width: 100%; height: 150px; overflow: auto; border: 1px solid #5b80b2; margin-bottom: 5px;');
				td.appendChild(ldiv);

				tab = document.createElement('table');
				tab.setAttribute('class', 'condorPanel');
				var check, statusClass;
				var nbidle=0, nbbusy=0, total = resp['results'].length;
				for (var k=0; k < total; k++) {
					if(resp['results'][k][1] == 'Idle') {
						statusClass = 'idle';
						nbidle++;
					}
					else {
						statusClass = 'busy';
						nbbusy++;
					}

					tr = document.createElement('tr');
					tr.setAttribute('class', statusClass);

					td = document.createElement('td');
					td.setAttribute('id', instance_name + '_host_td' + k);
					td.setAttribute('class', 'host');
					check = document.createElement('input');
					check.setAttribute('id', instance_name + '_host_check' + k);
					check.setAttribute('type', 'checkbox');
					check.setAttribute('style', 'margin-right: 5px;');
					td.appendChild(check);
					td.appendChild(document.createTextNode(resp['results'][k][0]));
					tr.appendChild(td);

					td = document.createElement('td');
					td.setAttribute('class', 'status');
					td.appendChild(document.createTextNode(resp['results'][k][1]));
					tr.appendChild(td);
					tab.appendChild(tr);
				}
				sdiv.appendChild(document.createTextNode('Idle: ' + nbidle + ' (' + (nbidle/total*100).toFixed(2) + '%), Busy: ' 
					+ nbbusy + ' (' + (nbbusy/total*100).toFixed(2) + '%) ['));
				var ref = document.createElement('a');
				ref.setAttribute('href', '#');
				ref.setAttribute('onclick', instance_name + '.update();');
				ref.appendChild(document.createTextNode('Refresh'));
				sdiv.appendChild(ref);
				sdiv.appendChild(document.createTextNode(']'));

				ldiv.appendChild(tab);

				var htd = document.getElementById(container_id + '_host_list_td');
				var s_chk = document.createElement('input');
				s_chk.setAttribute('id', instance_name + '_save_sel_check');
				s_chk.setAttribute('type', 'checkbox');
				s_chk.setAttribute('checked', 'checked');
				s_chk.setAttribute('style', 'margin-right: 5px;');
				htd.appendChild(s_chk);
				htd.appendChild(document.createTextNode('Save current selection for later use'));

				// Buttons div
				var bdiv = document.createElement('div');
				bdiv.setAttribute('style', 'text-align: center');
				var but = document.createElement('input');
				but.setAttribute('type', 'button');
				but.setAttribute('value', 'Select all');
				but.setAttribute('style', 'margin-right: 10px;');
				but.setAttribute('onclick', instance_name + '.selectAll();');
				bdiv.appendChild(but);

				but = document.createElement('input');
				but.setAttribute('type', 'button');
				but.setAttribute('value', 'Unselect all');
				but.setAttribute('onclick', instance_name + '.unselectAll();');
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
							var e = document.getElementById(instance_name + '_host_check' + n);
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
				ry.send('/youpi/profile/loadCondorNodeSelection/');
			}
		);

		// Send POST HTTP query
		xhr.send('/youpi/cluster/status/');
	}

	/*
	 * Function: _mustSaveCurrentSelection
	 * Returns Checkbox's state to know if current Condor selection should be saved.
	 *
	 * Returns:
	 *
	 * true if checkbox is checked; false if not
	 *
	 */ 
	function _mustSaveCurrentSelection() {
		return document.getElementById(instance_name + '_save_sel_check').checked;
	}

	/*
	 * Function: selectAll
	 * Checks all checkboxes list
	 *
	 */ 
	this.selectAll = function() {
		toggleSelection(true);
	}

	/*
	 * Function: unselectAll
	 * Unchecks all checkboxes list
	 *
	 */ 
	this.unselectAll = function() {
		toggleSelection(false);
	}

	/*
	 * Function: toggleSelection
	 * Un/Checks a node's checkbox
	 *
	 * Parameters:
	 *
	 * checked - boolean: true or false
	 *
	 */ 
	function toggleSelection(checked) {
		var checked = checked == true ? true : false;
		var nodes = getHostsInputNodes();

		for (var k=0; k < nodes.length; k++) {
			nodes[k].checked = checked;
		}
	}

	/*
	 * Function: getSelectedHosts
	 * Returns array of names of selected Condor nodes 
	 *
	 * Returns:
	 *
	 * Array of strings (Condor nodes)
	 *
	 * See Also:
	 * <getHostsInputNodes>
	 *
	 */ 
	this.getSelectedHosts = function() {
		var nodes = getHostsInputNodes();
		var hosts = new Array();
		var j=0;

		for (var k=0; k < nodes.length; k++) {
			if (nodes[k].checked) {
				hosts[j++] = document.getElementById(instance_name + '_host_td' + k).firstChild.nextSibling.nodeValue;
			}
		}

		if (_mustSaveCurrentSelection()) {
			var r = new HttpRequest(
				'{{ plugin.id }}_result',
				null,	
				function(resp) {
					// NOP
				}
			);
			var post = 'SelectedHosts=' + hosts;
			r.send('/youpi/profile/saveCondorNodeSelection/', post);
		}

		return hosts;
	}

	/*
	 * Function: getHostsInputNodes
	 * Returns array of DOM checkbox nodes (hosts nodes)
	 *
	 * Returns:
	 *
	 * Array of strings (Condor nodes)
	 *
	 * See Also:
	 * <getSelectedHosts>
	 *
	 */ 
	function getHostsInputNodes() {
		var nodes = document.getElementsByTagName('input');
		var checks = new Array();
		var i=0;
		for (var k=0; k < nodes.length; k++) {
			if (nodes[k].id.search(instance_name + '_host_check') == 0) {
				checks[i++] = nodes[k];
			}
		}
		return checks;
	}
}
