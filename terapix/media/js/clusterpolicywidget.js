/*
 * Class: ClusterPolicyWidget
 * Cluster policy widget, used in Condor Setup panel to define custom policies
 *
 * File:
 *
 *  clusterpolicywidget.js
 *
 * Dependencies:
 *
 *  common.js - <getSelect>, <validate_container>, <DropdownBox>, <Logger>
 *  bsn.AutoSuggest_c_2.0.js - AutoSuggest feature (3rd party)
 *
 * Constructor Parameters:
 *
 * container - string or DOM node: name of parent block container
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function ClusterPolicyWidget(container, varName) {
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
	 * Header title
	 *
	 */
	var _headerTitle = 'Select all available hosts where';
	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container;
	/*
	 * Var: _searchCriteria
	 * Array of strings enumerating search criterias
	 *
	 */
	var _searchCriteria = ['Available memory (RAM)','Available disk space', 'Slots (vms)', 'Host name'];
	/*
	 * Var: _comparators
	 * Array of strings for integer comparison
	 *
	 */
	var _comparators = ['>=', '=', '<='];
	/*
	 * Var: _memUnits
	 * Array of strings for memory units
	 *
	 */
	var _memUnits = ['MB', 'GB'];
	/*
	 * Var: _diskUnits
	 * Array of strings for disk units
	 *
	 */
	var _diskUnits = ['MB', 'GB', 'TB'];
	/*
	 * Var: _slotsConditions
	 * Array of strings for slots conditions
	 *
	 */
	var _slotsConditions = ['belong to selection', 'are not in selection'];
	/*
	 * Var: _hostConditions
	 * Array of strings for host conditions
	 *
	 */
	var _hostConditions = ['matches', 'does not match'];
	/*
	 * Var: _eop
	 * Policy delimiter
	 *
	 */
	var _eop = '#';
	/*
	 * Var: _serialMappings
	 * Associative array for serialized mappings
	 *
	 */
	var _serialMappings = {
		'>='	: 'G',
		'<='	: 'L',
		'='		: 'E',
		'MB'	: 'M',
		'GB'	: 'G',
		'TB'	: 'T',
		'belong to selection' 	: 'B',
		'are not in selection'	: 'NB',
		'matches'				: 'M',
		'does not match' 		: 'NM'
	};
	/*
	 * Var: _criteriaMappings
	 * Used to deserialize critera
	 *
	 */
	var _criteriaMappings = {'MEM' : 0, 'DSK' : 1, 'SLT' : 2, 'HST' : 3};
	/*
	 * Var: _slotsMappings
	 * Used to deserialize slotsConditions
	 *
	 */
	var _slotsMappings = {'B' : 0, 'NB' : 1};
	/*
	 * Var: _hostsMappings
	 * Used to deserialize hostsMappings
	 *
	 */
	var _hostsMappings = {'M' : 0, 'NM' : 1};
	/*
	 * Var: _compMappings
	 * Used to deserialize comparators
	 *
	 */
	var _compMappings = {'G' : 0, 'E' : 1, 'L' : 2};
	/*
	 * Var: _memMappings
	 * Used to deserialize mem and disk units
	 *
	 */
	var _unitsMappings = {'M' : 0, 'G' : 1, 'T' : 2};
	/*
	 * Var: _noSelText
	 * Caption used when no saved selections are available
	 *
	 */
	var _noSelText = '-- no saved selections available --';


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _rowIdx
	 * Current row index in table
	 *
	 */
	var _rowIdx = 0;
	/*
	 * Var: _policyTable
	 * DOM table node
	 *
	 */
	var _policyTable;
	/*
	 * Var: _savePolicyBox
	 * <DropdownBox> for saving current policy
	 *
	 */
	var _savePolicyBox;
	/*
	 * Var: _stringPolicyBox
	 * <DropdownBox> for displaying computed Condor requirement string policy
	 *
	 */
	var _stringPolicyBox;
	/*
	 * Var: _onSavePolicyHandler
	 *  Custom handler function called when new policy has been saved
	 */
	var _onSavePolicyHandler = null;


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
		alert('ClusterPolicyWidget::' + msg);
	}

	/*
	 * Function: render
	 * Renders widget
	 *
	 */ 
	this.render = function() {
		_render();
	}

	/*
	 * Function: _render
	 * Renders widget
	 *
	 * Parameters:
	 *  policies - string: row policies (optional)
	 *
	 */ 
	function _render(policies) {
		var policies = typeof policies == 'string' ? policies : null;
		if (policies)
			policies = policies.split(_eop);

		_container.innerHTML = '';
		_container.appendChild(document.createTextNode(_headerTitle));

		_policyTable = document.createElement('table');
		_policyTable.setAttribute('id', _instance_name + '_policy_table');
		_policyTable.setAttribute('class', 'cluster_policy');
		_container.appendChild(_policyTable);

		if (!policies)
			_addRow();
		else {
			for (var k=0; k < policies.length; k++)
				_addRow(policies[k]);
		}

		// Condor string policy box
		_stringPolicyBox = new DropdownBox(_container, 'Instant view of Condor requirement string');
		_stringPolicyBox.setTopLevelContainer(false);
		_stringPolicyBox.setOnClickHandler(function() {
			if (_stringPolicyBox.isOpen()) {
				_getSerializedData(_stringPolicyBox.getContentNode(), function(post) {
					if (!post.length)
						return;

					// Sends request to get computed Condor requirement string
					var container = _stringPolicyBox.getContentNode();
					var r = new HttpRequest(
						container,
						null,	
						function(resp) {
							container.innerHTML = '';
							var area = document.createElement('textarea');
							area.setAttribute('style', 'width: 90%;');
							area.setAttribute('rows', '4');
							area.setAttribute('readonly', 'readonly');
							area.appendChild(document.createTextNode(resp['ReqString']));
							container.appendChild(area);
						}
					);
	
					post = 'Params=' + post;
					r.setBusyMsg('Computing requirement string');
					r.send('/youpi/cluster/computeRequirementString/', post);
				} );
			}
		} );

		// Save policy box
		_savePolicyBox = new DropdownBox(_container, 'Save current policy');
		_savePolicyBox.setTopLevelContainer(false);
		_savePolicyBox.setOnClickHandler(function() {
			if (_savePolicyBox.isOpen()) {
				_getSerializedData(_savePolicyBox.getContentNode(), function(post) {
					if (!post.length) return;
					_renderSaveCurrentPolicy(_savePolicyBox.getContentNode());
				} );
			}
		} );

	}

	/*
	 * Function: setOnSavePolicyHandler
	 * Sets custom function handler
	 *
	 * Parameters:
	 *  handler - function: custom handler function called when new policy has been saved
	 *
	 */ 
	this.setOnSavePolicyHandler = function(handler) {
		_onSavePolicyHandler = typeof handler == 'function' ? handler : null;
	}

	/*
	 * Function: getOnSavePolicyHandler
	 * Returns custom function handler called when new policy saved
	 *
	 * Returns:
	 *  function
	 *
	 */ 
	this.getOnSavePolicyHandler = function(handler) {
		return _onSavePolicyHandler;
	}

	/*
	 * Function: savePolicy
	 * Saves current policy
	 *
	 */ 
	this.savePolicy = function() {
		var name = document.getElementById(_instance_name + '_save_policy_input').value;
		var log = new Logger(_instance_name + '_save_log_div');
		log.clear();

		if (!name.length) {
			log.msg_warning('Cannot save a policy with an empty name!');
			return;
		}

		var r = new HttpRequest(
			log,
			null,	
			function(resp) {
				log.clear();
				if (resp['Error']) {
					log.msg_error(resp['Error']);
					return;
				}
				log.msg_ok("Policy '" + resp['Label'] + "' has been saved.");

				if (_onSavePolicyHandler) _onSavePolicyHandler();
			}
		);
		var post = 'Label=' + name + '&Serial=' + _getSerializedData();
		r.setBusyMsg('Saving policy');
		r.send('/youpi/cluster/savePolicy/', post);
	}

	/*
	 * Function: _renderSaveCurrentPolicy
	 * Renders save policy widget
	 *
	 * Parameters:
	 *  container - DOM container
	 *
	 */ 
	function _renderSaveCurrentPolicy(container) {
		var label = document.createElement('label');
		label.appendChild(document.createTextNode('Save as'));
		var iname = document.createElement('input');
		iname.setAttribute('id', _instance_name + '_save_policy_input');
		iname.setAttribute('type', 'text');
		iname.setAttribute('style', 'margin-right: 10px;');
		var ibut = document.createElement('input');
		ibut.setAttribute('type', 'button');
		ibut.setAttribute('value', 'Save!');
		ibut.setAttribute('onclick', _instance_name + '.savePolicy();');
		var logdiv = document.createElement('div');
		logdiv.setAttribute('id', _instance_name + '_save_log_div');

		container.appendChild(label);
		container.appendChild(iname);
		container.appendChild(ibut);
		container.appendChild(logdiv);
		document.getElementById(_instance_name + '_save_policy_input').focus();
					
		// Live autocompletion:s
		try {
			var options = {
				script: '/youpi/autocompletion/CondorSavedPolicies/',
				varname: 'Value',
				json: true,
				maxresults: 10,
				timeout: 2000
			};
			var as = new _bsn.AutoSuggest(_instance_name + '_save_policy_input', options);
		} catch(e) {}
	}

	/*
	 * Function: getSavePolicyBox
	 * Returns save policy <DropdownBox> instance
	 *
	 * Returns:
	 *  Save policy <DropdownBox> instance
	 *
	 */ 
	this.getSavePolicyBox = function() {
		return _savePolicyBox;
	}

	/*
	 * Function: getStringPolicyBox
	 * Returns Condor requirement string policy <DropdownBox> instance
	 *
	 * Returns:
	 *  Condor requirement string policy <DropdownBox> instance
	 *
	 */ 
	this.getStringPolicyBox = function() {
		return _stringPolicyBox;
	}

	/*
	 * Function: criteriumChanged
	 * Called when search criterium selection has changed
	 *
	 * When selection changes, updates row's content.
	 *
	 * Parameters:
	 *  rowIdx - integer: table row index where the criterium changed
	 *
	 * See Also:
	 *  <_updateRowContent>
	 *
	 */ 
	this.criteriumChanged = function(rowIdx) {
		_updateRowContent(rowIdx);
	}

	/*
	 * Function: _updateRowContent
	 * Updates row's content to match new criterium selection
	 *
	 * Parameters:
	 *  rowIdx - integer: table row index where the criteria changed
	 *  rpol - string: row policy (optional)
	 *
	 * See Also:
	 *  <criteriumChanged>
	 *
	 */ 
	function _updateRowContent(rowIdx, rpol) {
		var tr = _getTableTRNode(rowIdx);
		var sel = document.getElementById(_policyTable.id + '_select_' + rowIdx);
		var td = document.getElementById(tr.id + '_condition_td');
		var later = false;
		var prefix;
		var policy = typeof rpol == 'string' ? rpol : null;

		if (policy) {
			var pol = policy.split(',');
		}

		removeAllChildrenNodes(td);
		td.innerHTML = '';

		switch (sel.selectedIndex) {
			case 0:
				// Memory
				later = true;
				prefix = 'mem';
				break;

			case 1:
				// Disk space
				later = true;
				prefix = 'disk';
				break;

			case 2:
				// Slots (vms)
				var condSel = getSelect(tr.id + '_' + prefix + '_select', _slotsConditions);
				if (policy)
					condSel.selectedIndex = _slotsMappings[pol[1]];

				td.appendChild(condSel);
				var savedSel;
				var r = new HttpRequest(
					null,
					null,	
					function(resp) {
						var sels = resp['Selections'];
						if (policy) {
							for (var k=0; k < sels.length; k++) {
								if (sels[k] == pol[2])
									break;
							}
							if (k == sels.length) {
								// FIXME: pb!! selection does not exist anymore!
								_error('PB');
							}
						}

						if (!sels.length) {
							savedSel = getSelect('', [_noSelText]);
						}
						else {
							savedSel = getSelect('', sels);
							if (policy)
								savedSel.selectedIndex = k;
						}


						td.appendChild(savedSel);
					}
				);
				r.send('/youpi/cluster/getCondorNodeSelections/');
				break;

			case 3:
				// Host name
				var condSel = getSelect(tr.id + '_' + prefix + '_select', _hostConditions);
				if (policy)
					condSel.selectedIndex = _hostsMappings[pol[1]];
				var i = document.createElement('input');
				i.setAttribute('id', tr.id + prefix + '_value');
				i.setAttribute('type', 'text');
				if (policy) {
					i.setAttribute('value', pol[2]);
				}
				td.appendChild(condSel);
				td.appendChild(i);
				break;

			default:
				break;
		}

		if (later) {
			var condSel = getSelect(tr.id + '_' + prefix + '_select', _comparators);
			var uSel = getSelect(tr.id + '_unit_select', (sel.selectedIndex == 0 ? _memUnits : _diskUnits));
			var i = document.createElement('input');
			i.setAttribute('id', tr.id + prefix + '_value');
			i.setAttribute('type', 'text');
			i.setAttribute('maxlength', '4');
			i.setAttribute('size', '4');
			td.appendChild(condSel);
			td.appendChild(i);
			td.appendChild(uSel);
			if (policy) {
				i.setAttribute('value', pol[2]);
				condSel.selectedIndex = _compMappings[pol[1]];
				uSel.selectedIndex = _unitsMappings[pol[3]];
			}
		}
	}

	/*
	 * Function: setupFormFromSerializedData
	 * Restaure complete form from serialized data
	 *
	 * Parameters:
	 *  serial - serialized data
	 *
	 */ 
	this.setupFormFromSerializedData = function(serial) {
		_render(serial);
	}

	/*
	 * Function: _getSerializedData
	 * Serialize form parameters
	 *
	 * Purpose:
	 * 	Serializes the form's data which can be sent as POST data to the server.
	 *
	 * Serialized data format:
	 *  The following elements can occur in any order (for every line):
	 *
	 * > MEM,[G|E|L],value,[M|G];
	 * > DSK,[G|E|L],value,[M|G|T];
	 * > SLT,[B|NB],selname;
	 * > HST,[M,NM],regexp;
	 *
	 * Parameters:
	 *  container - (_optional_) DOM element container 
	 *  onFinishHanlder - (_optional_) handler function called after computation
	 *
	 * Returns:
	 *  post - string: POST parameters of serialized data. Is an empty string in case of failure (bad form validation).
	 *
	 */ 
	function _getSerializedData(container, onFinishHandler) {
		var handler = typeof onFinishHandler == 'function' ? true : false;
		// Fake container
		var c = (typeof container == 'undefined' || !container) ? false : true;
		if (!c)
			var container = document.createElement('div');
		container.innerHTML = '';
		var post = '';
		var trs = _policyTable.getElementsByTagName('tr');
		// Data validation
		var errors = false;
		var error_msg;
		var log = new Logger(container);

		for (var k=0; k < trs.length; k++) {
			var kind = null;
			var sel = trs[k].getElementsByTagName('select')[0];
			var tds = trs[k].getElementsByTagName('td');
			// Last td
			ltd = tds[tds.length-1];
			var msels = ltd.getElementsByTagName('select');
			var ov = parseInt(sel.selectedIndex);
			if (ov == 0) {
				// Memory
				kind = 'MEM';
			} 
			else if (ov == 1) {
				// Disk space
				kind = 'DSK';
			}
			else if (ov == 2) {
				// Slots (vms)
				var comp = msels[0];
				var sel = msels[1];
				if (sel.options.length == 1 && sel.options[sel.selectedIndex].text == _noSelText) {
					errors = true;
					error_msg = 'no saved selection available. Please first save custom selections below if you want to ' +
						'use this search criterium.';
					break;
				}
				post += 'SLT,' + _serialMappings[comp.options[comp.selectedIndex].text] + ',' + 
					sel.options[sel.selectedIndex].text + _eop;
			}
			else if (ov == 3) {
				// Host name
				var comp = msels[0];
				var val = ltd.getElementsByTagName('input')[0].value;
				if (!val.length) {
					errors = true;
					error_msg = 'host name search criteria cannot be empty!';
					break;
				}
				post += 'HST,' + _serialMappings[comp.options[comp.selectedIndex].text] + ',' + encodeURI(val) + _eop;
			}

			if (kind) {
				var comp = msels[0];
				var unit = msels[1];
				var val = ltd.getElementsByTagName('input')[0].value;
				if (isNaN(parseInt(val))) {
					errors = true;
					error_msg = "memory or disk related size field must be an integer, not '" + val + "'!";
					break;
				}
				post += kind + ',' + _serialMappings[comp.options[comp.selectedIndex].text] + ',' + val + ',' + 
					_serialMappings[unit.options[unit.selectedIndex].text] + _eop;
			}
		}

		if (errors) {
			log.msg_error('Error at line ' + (k+1) + ': ' + error_msg);
		}

		post = post.substr(0, post.length-1);
		if (handler)
			onFinishHandler(post);

		return post;
	}

	/*
	 * Function: _getTableTRNode
	 * Returns DOM TR node
	 *
	 * Parameters:
	 *  rowIdx - integer: table row index where the criteria changed
	 *
	 * Returns:
	 *  DOM TR node
	 *
	 */ 
	function _getTableTRNode(rowIdx) {
		return document.getElementById(_policyTable.id + '_row_' + rowIdx);
	}

	/*
	 * Function: removeRow
	 * Removes a row from the table
	 *
	 * Parameters:
	 *  rowIdx - integer: table row index where the criteria changed
	 *
	 */ 
	this.removeRow = function(rowIdx) {
		var tr = _getTableTRNode(rowIdx);
		tr.parentNode.removeChild(tr);
	}

	/*
	 * Function: addRow
	 * Adds a new row of data
	 *
	 */ 
	this.addRow = function() {
		_addRow();
	}

	/*
	 * Function: _addRow
	 * Adds a new row of data
	 *
	 * Example:
	 *  rpol = 'MEM,G,1,G' will render a row with 'Memory >= 1 GB'
	 *
	 * Parameters:
	 *  rpol - string: row policy (optional)
	 *
	 */ 
	function _addRow(rpol) {
		var tr, td;
		var tab = _policyTable;
		var policy = typeof rpol == 'string' ? rpol : null;

		tr = document.createElement('tr');
		tab.appendChild(tr);
		tr.setAttribute('id', tab.id + '_row_' + _rowIdx);

		// - button
		td = document.createElement('td');
		if (_rowIdx > 0) {
			var addb = document.createElement('input');
			addb.setAttribute('type', 'button');
			addb.setAttribute('value', '-');
			addb.setAttribute('onclick', _instance_name + ".removeRow(" + _rowIdx + ");");
			td.appendChild(document.createTextNode('and '));
			td.appendChild(addb);
		}
		tr.appendChild(td);

		// + button
		td = document.createElement('td');
		addb = document.createElement('input');
		addb.setAttribute('type', 'button');
		addb.setAttribute('value', '+');
		addb.setAttribute('onclick', _instance_name + ".addRow();");
		td.appendChild(addb);
		tr.appendChild(td);

		td = document.createElement('td');
		var sel = getSelect(tab.id + '_select_' + _rowIdx, _searchCriteria);
		sel.setAttribute('onchange', _instance_name + ".criteriumChanged(" + _rowIdx + ");");
		if (policy) {
			var crit = policy.split(',');
			sel.selectedIndex = _criteriaMappings[crit[0]];
		}
		td.appendChild(sel);
		tr.appendChild(td);

		// Condition
		td = document.createElement('td');
		td.setAttribute('id', tr.id + '_condition_td');
		tr.appendChild(td);

		_updateRowContent(_rowIdx, policy);
		_rowIdx++;
	}

	/*
	 * Function: _main
	 * Main entry point
	 *
	 */ 
	function _main() {
		_container = validate_container(container);
		if (!_container) {
			_error('_main:: container is not valid!');
			return;
		}
	}

	_main();
}
